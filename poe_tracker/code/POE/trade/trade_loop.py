
import asyncio
import requests
import httpx
import time
import datetime

import pymongo
import motor.motor_asyncio
import copy

# from ...Client import Client
from ...Config import Config
from ...Log import Log
from .change_id import ChangeID
from .api import TradeAPI
from .. import mongo

class Trade_Loop:

    def __init__(self, args):
        self.log = Log()
        self.args = args
        self.config = Config()
        self.stash_queue = asyncio.Queue()
        self.db = mongo.Mongo().db


    async def loop(self):
        """
        Run the main loop of tracking various POE stuffs
        """
        self.log.info(f"Booted trade loop")
        if not self.config[self.args.env]['trade']['ingest']:
            self.log.warning("Config was set to not ingest trading. Aborting trade_loop.")
            return
        ingest_to_db_task = asyncio.create_task(self.ingest_to_db())
        queue_stash_task = asyncio.create_task(self.queue_up_stashes())

        while 1:
            await asyncio.sleep(1)

            if ingest_to_db_task.done():
                try:
                    r = ingest_to_db_task.result()
                except (KeyboardInterrupt, SystemExit):
                    return
                except Exception as e:
                    self.log.exception("Task threw exception")
                self.log.info("Restarting ingest_to_db")
                ingest_to_db_task = asyncio.create_task(self.ingest_to_db())

            if queue_stash_task.done():
                try:
                    r = queue_stash_task.result()
                except (KeyboardInterrupt, SystemExit):
                    return
                except Exception as e:
                    self.log.exception("Task threw exception")
                self.log.info("Restarting queue_up_stashes")
                queue_stash_task = asyncio.create_task(self.queue_up_stashes())


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


    async def queue_up_stashes(self):

        self.log.info("Begin queue_up_stashes")

        cache = await self.db.cache.find_one({"name":"trade"})

        x = TradeAPI() # We should move this someplace secure...
        # print("Syncing (this might take a while)")
        # x.sync_change_ids()
        x.set_next_change_id(cache['current_next_id'])
        # x.sync_poe_ninja()

        async for data in x.iter_data():
            await self.stash_queue.put(data)
            # Allow other tasks to run
            await asyncio.sleep((self.stash_queue.qsize()/10)**2)
