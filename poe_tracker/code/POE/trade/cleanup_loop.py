import asyncio
import httpx
import time
import datetime

from ...Config import Config
from ...Log import Log
from ...args import Args
from .change_id import ChangeID
from .api import TradeAPI
from .. import mongo

class CleanupLoop:

    def __init__(self):
        self.log = Log()
        self.args = Args()
        self.config = Config()
        self.stash_queue = asyncio.Queue()
        self.db = mongo.Mongo().db


    async def loop(self):
        """
        Run the main loop of tracking various POE stuffs
        """
        self.log.info(f"Booted trade loop")
        if not self.config[self.args.env]['trade']['post_process']:
            self.log.warning("Config was set to not process trading. Aborting post_process_loop.")
            return
        cleaner_task = asyncio.create_task(self.cleaner())

        while 1:
            await asyncio.sleep(1)

            if cleaner_task.done():
                try:
                    r = cleaner_task.result()
                except (KeyboardInterrupt, SystemExit):
                    return
                except Exception as e:
                    self.log.exception("Task threw exception")
                self.log.info("Restarting cleaner")
                cleaner_task = asyncio.create_task(self.cleaner())


    async def cleaner(self):
        self.log.info("Begin cleaning updated items")
        while 1:

            updated_pointer = (await self.db.cache.find_one({"name":"trade"}))['filter_updated_pointer']

            # self.log.info(f"Currently {datetime.datetime.utcnow() - updated_pointer} behind")

            while (datetime.datetime.utcnow() - updated_pointer) < datetime.timedelta(minutes=2):
                await asyncio.sleep(15)
            start_update = time.time()

            element = 0
            sold = 0
            t1 = time.time()
            async for stash in self.db.stashes.find({"_updatedAt": {"$gt": updated_pointer}}, sort=[('_updatedAt', 1)]):
                await asyncio.sleep(0)
                
                updated_pointer = stash['_updatedAt']

                if (datetime.datetime.utcnow() - updated_pointer) < datetime.timedelta(minutes=1) or time.time() - t1 > 60:
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

            await self.db.cache.update_one({"name":"trade"},{"$set":{"filter_updated_pointer":updated_pointer}})
            self.log.info(f"Cleaning {element/(time.time()-t1):,.0f} stashes/s. Found {sold:,d}/{element:,d} missing items. Currently {datetime.datetime.utcnow() - updated_pointer} behind")
            await asyncio.sleep(1)


    async def push_influx_stats(self):

        pass