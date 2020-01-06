

class PreProcess:

    
    def __init__(self):
        pass


    async def process_stash(self, stash_dict):
        """Given a raw stash from the API, process it fully into the DB
        """


    async def process_item(self, item_dict, stash_id):
        """Given a raw item from the API, process it fully into the DB
        Returns:
            id of item
        """


    async def process_currency(self, item_dict):
        """Given some currency from the API, process it fully into the DB
        """


    async def ingest_to_db(self):

        stash_operations = []
        item_operations = []
        cache_operation = None
        last_good_change_id = ChangeID()
        last_poe_ninja_update = time.time()

        self.log.info("Begin ingesting items/stashes into DB")

        while 1:
            if self.stash_queue.qsize():
                stashes = await self.stash_queue.get()
                cache_operation = pymongo.UpdateOne(
                    {"name": "trade"},
                    {'$set': 
                        {'current_next_id':stashes['next_change_id']}
                    }
                )
                last_good_change_id = ChangeID(stashes['next_change_id'])

                for stash in stashes['stashes']:
                    # XXX Newly emptied stashes break here... Should we take the time to check them?
                    if len(stash['items']) == 0:
                        continue
                    # stash_sub_dict = copy.deepcopy(stash)
                    stash_sub_dict = {k:stash[k] for k in stash if k != 'items'}
                    stash_sub_dict['items'] = []

                    for item in stash['items']:
                        # TODO: Maybe make this a config option?
                        # if 'note' not in item:
                        #     continue
                        item['stash_id'] = stash['id']
                        item.pop("descrText", None)
                        item.pop("flavourText", None)
                        item.pop("icon", None)

                        try:
                            stash_sub_dict['items'].append(item['id'])
                        except KeyError:
                            # There was a corrupt item in the api?
                            # TODO: Verify and check items before storage
                            continue
                        item_operations.append(
                            pymongo.UpdateOne(
                                {"id":item['id']},
                                {
                                    "$setOnInsert": {
                                        "_createdAt": datetime.datetime.utcnow(),
                                        "_sold": False
                                    },
                                    "$set": {**item, "_updatedAt": datetime.datetime.utcnow()}
                                },
                                upsert=True
                            )
                        )
                    
                    stash_operations.append(
                            pymongo.UpdateOne(
                                {"id":stash_sub_dict['id']},
                                {
                                    "$setOnInsert": {"_createdAt": datetime.datetime.utcnow()},
                                    "$set": {**stash_sub_dict, "_updatedAt": datetime.datetime.utcnow()}
                                },
                                upsert=True
                            )
                    )
                if (len(stash_operations) and len(item_operations)):
                    try:
                        stash_result = await self.db.stashes.bulk_write(stash_operations, ordered=False)
                        item_result = await self.db.items.bulk_write(item_operations, ordered=False)
                    except pymongo.errors.AutoReconnect:
                        self.log.exception("Expereinced bulk_write error, sleeping")
                        time.sleep(5)
                    else:
                        # self.log.info(f"Stashes: Mod: {stash_result.modified_count:,d} Up: {stash_result.upserted_count:,d}")
                        # self.log.info(f"  Items: Mod: {item_result.modified_count:,d} Up: {item_result.upserted_count:,d}")
                        # self.log.info(f"{self.stash_queue.qsize()}")
                        if time.time() - last_poe_ninja_update > 60:
                            poe_ninja_change_id = ChangeID()
                            await poe_ninja_change_id.async_poe_ninja()
                            self.log.info(f"ChangeID delta: {poe_ninja_change_id-last_good_change_id}")
                            last_poe_ninja_update = time.time()
                            self.log.info(f"ChangeID: {last_good_change_id}")
                        stash_operations = []
                        item_operations = []


                if cache_operation:
                    await last_good_change_id.post_to_influx()
                    await self.db.cache.bulk_write([cache_operation,])
                    cache_operation = None
            else:
                await asyncio.sleep(1)
