#!/usr/bin/env python

import pymongo
import time
from collections import defaultdict
import numpy as np

client = pymongo.MongoClient('atlas.lan:27017', 
                    username='poe', 
                    password='poe', 
                    authSource='admin')

db = client.path_of_exile_dev

total_items = db.items.count_documents({})
print(f"  Total Items: {total_items:,d}")
total_stashes = db.stashes.count_documents({})
print(f"Total Stashes: {total_stashes:,d}")
print(f"  Items/Stash: {total_items/total_stashes:,.3f}")

stash_item_counts = []
for stash in db.stashes.find():
    stash_item_counts.append(len(stash['items']))

stash_item_counts = np.asarray(stash_item_counts)


print(f"    Max Items: {stash_item_counts.max()}")
print(f" Median Items: {np.median(stash_item_counts)}")
print(f"      5th Per: {np.percentile(stash_item_counts,5)}")
print(f"     25th Per: {np.percentile(stash_item_counts,25)}")
print(f"     75th Per: {np.percentile(stash_item_counts,75)}")
print(f"     95th Per: {np.percentile(stash_item_counts,95)}")
