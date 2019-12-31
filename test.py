#!/usr/bin/env python

import pymongo
from poe_tracker.code.Log import Log
from pprint import pprint
import time
import datetime
import os
import re

# SIMPLE SETUP, DON'T REMOVE
class Object:
    pass

args = Object()
args.name = "test"
args.log_level = "INFO"

log = Log(args)

# SIMPLE SETUP, DON'T REMOVE



# client = pymongo.MongoClient('atlas.lan:27017', username='poe', password='poe', authSource='path_of_exile')
# db = client.path_of_exile

# db.example.subexample.insert_one({"test":True})

# db.example.subexample2.insert_one({"test":True})
# db.example.subexample3.insert_one({"test":True})

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
