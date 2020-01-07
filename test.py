#!/usr/bin/env python


from collections import defaultdict
from poe_tracker.code.POE.trade.price import Price
import datetime
import pymongo
import re
import time
from pprint import pprint

# tzinfo.utcoffset
client = pymongo.MongoClient('atlas.lan:27017', 
                    username='poe', 
                    password='poe', 
                    authSource='admin')

m_db = client.path_of_exile_dev

values = defaultdict(lambda: 0)
try:
    for item in m_db.items.find({"_value_name":{"$exists":1}}):
        values[item['_value_name']] += 1
finally:
    pprint(values)

