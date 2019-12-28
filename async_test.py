#!/usr/bin/env python3.7

from pprint import pprint
import datetime
# import json
# import os
import time
import queue
import asyncio

from poe_tracker.code.Log import Log
# from poe_tracker.code.POE.trade.sql import Sql

async def Mongo(stash_queue):
    from poe_tracker.code.POE.trade.change_id import ChangeID

    import pymongo
    import motor.motor_asyncio
    import copy

    client = motor.motor_asyncio.AsyncIOMotorClient('atlas.lan:27017', username='poe', password='poe', authSource='path_of_exile')
    db = client.path_of_exile
    stash_operations = []
    item_operations = []
    config_operation = None
    last_good_change_id = ChangeID()
    last_poe_ninja_update = time.time()
    log = Log()

    # Seconds between writes

    while 1:
        if stash_queue.qsize():
            stashes = await stash_queue.get()
            config_operation = pymongo.UpdateOne(
                {"current_next_id": {"$exists":1}},
                {'$set': 
                    {'current_next_id':stashes['next_change_id']}
                }
            )
            last_good_change_id = ChangeID(stashes['next_change_id'])

            for stash in stashes['stashes']:
                stash_sub_dict = copy.deepcopy(stash)
                stash_sub_dict['items'] = []

                for item in stash['items']:
                    if 'note' not in item:
                        continue
                    item['stash_id'] = stash['id']
                    item.pop("descrText", None)
                    item.pop("flavourText", None)

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
                    stash_result = await db.stashes.bulk_write(stash_operations, ordered=False)
                    item_result = await db.items.bulk_write(item_operations, ordered=False)
                except pymongo.errors.AutoReconnect:
                    log.exception("Expereinced bulk_write error, sleeping")
                    time.sleep(5)
                else:
                    log.info('')
                    log.info(f"Stashes: Mod: {stash_result.modified_count:,d} Up: {stash_result.upserted_count:,d}")
                    log.info(f"  Items: Mod: {item_result.modified_count:,d} Up: {item_result.upserted_count:,d}")
                    # log.info(f"{stash_queue.qsize()}")
                    if time.time() - last_poe_ninja_update > 30:
                        poe_ninja_change_id = ChangeID()
                        poe_ninja_change_id.sync_poe_ninja()
                        log.info(f"ChangeID delta: {poe_ninja_change_id-last_good_change_id}")
                        last_poe_ninja_update = time.time()
                    log.info(f"ChangeID: {last_good_change_id}")
                    stash_operations = []
                    item_operations = []

            if config_operation:
                await db.config.bulk_write([config_operation,])
                config_operation = None
        else:
            await asyncio.sleep(1)
        await MongoCleaner()

async def MongoCleaner():
    import pymongo
    log = Log()

    client = pymongo.MongoClient('atlas.lan:27017', username='poe', password='poe', authSource='path_of_exile')
    db = client.path_of_exile

    config = db.config.find_one()

    updated_pointer = config['filter_updated_pointer']

    if datetime.datetime.utcnow() - updated_pointer < datetime.timedelta(minutes=15): 
        return

    log.info(f"Currently {datetime.datetime.utcnow() - updated_pointer} behind")

    start_update = time.time()

    element = 0
    sold = 0
    t1 = time.time()
    for stash in db.stashes.find({"_updatedAt": {"$gt": updated_pointer}}, sort=[('_updatedAt', 1)]):
        if time.time() - start_update > 10:
            log.warning("Timeout reached...")
            break

        updated_pointer = stash['_updatedAt']

        #TODO: Copy currency items up to the currency DB

        results = db.items.delete_many(
            {
                "stash_id":stash['id'],
                "id": {"$not":{"$in": stash['items']}}
            }
        )
        sold += results.deleted_count

        element += len(stash['items'])

    db.config.update_one({},{"$set":{"filter_updated_pointer":updated_pointer}})
    log.info(f"Loop took {datetime.timedelta(seconds=time.time()-t1)} ({element/(time.time()-t1):,.0f} stashes/s). Found {sold}/{element} missing items. Currently {datetime.datetime.utcnow() - updated_pointer} behind")



async def POE(stash_queue):
    from poe_tracker.code.POE.trade.change_id import ChangeID
    from poe_tracker.code.POE.trade.api import TradeAPI
    from poe_tracker.code.POE.trade.item import ItemGenerator

    import pymongo
    log = Log()

    log.info("Begin POE")

    client = pymongo.MongoClient('atlas.lan:27017', username='poe', password='poe', authSource='path_of_exile')
    db = client.path_of_exile

    config = db.config.find_one()


    x = TradeAPI() # We should move this someplace secure...
    # print("Syncing (this might take a while)")
    # x.sync_change_ids()
    x.set_next_change_id(config['current_next_id'])
    # x.sync_poe_ninja()

    async for data in x.iter_data():
        await stash_queue.put(data)
        # Allow other tasks to run
        await asyncio.sleep(0)
        log.info(f"POE: {stash_queue.qsize()}")

class Object:
    pass

args = Object()
args.name = "test"
args.log_level = "INFO"

# Do simple setup
log = Log(args)

loop = asyncio.get_event_loop()

stash_queue = asyncio.Queue(loop=loop)

loop.create_task(Mongo(stash_queue))
loop.create_task(POE(stash_queue))
try:
    loop.run_forever()
except KeyboardInterrupt:
    # log.exception("Catch and accept")
    pass