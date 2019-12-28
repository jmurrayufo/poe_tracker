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

i_mods = []
e_mods = []

re_pat = re.compile("\d+(?:.\d+)?")

def parse_mod(mod, _type):
    (mod, numbers) = re_pat.subn("X",mod)
    if db.mod_lookup.count_documents({"name":mod, "type":_type}):
        return
    next_id = db.index_markers.find_one_and_update(
        {"type":_type+"Mods"},
        {"$inc": {"next_id":max(1,numbers)}}
        )['next_id']
    # print(next_id)

    db.mod_lookup.insert_one(
        {"name":mod, 
         "id":next_id, 
         "type":_type,
         "numbers":numbers}
        )


    # print(mod)
i = 0
for item in db.items.find({}):
    print(i, datetime.datetime.utcnow() - item['_createdAt'])
    i += 1
    if "explicitMods" in item:
        for mod in item['explicitMods']:
            parse_mod(mod, "explicit")
    if "implicitMods" in item:
        for mod in item['implicitMods']:
            parse_mod(mod, "implicit")



# print("Purging DB of currency")
# db.currency.delete_many({})

# print("Importing currency")
# for item in db.items.find({}):
#     if item['extended']['category'] != "currency":
#         continue
#     if "~" in item['note']:
#         p = Price(item['note'])
        
#         if not p.parse():
#             continue

#         currency = {}
#         currency['typeLine'] = item['typeLine']
#         currency['value'] = p.value
#         currency['value_name'] = p.value_name
#         currency['count'] = item.get("stackSize", 1)
#         currency['id'] = item['id']
#         currency['league'] = item['league']
#         currency['_insertedAt'] = datetime.datetime.utcnow()
#         # print(item['typeLine'], p.value, p.value_name, item.get("stackSize", 1))
#         try:
#             db.currency.insert_one(currency)
#         except pymongo.errors.DuplicateKeyError:
#             pass

# Lets try to predict the value of an Exalt!
