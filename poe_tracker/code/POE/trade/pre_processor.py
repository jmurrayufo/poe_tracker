import datetime
import pymongo
import time
import asyncio

from .price import Price
from .. import mongo
from ...Log import Log
from .change_id import ChangeID
from collections import defaultdict

class PreProcessor:

    
    def __init__(self, api_dict):
        self.db = mongo.Mongo().db
        self.log = Log()
        self.api_dict = api_dict
        self.update_dict = defaultdict(lambda: [])


    async def process_api(self):
        """Given a full api raw dict, process it into the mongo db
        """
        # t1 = time.time()
        # Process and queue up items for writes
        for stash in self.api_dict['stashes']:
            await asyncio.sleep(0) # Be nice!
            await self.process_stash(stash)

        now = datetime.datetime.utcnow()
        op = pymongo.UpdateOne(
            {
                "name": "trade",
                "change_id_last_update": {"$lt": now}
            },
            {'$set': 
                {
                    'current_next_id': self.api_dict['next_change_id'],
                    'change_id_last_update': now,
                }
            }
        )
        self.update_dict['cache'].append(op)

        # TODO: This could really be a call to Mongo()
        # total_ops = 0
        for collection_name in self.update_dict:
                col = self.db.get_collection(name=collection_name)
                await col.bulk_write(
                        self.update_dict[collection_name], 
                        ordered=False
                )
                # total_ops += len(self.update_dict[collection_name])
        # self.log.info(f"{total_ops/(time.time()-t1)}")

        await ChangeID(self.api_dict['next_change_id']).post_to_influx()


    async def process_stash(self, stash_dict):
        """Given a raw stash from the API, process it fully into the DB
        """
        # XXX Newly emptied stashes break here... Should we take the time to check them?
        if len(stash_dict['items']) == 0:
            return

        # TODO: Preprocess item merge stacks with priced stacks
        noted_items = {}
        for item_dict in stash_dict['items']:
            if item_dict['extended']['category'] != "currency":
                continue
            if 'stackSize' not in item_dict:
                continue
            if 'note' in item_dict and Price(item_dict['note']).parse():
                noted_items[item_dict['typeLine']] = item_dict['id']

        prune_ids = []
        for item_dict in stash_dict['items']:
            if item_dict['extended']['category'] != "currency":
                continue
            if 'note' in item_dict:
                continue
            if 'stackSize' not in item_dict:
                continue
            if item_dict['typeLine'] not in noted_items:
                continue
            prune_ids.append(item_dict['id'])

            # Find the item to merge with, and incriment it's stack size
            for merge_dict in stash_dict['items']:
                if merge_dict['id'] == noted_items[item_dict['typeLine']]:
                    merge_dict['stackSize'] += item_dict['stackSize']
                    break

        # We might not even care about this? Pruning it keeps total items cleaner though...
        stash_dict['items'] = [x for x in stash_dict['items'] if x['id'] not in prune_ids]

        # Loop through items and build list of `id`s.
        new_ids = []
        for item_dict in stash_dict['items']:
            await asyncio.sleep(0) # Be nice!
            _id = await self.process_item(item_dict, stash_dict)
            if _id is None:
                continue
            new_ids.append(_id)

        # Repalce `items` field with array of `id` values
        stash_dict['items'] = new_ids

        # Commit to mongodb
        op = pymongo.UpdateOne(
                {"id":stash_dict['id']},
                {
                    "$setOnInsert": {"_createdAt": datetime.datetime.utcnow()},
                    "$set": {**stash_dict, "_updatedAt": datetime.datetime.utcnow()}
                },
                upsert=True
        )
        self.update_dict['stashes'].append(op)
        # await self.mongo.bulk_write(op, "stashes")


    async def process_item(self, item_dict, stash_dict):
        """Given a raw item from the API, process it fully into the DB
        Returns:
            id of item
        """

        # TODO: If the item doesn't have a note, check to see if the stash has a valid note?
        if 'note' not in item_dict:
            if stash_dict['stash'].startswith("~"):
                item_dict['note'] = stash_dict['stash']

        if 'note' in item_dict:
            # Parse out price, save if good
            price = Price(
                    item_dict['note'], 
                    item_dict.get('stackSize', 1)
            )
            try:
                if price.parse():
                    item_dict['_value'] = price.value
                    item_dict['_value_name'] = price.value_name
            except TypeError:
                self.log.exception("Type error when parsing item")
                self.log.error(item_dict)
                self.log.error("Check the above for bad `stackSize` field?")
                return None

        item_dict['stash_id'] = stash_dict['id']
        item_dict.pop("descrText", None)
        item_dict.pop("flavourText", None)
        item_dict.pop("icon", None)
        item_dict.pop("socketedItems", None)
        # category = item_dict['e']

        if 'id' not in item_dict:
            return None

        # TODO: Verify and check items before storage
        op = pymongo.UpdateOne(
                {"id":item_dict['id']},
                {
                    "$setOnInsert": {
                        "_createdAt": datetime.datetime.utcnow(),
                        "_sold": False
                    },
                    "$set": {**item_dict, "_updatedAt": datetime.datetime.utcnow()}
                },
                upsert=True
        )
        self.update_dict['items'].append(op)

        if item_dict['extended']['category'] == 'currency':
            # await self.process_currency(item_dict)
            pass

        return item_dict['id']


    async def process_currency(self, item_dict):
        """Given some currency from the API, process it fully into the DB
        """

        item_dict.pop("identified", None)
        item_dict.pop("inventoryId", None)
        item_dict.pop("properties", None)
        # item_dict.pop("extended", None)
        item_dict.pop("prophecyText", None)
        item_dict.pop("explicitMods", None)

        op = pymongo.UpdateOne(
                {"id":item_dict['id']},
                {
                    "$setOnInsert": {
                        "_createdAt": datetime.datetime.utcnow()
                    },
                    "$set": {
                        **item_dict, 
                        "_updatedAt": datetime.datetime.utcnow(),
                    }
                },
                upsert=True
        )
        self.update_dict['items.currency'].append(op)
