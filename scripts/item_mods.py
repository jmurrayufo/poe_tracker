#!/usr/bin/env python3.7

import pymongo
from pprint import pprint
import time
import datetime
import os
import re







class ModFinder:

    client = pymongo.MongoClient('atlas.lan:27017', username='poe', password='poe', authSource='admin')
    db = client.path_of_exile_dev

    re_pat = re.compile(r"-?\d+(?:\.\d+)?")

    def __init__(self):

        max_index = self.db.items.mods.find_one({},sort=[("index",-1)])
        if max_index:
            self.index_counter = max_index['index']+1
        else:
            self.index_counter = 0
        print(f"Init with index of {self.index_counter}")
        time.sleep(1)


    def insert_mod(self, mod, _type, frameType):
        if mod == "":
            return
        mod_numbers = self.re_pat.findall(mod)
        (mod, numbers) = self.re_pat.subn(r"{}",mod)

        item_dict = self.db.items.mods.find_one(
                {
                    "name":mod,
                    "type":_type,
                },
                sort=[("index",-1)]
        )

        if item_dict:
            _index = item_dict['index']
        else:
            _index = self.index_counter
            self.index_counter += max(1, numbers)

        if numbers:
            self.mongo_update(mod, _type, _index, numbers, mod_numbers)
        else:
            self.mongo_update(mod, _type, _index, 1, [1.0])

    def mongo_update(self, mod, _type, _index, numbers, max_val):
        # print(f"Insert on {_index:4d} `{mod}`")

        max_dict = {}
        max_index = 0
        for m in max_val:
            max_dict[f"norm.{max_index}"] = abs(float(m))
            max_index += 1

        if len(max_dict) == 0:
            max_dict["norm.0"] = 1.0

        result = self.db.items.mods.find_one_and_update(
                {
                    "name":mod,
                    "type":_type,
                    "index":_index
                },
                {
                    "$setOnInsert": {
                        "name":mod, 
                        "type":_type,
                        "numbers":numbers,
                        "index":_index,
                        # "norm": []
                    },
                    "$max": {
                        **max_dict
                    }
                },
                upsert=True,
        )
        return

    def run(self):
        t0 = time.time()
        dt0 = datetime.datetime.now()
        i = 0
        last_update = time.time()
        for item in self.db.items.find({},sort=[("_updatedAt",1)]):
            if time.time() - last_update > 1:
                print(datetime.datetime.now()-dt0,f" {i:,d} ", datetime.datetime.utcnow() - item['_updatedAt'])
                last_update = time.time()
            i += 1
            if "explicitMods" in item:
                for mod in item['explicitMods']:
                    self.insert_mod(mod, "explicit", item['frameType'])
            if "implicitMods" in item:
                for mod in item['implicitMods']:
                    self.insert_mod(mod, "implicit", item['frameType'])
            if "craftedMods" in item:
                for mod in item['craftedMods']:
                    self.insert_mod(mod, "craft", item['frameType'])
            if "enchantMods" in item:
                for mod in item['enchantMods']:
                    self.insert_mod(mod, "enchant", item['frameType'])


if __name__ == '__main__':
    x = ModFinder()
    x.run()