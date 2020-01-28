
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
from . import pre_processor, post_processor

class Trade_Loop:

    def __init__(self, args):
        self.log = Log()
        self.args = args
        self.config = Config()
        self.api_queue = asyncio.Queue()
        self.db = mongo.Mongo().db
        self.mongo = mongo.Mongo()


    async def loop(self):
        """
        Run the main loop of tracking various POE stuffs
        """
        self.log.info(f"Booted trade loop")
        if self.config[self.args.env]['trade']['ingest']:
            ingest_to_db_task = asyncio.create_task(self.ingest_to_db())
            queue_stash_task = asyncio.create_task(self.queue_up_stashes())
        else:
            ingest_to_db_task = None
            queue_stash_task = None
            self.log.warning("Config was set to not ingest trading. Aborting trade_loop.")

        if self.config[self.args.env]['trade']['post_process']:
            cleaner_task = asyncio.create_task(self.cleaner())
        else:
            cleaner_task = None
            self.log.warning("Config was set to not process trading. Aborting post_process_loop.")

        while 1:
            await asyncio.sleep(1)

            if ingest_to_db_task and ingest_to_db_task.done():
                try:
                    r = ingest_to_db_task.result()
                except (KeyboardInterrupt, SystemExit):
                    return
                except Exception as e:
                    self.log.exception("Task threw exception")
                self.log.info("Restarting ingest_to_db")
                ingest_to_db_task = asyncio.create_task(self.ingest_to_db())

            if queue_stash_task and queue_stash_task.done():
                try:
                    r = queue_stash_task.result()
                except (KeyboardInterrupt, SystemExit):
                    return
                except Exception as e:
                    self.log.exception("Task threw exception")
                self.log.info("Restarting queue_up_stashes")
                queue_stash_task = asyncio.create_task(self.queue_up_stashes())

            if cleaner_task and cleaner_task.done():
                try:
                    r = cleaner_task.result()
                except (KeyboardInterrupt, SystemExit):
                    return
                except Exception as e:
                    self.log.exception("Task threw exception")
                self.log.info("Restarting cleaner")
                cleaner_task = asyncio.create_task(self.cleaner())


    async def ingest_to_db(self):
        last_poe_ninja_update = time.time()
        
        self.log.info("Begin ingesting items/stashes into DB")

        while 1:
            await asyncio.sleep(0)
            # This item will wait until something enters the queue
            api_dict = await self.api_queue.get()

            pre_proc = pre_processor.PreProcessor(api_dict)
            await pre_proc.process_api()

            # Generate a new 

            # Log every minute
            if time.time() - last_poe_ninja_update > 60:
                last_good_change_id = ChangeID(api_dict['next_change_id'])

                poe_ninja_change_id = ChangeID()
                await poe_ninja_change_id.async_poe_ninja()
                
                self.log.debug(f"ChangeID delta: {poe_ninja_change_id-last_good_change_id}")
                last_poe_ninja_update = time.time()
                
                self.log.debug(f"ChangeID: {last_good_change_id}")


    async def queue_up_stashes(self):
        self.log.info("Begin queue_up_stashes")

        cache = await self.db.cache.find_one({"name":"trade"})

        api = TradeAPI() # We should move this someplace secure...
        # print("Syncing (this might take a while)")
        # api.sync_change_ids()
        api.set_next_change_id(cache['current_next_id'])
        # api.sync_poe_ninja()

        async for data in api.iter_data():
            await asyncio.sleep(0)
            await self.api_queue.put(data)
            # Allow other tasks to run
            await asyncio.sleep((self.api_queue.qsize()/10)**2)


    async def cleaner(self):
        self.log.info("Begin cleaning updated items")

        post_proc =  post_processor.PostProcessor()

        next_scub = datetime.datetime.now()
        
        while 1:
            await asyncio.sleep(0)
            if datetime.datetime.now() < next_scub:
                dt = next_scub - datetime.datetime.now()
                dt = dt.total_seconds()
                dt = max(0, dt)
                await asyncio.sleep(dt)
            
            await post_proc.clean_pass(60)
            await post_proc.push_influx_stats()

            next_scub += datetime.timedelta(minutes=1)
