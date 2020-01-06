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

type_counts = defaultdict(lambda: 0)

for i in m_db.items.currency.find():
    type_counts[i['typeLine']] += 1

type_counts = {k:type_counts[k] for k in type_counts}

type_counts= {k: v for k, v in sorted(type_counts.items(), key=lambda item: item[1])}

for k,v in type_counts.items():
    print(f"{k}:{v}")

