
import pymongo
import datetime
import motor.motor_asyncio
import asyncio

from ..Singleton import Singleton
from ..Log import Log
from ..args import Args
from ..watchdog import watchdog
import os

from collections import defaultdict

class Mongo(metaclass=Singleton):

    def __init__(self):
        self.ready = False
        self.log = Log()
        self.args = Args()

        if self.args.env == 'dev':
            self.log.info("Booting into dev env")
            client = motor.motor_asyncio.AsyncIOMotorClient('atlas.lan:27017', 
                                                            username=os.environ['MONGODB_USERNAME'], 
                                                            password=os.environ['MONGODB_PASSWORD'], 
                                                            authSource='admin')
            self.db = client.path_of_exile_dev
        if self.args.env == 'prod':
            self.log.info("Booting into prod env")
            client = motor.motor_asyncio.AsyncIOMotorClient('atlas.lan:27017', 
                                                            username=os.environ['MONGODB_USERNAME'], 
                                                            password=os.environ['MONGODB_PASSWORD'], 
                                                            authSource='admin')
            self.db = client.path_of_exile
        self.log.info("Mongo Connection init completed")

        # No bulk write operations in progress
        self.bulk_write_task = None
        self.bulk_write_queues = defaultdict(lambda: [])
        self.lock = asyncio.Lock()

    async def setup(self):
        """Ensure DB is setup for use
        """
        self.log.info("Begin mongo setup")

        boot_task = asyncio.create_task(self.boot_loop())

        try:
            # db.cache
            self.log.info("Setup db.cache")
            self.log.info("Init cache indexes")
            self.log.info("Create 'frameType_next_id_type' index")
            await self.db.cache.create_index(
                    [("name", 1)], 
                    name="name",
                    unique=True)
            self.log.info("Init trade cache items")
            await self.db.cache.update_one(
                    {"name": "trade"},
                    {"$setOnInsert":
                        {"name" : "trade",
                         "current_next_id" : "1-1-1-1-1",
                         "filter_updated_pointer" : datetime.datetime.utcnow()
                        }
                    },
                    upsert=True
            )


            # db.index_markers
            self.log.info("Setup db.index_markers")
            self.log.info("Init index_markers indexes")
            self.log.info("Create 'frameType_next_id_type' index")
            await self.db.index_markers.create_index(
                    [("frameType", 1),
                     ("next_id", 1),
                     ("type", 1),
                    ], 
                    name="frameType_next_id_type",
                    unique=True)
            self.log.info("Init index_markers items")
            for i in range(10):
                await self.db.index_markers.update_one(
                        {"type": "implicitMods", "frameType": i},
                        {
                            "$setOnInsert": {
                                "type": "implicitMods",
                                "next_id": 0,
                                "frameType":i,
                            }
                        },
                        upsert=True,
            )
                await self.db.index_markers.update_one(
                        {"type": "explicitMods", "frameType": i},
                        {
                            "$setOnInsert": {
                                "type": "explicitMods",
                                "next_id": 0,
                                "frameType":i,
                            }
                        },
                        upsert=True,
            )


            # db.items
            self.log.info("Setup db.items")
            self.log.info("Init items indexes")
            self.log.info("Create 'createdAt' index")
            await self.db.items.create_index(
                    [('_createdAt', 1)],
                    name="createdAt"
            )
            self.log.info("Create 'updatedAt' index")
            await self.db.items.create_index(
                    [('_updatedAt', 1)],
                    name="updatedAt",
                    expireAfterSeconds=3*24*60*60
            )
            self.log.info("Create 'category' index")
            await self.db.items.create_index(
                    [('extended.category', 1)],
                    name="category",
            )
            self.log.info("Create 'id' index")
            await self.db.items.create_index(
                    [('id', 1)],
                    name="id",
                    unique=True,
            )
            self.log.info("Create 'id_hashed' index")
            await self.db.items.create_index(
                    [('id', 'hashed')],
                    name="id_hashed",
            )
            self.log.info("Create 'league' index")
            await self.db.items.create_index(
                    [('league', 1)],
                    name="league",
            )
            self.log.info("Create 'name' index")
            await self.db.items.create_index(
                    [('name', 1)],
                    name="name",
            )
            self.log.info("Create 'typeLine' index")
            await self.db.items.create_index(
                    [('typeLine', 1)],
                    name="typeLine",
            )
            self.log.info("Create 'note' index")
            await self.db.items.create_index(
                    [('note', 1)],
                    name="note",
                    sparse=True,
            )
            self.log.info("Create 'stash_id' index")
            await self.db.items.create_index(
                    [('stash_id', 1)],
                    name="stash_id",
            )
            self.log.info("Create '_value_name' index")
            await self.db.items.create_index(
                    [('_value_name', 1)],
                    name="_value_name",
                    sparse=True
            )
            self.log.info("Create '_value' index")
            await self.db.items.create_index(
                    [('_value', 1)],
                    name="_value",
                    sparse=True
            )

            # db.items.currency
            # self.log.info("Setup db.items.currency")
            # self.log.info("Create 'id' index")
            # await self.db.items.currency.create_index(
            #         [('id', 1)],
            #         name="id",
            #         unique=True,
            # )
            # self.log.info("Create 'typeLine' index")
            # await self.db.items.currency.create_index(
            #         [('typeLine', 1)],
            #         name="typeLine",
            # )
            # self.log.info("Create 'updatedAt' index")
            # await self.db.items.currency.create_index(
            #         [('_updatedAt', 1)],
            #         name="updatedAt",
            #         expireAfterSeconds=1*6*60*60
            # )
            # self.log.info("Create 'league' index")
            # await self.db.items.currency.create_index(
            #         [('league', 1)],
            #         name="league",
            # )
            # self.log.info("Create '_value_name' index")
            # await self.db.items.currency.create_index(
            #         [('_value_name', 1)],
            #         name="_value_name",
            # )
            # self.log.info("Create '_value' index")
            # await self.db.items.currency.create_index(
            #         [('_value', 1)],
            #         name="_value",
            # )

            # db.items.price.cache
            self.log.info("Setup db.items.price.cache")
            self.log.info("Create 'typeLine' index")
            await self.db.items.price.cache.create_index(
                    [('typeLine', 1)],
                    name="typeLine",
                    unique=True,
            )
            self.log.info("Create '_value_name' index")
            await self.db.items.price.cache.create_index(
                    [('_value_name', 1)],
                    name="_value_name",
            )
            self.log.info("Create '_value' index")
            await self.db.items.price.cache.create_index(
                    [('_value', 1)],
                    name="_value",
            )

            # db.items.mods
            self.log.info("Setup db.items.mods")
            self.log.info("Init items indexes")
            self.log.info("Create 'frameType' index")
            await self.db.items.mods.create_index(
                    [('frameType', 1)],
                    name="frameType",
                    unique=True,
            )
            self.log.info("Create 'id' index")
            await self.db.items.mods.create_index(
                    [('id', 1)],
                    name="id",
                    unique=True,
            )
            self.log.info("Create 'type' index")
            await self.db.items.mods.create_index(
                    [('type', 1)],
                    name="type",
                    unique=True,
            )


            # db.items.sold
            self.log.info("Setup db.items.sold")
            self.log.info("Create 'id' index")
            await self.db.items.sold.create_index(
                    [('id', 1)],
                    name="id",
                    unique=True,
            )
            self.log.info("Create 'updatedAt' index")
            # await self.db.items.create_index(
            #         [('_updatedAt', 1)],
            #         name="updatedAt",
            #         expireAfterSeconds=3*24*60*60
            # )


            # db.stashes
            self.log.info("Setup db.stashes")
            self.log.info("Init stashes indexes")
            self.log.info("Create 'createdAt' index")
            await self.db.stashes.create_index(
                    [('_createdAt', 1)],
                    name="createdAt"
            )
            self.log.info("Create 'updatedAt' index")
            await self.db.stashes.create_index(
                    [('_updatedAt', 1)],
                    name="updatedAt",
                    expireAfterSeconds=3*24*60*60,
            )
            self.log.info("Create 'id_hashed' index")
            await self.db.stashes.create_index(
                    [('id', 'hashed')],
                    name="id_hashed",
            )
            self.log.info("Create 'id' index")
            await self.db.stashes.create_index(
                    [('id', 1)],
                    name="id",
                    unique=True,
            )
            self.log.info("Create 'accountName' index")
            await self.db.stashes.create_index(
                    [('accountName', 1)],
                    name="accountName",
            )

            # db.characters.xp
            self.log.info("Setup db.characters.xp")
            self.log.info("Create 'date_name' index")
            await self.db.characters.xp.create_index(
                    [('date', 1),('name',1)],
                    name="date_name",
                    unique=True,
            )

        finally:
            boot_task.cancel()

        self.log.info("Finish mongo setup")


    async def boot_loop(self):
        """While booting, request more time from the notification system while we wait for mongo to do it's thing.
        """
        await asyncio.sleep(5)
        self.log.info("Taking a while to boot, lets remind the system to let us boot.")

        wd = watchdog.Watchdog()
        try:
            while 1:
                wd.long_boot(1)
                await asyncio.sleep(30)
                self.log.debug("Loop...")
        finally:
            self.log.info("Finished boot looper")


    async def bulk_write(self, op, queue_name):
        # We accept both single operations, and bulk writes
        async with self.lock:
            if type(op) in [list,tuple]:
                for o in op:
                    self.bulk_write_queues[queue_name].append(o)
            else:
                self.bulk_write_queues[queue_name].append(op)
        if self.bulk_write_task is None:
            self.bulk_write_task = asyncio.create_task(self.write_worker())
            await asyncio.sleep(0)


    async def write_worker(self):
        """Background task to commit writes to the DB
        """
        # Queue up writes for 15 seconds, then burst to server.
        # TODO: Make config value
        await asyncio.sleep(15)

        for queue in self.bulk_write_queues:
            if len(self.bulk_write_queues[queue]):
                break
        else:
            self.bulk_write_task = None
            return

        async with self.lock:
            for queue in self.bulk_write_queues:
                if len(self.bulk_write_queues[queue]) == 0:
                    continue
                ops = self.bulk_write_queues[queue]
                # Blank out list to allow fresh new one for next insert
                self.bulk_write_queues[queue] = []

                col = self.db.get_collection(name=queue)
                await col.bulk_write(ops, ordered=False)

        self.bulk_write_task = asyncio.create_task(self.write_worker())
