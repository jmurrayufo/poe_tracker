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

for item in m_db.items.find({"extended":{"$exists":1}}):
    print(item)
    time.sleep(1)
