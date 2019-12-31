#!/usr/bin/env python3.7

import pymongo
from poe_tracker.code.Log import Log
from poe_tracker.code.POE.trade.price import Price
from pprint import pprint
import time
import datetime
import os
import re

class Object:
    pass

args = Object()
args.name = "test"
args.log_level = "INFO"

# Do simple setup
log = Log(args)

client = pymongo.MongoClient('atlas.lan:27017', username='poe', password='poe', authSource='path_of_exile')
db = client.path_of_exile

pprint(db.items.index_information())
exit()

# Cleanup
db.mod_lookup.delete_many({})
db.mod_lookup.find_one_and_update(
    {"type": "explicitMods"},
    {"$set": {"next_id":0}}
    )
db.mod_lookup.find_one_and_update(
    {"type": "implicitMods"},
    {"$set": {"next_id":0}}
    )

i_mods = []
e_mods = []

re_pat = re.compile(r"\d+(?:.\d+)?")

def parse_mod(mod, _type, frameType):
    (mod, numbers) = re_pat.subn("X",mod)
    if db.mod_lookup.count_documents({"name":mod, "type":_type,"frameType":frameType}):
        return
    next_id = db.index_markers.find_one_and_update(
        {"type":_type+"Mods", "frameType":frameType},
        {"$inc": {"next_id":max(1,numbers)}}
        )['next_id']

    try:
        result = db.mod_lookup.insert_one(
            {"name":mod, 
             "id":next_id, 
             "type":_type,
             "numbers":numbers,
             "frameType":frameType}
            )
    except pymongo.errors.DuplicateKeyError:
        return

    # print(dir(result))
    # print(result.matched_count,result.modified_count)

db.index_markers.drop_indexes()
db.index_markers.delete_many({})

for i in range(10):
    db.index_markers.insert_one(
        {"type" : "implicitMods",
        "next_id" : 0,
        "frameType":i}
        )
    db.index_markers.insert_one(
        {"type" : "explicitMods",
        "next_id" : 0,
        "frameType":i}
        )

db.index_markers.create_index(
    [ ("frameType", 1), ("next_id", 1), ("type", 1) ], 
    unique=True )
    # print(mod)        
t0 = time.time()
i = 0
for item in db.items.find({},sort=[("_updatedAt",1)]):
    print(datetime.datetime.now(),f"{i:,d}", datetime.datetime.utcnow() - item['_updatedAt'])
    i += 1
    if "explicitMods" in item:
        for mod in item['explicitMods']:
            parse_mod(mod, "explicit", item['frameType'])
    if "implicitMods" in item:
        for mod in item['implicitMods']:
            parse_mod(mod, "implicit", item['frameType'])