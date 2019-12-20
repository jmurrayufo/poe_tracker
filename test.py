#!/usr/bin/env python3.7
from poe_tracker.code.POE.trade_api import Trade_API
from pprint import pprint
import datetime
import time
import json
import os

x = Trade_API()
t = datetime.datetime.now()
x.sync_change_ids()
# exit()

# Hidden while 1 loop!
for data in x.iter_data():

    stash_count = 0
    item_count = 0
    byte_count = 0

    for stash in data['stashes']:
        stash_count += 1
        for item in stash['items']:
            item_count += 1
    byte_count = x.data_size
    # print()
    # print(f"Saw {stash_count:,d} stashes")
    # print(f"Saw {item_count:,d} itemes")
    # print(f"Total of {byte_count/(2**10):,.0f} KiB")
    # print(x.gen_change_id())
    for stash in data['stashes']:
        for item in stash['items']:
            if 'note' not in item:
                continue
            print()
            print()
            print()
            print()
            os.system("clear")
            pprint(item)
            input()

    for stash in data['stashes']:
        try:
            if stash['accountName'].lower() == 'jmurrayufo':
                print(datetime.datetime.now())
                # print(stash)
        except AttributeError:
            pass