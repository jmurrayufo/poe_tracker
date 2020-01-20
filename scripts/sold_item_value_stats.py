#!/usr/bin/env python3.7

import pymongo
from pprint import pprint
import time
import datetime
import os
import re
import numpy as np



def convert_value(value, value_name, db):
    if value_name == "Chaos Orb":
        return value
    cache_dict = db.items.price.cache.find_one({"typeLine":value_name, "league":"Metamorph"})
    if cache_dict is None:
        return None
    return cache_dict['_value'] * value



class ModFinder:

    client = pymongo.MongoClient('atlas.lan:27017', username='poe', password='poe', authSource='admin')
    db = client.path_of_exile_dev


    def __init__(self):
        pass


    def run(self):
        t0 = time.time()
        dt0 = datetime.datetime.now()
        i = 0
        last_update = time.time()
        values = []
        for item in self.db.items.sold.find({}, limit=1000):
            v = convert_value(item['_value'], item['_value_name'], self.db)
            if v is None:
                continue
            values.append(v)
        edges = np.logspace(0,1,16)
        edges = np.insert(edges, 0, 0)
        edges = np.append(edges, 1e9)
        edges = [0,1,2,5,10,20,50,100,200,500,1000,2000,5000,10000,20000,50000,100000]
        edges = [0,1,2,5,10,20,50,100,200,500,1000,100000]
        print(edges)
        bins = np.histogram(values, bins=edges)
        for idx in range(len(bins[1][:-1])):
            print(f"{bins[1][idx]:>6,.0f}-{bins[1][idx+1]:<6,.0f} = {bins[0][idx]:>5,}")
        print(len(bins[0]))
        # edges = bins[1].tolist()
        edges = [int(x) for x in bins[1]]
        print(edges)



if __name__ == '__main__':
    x = ModFinder()
    x.run()
