#!/usr/bin/env python

import pymongo
import datetime
import time
from poe_tracker.code.POE.trade.price import Price

from collections import defaultdict

# tzinfo.utcoffset
client = pymongo.MongoClient('atlas.lan:27017', 
                    username='poe', 
                    password='poe', 
                    authSource='admin')

m_db = client.path_of_exile_dev

types = set()
num = 0
try:
    for item in m_db.items.find({"extended":{"$exists":1}}):
        num += 1
        if 'subcategories' in item['extended']:
            for cat in item['extended']['subcategories']:
                types.add(f"{item['extended']['category']}.{cat}")
        else:
            types.add(f"{item['extended']['category']}")
except:
    pass
finally:
    print()
    print(num)
    types = sorted([i for i in types])

    print(types)