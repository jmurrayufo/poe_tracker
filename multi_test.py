#!/usr/bin/env python3.7

from pprint import pprint
import datetime
# import json
# import os
import time
import queue

from poe_tracker.code.Log import Log
# from poe_tracker.code.POE.trade.sql import Sql

from multiprocessing import Process, Queue


class Object(object):
    pass

def Mongo(stash_queue):
    import pymongo

    client = pymongo.MongoClient('atlas.lan:27017', username='poe', password='poe', authSource='path_of_exile')
    db = client.path_of_exile
    stash_operations = []
    item_operations = []
    config_operation = None

    # Seconds between writes

    while 1:
        try:
            # Hang onto the queue for at most 5 seconds
            stashes = stash_queue.get(timeout=1)
        except queue.Empty:
            pass
        else:
            config_operation = pymongo.UpdateOne(
                {"current_next_id": {"$exists":1}},
                {'$set': 
                    {'current_next_id':stashes['next_change_id']}
                }
            )

            for stash in stashes['stashes']:
                stash_sub_dict = {i:stash[i] for i in stash if i!='items'}
                stash_sub_dict['items'] = []

                for item in stash['items']:
                    item['stash_id'] = stash['id']
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
                                "$setOnInsert": {"_createdAt": datetime.datetime.utcnow()},
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
            t1 = time.time()
            try:
                stash_result = db.stashes.bulk_write(stash_operations, ordered=False)
                item_result = db.items.bulk_write(item_operations, ordered=False)
            except pymongo.errors.AutoReconnect:
                print("Expereinced bulk_write error, sleeping")
                time.sleep(5)
            else:
                t2 = time.time()
                print()
                print(stash_result.modified_count, stash_result.upserted_count)
                print(item_result.modified_count, item_result.upserted_count)
                print(stash_queue.qsize())
                # print(t2-t1)
                stash_operations = []
                item_operations = []

        if config_operation:
            db.config.bulk_write([config_operation,])
            config_operation = None

        MongoCleaner()

def MongoCleaner():
    import pymongo

    client = pymongo.MongoClient('atlas.lan:27017', username='poe', password='poe', authSource='path_of_exile')
    db = client.path_of_exile

    config = db.config.find_one()

    updated_pointer = config['filter_updated_pointer']

    if datetime.datetime.utcnow() - updated_pointer < datetime.timedelta(minutes=5): 
        return

    print(f"Currently rently {datetime.datetime.utcnow() - updated_pointer} behind")

    start_update = time.time()

    element = 0
    sold = 0
    t1 = time.time()
    for stash in db.stashes.find({"_updatedAt": {"$gt": updated_pointer}}, sort=[('_updatedAt', 1)]):
        if time.time() - start_update > 10:
            print("Timeout reached...")
            break
        updated_pointer = stash['_updatedAt']

        results = db.items.delete_many(
            {
                "stash_id":stash['id'],
                "id": {"$not":{"$in": stash['items']}}
            }
        )
        sold += results.deleted_count

        element += len(stash['items'])

    db.config.update_one({},{"$set":{"filter_updated_pointer":updated_pointer}})
    print(f"Loop took {datetime.timedelta(seconds=time.time()-t1)} ({element/(time.time()-t1):,.0f} stashes/s). Found {sold}/{element} missing items. Currently {datetime.datetime.utcnow() - updated_pointer} behind")



def POE(stash_queue):
    from poe_tracker.code.POE.trade.api import TradeAPI
    from poe_tracker.code.POE.trade.item import ItemGenerator

    import pymongo

    client = pymongo.MongoClient('atlas.lan:27017', username='poe', password='poe', authSource='path_of_exile')
    db = client.path_of_exile

    config = db.config.find_one()

    args = Object()
    args.name = "test"
    args.log_level = "INFO"

    # Do simple setup
    log = Log(args)

    x = TradeAPI() # We should move this someplace secure...
    # print("Syncing (this might take a while)")
    # x.sync_change_ids()
    x.set_next_change_id(config['current_next_id'])

    for data in x.iter_data():
        stash_queue.put(data)
        # print(x.gen_change_id())
        # print(f"POE: {stash_queue.qsize()}")

stash_queue = Queue()

pMongo = Process(target=Mongo, args=(stash_queue,))
pPOE = Process(target=POE, args=(stash_queue,))

print("Start POE Trade API")
pPOE.start()

while stash_queue.qsize() == 0:
    time.sleep(1)
print("Start Mongo")
pMongo.start()



try:
    while 1:
        time.sleep(1)
finally:
    print("Kill POE")
    pPOE.kill()
    print("Kill Mongo")
    pMongo.kill()
