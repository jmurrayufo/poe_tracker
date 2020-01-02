#!/usr/bin/env python

import pymongo
import time
from collections import defaultdict

client = pymongo.MongoClient('atlas.lan:27017', 
                    username='poe', 
                    password='poe', 
                    authSource='admin')

db = client.path_of_exile_dev

counts = defaultdict(lambda: 0)
max_val = 0

for i in db.stashes.find({"accountName":{"$ne":None}}):
    counts[i['accountName']] += 1
    if counts[i['accountName']] > max_val:
        print(i['accountName'], counts[i['accountName']])
        max_val = counts[i['accountName']]
        time.sleep(1/30)
