#!/usr/bin/env python3.7


import pymongo
from pprint import pprint
import time
import datetime
import re
import numpy as np
import tensorflow as tf
import pathlib
import asyncio

re_pat = re.compile(r"-?\d+(?:.\d+)?")

# Helper to run async couroutines for us
def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def convert_value(value, value_name, db):
    if "value_name" == "Chaos Orb":
        return value
    cache_dict = db.items.price.cache.find_one({"typeLine":value_name, "league":"Metamorph"})
    if cache_dict is None:
        return None
    return cache_dict['_value'] * value


def set_values(np_array, mod, _type, db):

    matches = re_pat.findall(mod)
    (mod_r, numbers) = re_pat.subn(r"{}",mod)

    result = db.items.mods.find_one({"name":mod_r,"type":_type,})

    if result is None:
        return
    if result['numbers']:
        for idx, num in enumerate(matches):
            normalize_value = result['norm'][str(idx)]
            np_array[result['index'] + idx] = float(num) / normalize_value
    else:
        np_array[result['index']] = 1.0

def run(max_batch_size=500, max_batches=5):
    client = pymongo.MongoClient('atlas.lan:27017', username='poe', password='poe', authSource='admin')
    db = client.path_of_exile_dev

    # Used to clasify items into buckets
    edges = [0, 1, 2, 4, 10, 21, 46, 100, 215, 464, 1000, 2154, 4641, 10000, 21544, 46415, 100000]

    array_size = 0
    for mod in db.items.mods.find():
        array_size += max(1, mod['numbers'])

    print(array_size)

    _filter = {
        # "extended.category":"jewels",
        "frameType":2,
    }

    item_batch = []
    current_batch = 0

    stats = {}
    stats['items_parsed'] = 0
    stats['time_start'] = time.time()

    # Cleanup old files
    files = pathlib.Path().glob("item_values.*.tfrecord")
    for f in files:
        f.unlink()

    for item in db.items.sold.find(_filter):
        stats['items_parsed'] += 1

        data = np.zeros(array_size, dtype=np.float32)
        item_value = convert_value(item['_value'], item['_value_name'], db)
        if item_value is None: continue
        # value = np.asarray([item['_value']/100.0], dtype=np.float32)
        value = np.zeros(16, dtype=np.float32)
        for idx in range(16):
            if item_value < edges[idx+1]:
                value[idx] = 1
                break
        try:
            if "explicitMods" in item:
                for mod in item['explicitMods']:
                    set_values(data, mod, "explicit", db)

            if "implicitMods" in item:
                for mod in item['implicitMods']:
                    set_values(data, mod, "implicit", db)

            if "craftedMods" in item:
                for mod in item['craftedMods']:
                    set_values(data, mod, "craft", db)

            if "enchantMods" in item:
                for mod in item['enchantMods']:
                    set_values(data, mod, "exhant", db)
        except ZeroDivisionError:
            continue

        example = tf.train.Example(features=tf.train.Features(feature={
                "item_properties": tf.train.Feature(float_list=tf.train.FloatList(value=data)),
                "item_value": tf.train.Feature(float_list=tf.train.FloatList(value=value)),
        }))

        item_batch.append(example)
        if len(item_batch) >= max_batch_size:
            print(f"Parsed batch {current_batch}, {stats['items_parsed']:,} items at a rate of {stats['items_parsed']/(time.time()-stats['time_start']):,.0f} items/s")
            with tf.io.TFRecordWriter(f'item_values.{current_batch}.tfrecord', "GZIP") as writer:
                for item in item_batch:
                    writer.write(item.SerializeToString())
            item_batch = []
            current_batch += 1
        if current_batch >= max_batches:
            break