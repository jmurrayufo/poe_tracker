#!/usr/bin/env python3.7

import pymongo
from pprint import pprint
import time
import datetime
import os
import re

client = pymongo.MongoClient('atlas.lan:27017', username='poe', password='poe', authSource='admin')
db = client.path_of_exile_dev

re_pat = re.compile(r"-?\d+(?:.\d+)?")

def insert_mod(mod, _type, frameType):
    (mod, numbers) = re_pat.subn("X",mod)

    result = db.items.mods.find_one_and_update(
            {
                "name":mod,
                "type":_type,
            },
            {
                "$setOnInsert": {
                    "name":mod, 
                    "type":_type,
                    "numbers":numbers,
                }
            },
            upsert=True,
    )
    return

t0 = time.time()
i = 0
last_update = time.time()
for item in db.items.find({},sort=[("_updatedAt",-1)]):
    if time.time() - last_update > 1:
        print(datetime.datetime.now(),f" {i:,d} ", datetime.datetime.utcnow() - item['_updatedAt'])
        last_update = time.time()
    i += 1
    if "explicitMods" in item:
        for mod in item['explicitMods']:
            insert_mod(mod, "explicit", item['frameType'])
    if "implicitMods" in item:
        for mod in item['implicitMods']:
            insert_mod(mod, "implicit", item['frameType'])
