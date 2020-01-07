import datetime
import pymongo
import time
import asyncio

from .price import Price
from .. import mongo
from ...Log import Log
from .change_id import ChangeID

class PreProcessor:

    
    def __init__(self):
        self.mongo = mongo.Mongo()
        self.log = Log()


    async def process_api(self, api_dict):
        """Given a full api raw dict, process it into the mongo db
        """

        # Process and queue up items for writes
        for stash in api_dict['stashes']:
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
                    'current_next_id': api_dict['next_change_id'],
                    'change_id_last_update': now,
                }
            }
        )
        await self.mongo.bulk_write(op, "cache")
        await ChangeID(api_dict['next_change_id']).post_to_influx()


    async def process_stash(self, stash_dict):
        """Given a raw stash from the API, process it fully into the DB
        """

        # XXX Newly emptied stashes break here... Should we take the time to check them?
        if len(stash_dict['items']) == 0:
            return

        # Loop through items and build list of `id`s.
        new_ids = []
        for item_dict in stash_dict['items']:
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
        await self.mongo.bulk_write(op, "stashes")


    async def process_item(self, item_dict, stash_dict):
        """Given a raw item from the API, process it fully into the DB
        Returns:
            id of item
        """

        # TODO: If the item doesn't have a note, check to see if the stash has a valid note?
        if 'note' not in item_dict:
            if not stash_dict['stash'].startswith("~"):
                return None
            item_dict['note'] = stash_dict['stash']

        price = Price(item_dict['note'])
        item_dict['_value'] = price.value
        item_dict['_value_name'] = price.value_name

        item_dict['stash_id'] = stash_dict['id']
        item_dict.pop("descrText", None)
        item_dict.pop("flavourText", None)
        item_dict.pop("icon", None)
        item_dict.pop("socketedItems", None)

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

        await self.mongo.bulk_write(op, "items")

        if item_dict['extended']['category'] == 'currency':
            await self.process_currency(item_dict)

        return item_dict['id']


    async def process_currency(self, item_dict):
        """Given some currency from the API, process it fully into the DB
        """

        item_dict.pop("identified", None)
        item_dict.pop("inventoryId", None)
        item_dict.pop("properties", None)
        item_dict.pop("extended", None)
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

        await self.mongo.bulk_write(op, "items.currency")
