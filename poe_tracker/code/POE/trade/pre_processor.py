import datetime
import pymongo
import time
import asyncio

from . import price
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
                "filter_updated_pointer": {"$lt": now}
            },
            {'$set': 
                {
                    'current_next_id': api_dict['next_change_id'],
                    'filter_updated_pointer': now,
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
        for item in stash_dict['items']:
            _id = await self.process_item(item, stash_dict)
            if _id is None:
                continue
            new_ids.append(_id)

        # Repalce `items` field with array of `id` values
        stash_dict['items'] = new_ids

        op = pymongo.UpdateOne(
                {"id":stash_dict['id']},
                {
                    "$setOnInsert": {"_createdAt": datetime.datetime.utcnow()},
                    "$set": {**stash_dict, "_updatedAt": datetime.datetime.utcnow()}
                },
                upsert=True
        )
        await self.mongo.bulk_write(op, "stashes")
        # Commit to mongodb


    async def process_item(self, item_dict, stash_dict):
        """Given a raw item from the API, process it fully into the DB
        Returns:
            id of item
        """

        # TODO: If the item doesn't have a note, check to see if the stash has a valid note?
        # if 'note' not in item:
        #     continue
        item_dict['stash_id'] = stash_dict['id']
        item_dict.pop("descrText", None)
        item_dict.pop("flavourText", None)
        item_dict.pop("icon", None)

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

        return item_dict['id']


    async def process_currency(self, item_dict):
        """Given some currency from the API, process it fully into the DB
        """

