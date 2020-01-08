#!/usr/bin/env python3.7

import pymongo
from pprint import pprint
import time
import datetime
import os
import re

client = pymongo.MongoClient('atlas.lan:27017', username='poe', password='poe', authSource='path_of_exile')
db = client.path_of_exile

re_pat = re.compile(r"\d+(?:.\d+)?")

def parse_mod(mod, _type, frameType):
    (mod, numbers) = re_pat.subn("X",mod)
    if db.mod_lookup.find({"name":mod, "type":_type,"frameType":frameType}, limit=1):
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
