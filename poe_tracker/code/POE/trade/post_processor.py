import asyncio
import httpx
import time
import datetime

from ...Config import Config
from ...Log import Log
from ...args import Args
from .change_id import ChangeID
from .. import mongo

class PostProcessor:

    influxDB_host = "http://192.168.4.3:8086"
    
    def __init__(self):
        self.log = Log()
        self.args = Args()
        self.config = Config()
        self.stash_queue = asyncio.Queue()
        self.db = mongo.Mongo().db

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


    async def push_influx_stats(self):
        # self.log.info("Grab stats from mongo")
        collections = await self.db.list_collections()
        # collections = await collections.to_list()
        data = ""
        for col in collections:
            stats = await self.db.command("collstats", col['name'])
            data += f"mongo_db_stats,env={self.args.env},name={col['name']} "

            data_buffer = []
            for key in ['size', 'count', 'storageSize', 'nindexes', 'totalIndexSize', 'avgObjSize']:
                if key in stats:
                    data_buffer.append(f"{key}={stats[key]}")

            data += ','.join(data_buffer)
            data += "\n"
        self.log.debug(data)

        host = self.influxDB_host + '/write'
        params = {"db":"poe","precision":"m"}
        try:
            r = await httpx.post( host, params=params, data=data, timeout=1)
            r.raise_for_status()
            pass
            # print(data)
        except (KeyboardInterrupt, SystemExit, RuntimeError):
            raise
            return
        except Exception as e:
            self.log.exceptin("Posting to InfluxDB threw exception")


    async def clean_pass(self, timeout):
        updated_pointer = (await self.db.cache.find_one({"name":"trade"}))['filter_updated_pointer']

        # self.log.info(f"Currently {datetime.datetime.utcnow() - updated_pointer} behind")

        if (datetime.datetime.utcnow() - updated_pointer) < datetime.timedelta(minutes=5):
            return
        start_update = time.time()
        self.log.info("Begin cleaning process")

        element = 0
        sold = 0
        t1 = time.time()
        async for stash in self.db.stashes.find({"_updatedAt": {"$gte": updated_pointer}}, sort=[('_updatedAt', 1)]):
            await asyncio.sleep(0)
            
            updated_pointer = stash['_updatedAt']

            if (datetime.datetime.utcnow() - updated_pointer) < datetime.timedelta(minutes=1) or time.time() - t1 > timeout:
                break

            #TODO: Copy currency items up to the currency self.DB

            results = self.db.items.find(
                {
                    "stash_id":stash['id'],
                    "id": {"$not":{"$in": stash['items']}}
                }
            )

            results = await results.to_list(None)
            for sold_item in results:
                # Add to sold items
                if "note" in sold_item:
                    sold_item.pop("_id", None)
                    sold_item.pop("_updatedAt", None)
                    sold_item.pop("_createdAt", None)
                    sold_item.pop("stash_id", None)
                    await self.db.items.sold.find_one_and_update(
                            {"id":sold_item['id']},
                            {
                                "$set": {**sold_item,"_updatedAt": datetime.datetime.utcnow()},
                                "$setOnInsert": {"_createdAt": datetime.datetime.utcnow()},
                            },
                            upsert=True
                    )
                    sold += 1

                # Delete
                await self.db.items.delete_one(
                        {"id":sold_item['id']}
                )

            element += len(stash['items'])

        # Step back one second to better cover next cleaning operation
        # updated_pointer -= datetime.timedelta(seconds=1)

        await self.db.cache.update_one({"name":"trade"},{"$set":{"filter_updated_pointer":updated_pointer}})
        self.log.info(f"Cleaning {element/(time.time()-t1):,.0f} stashes/s. Found {sold:,d}/{element:,d} missing items. Currently {datetime.datetime.utcnow() - updated_pointer} behind")
