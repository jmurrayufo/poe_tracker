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
import logging
import shutil

# Local imports
from .bins import Bins
from .categories import categories


class Generator:

    re_pat = re.compile(r"-?\d+(?:.\d+)?")

    def __init__(
            self, 
            max_batch_size=500,
            max_batches=5,
            val_ratio=0.05,
            bin_slots=16,
            bin_max_edge=1000,
            bin_slot_cap=None
    ):
        self.log = logging.getLogger("predictor")

        self.max_batch_size = max_batch_size
        self.max_batches = max_batches
        self.val_ratio = val_ratio
        client = pymongo.MongoClient('atlas.lan:27017', username='poe', password='poe', authSource='admin')
        self.db = client.path_of_exile_dev
        self.bin_slots = bin_slots
        self.bin_max_edge = bin_max_edge
        self.bin_slot_cap = bin_slot_cap

        self.array_size = 0
        for mod in self.db.items.mods.find():
            self.array_size += max(1, mod['numbers'])
        self.log.info(f"Array sizes set to {self.array_size}")


    def __call__(self):
        self.log.info("Called")

        self.log.info("Purge old data")
        try:
            shutil.rmtree("data")
        except FileNotFoundError:
            pass


        self.log.info("Setup scanning categories")
        self.stats = {}
        for category in categories:
            self.stats[category] = {}
            for subcategory in categories[category]:
                self.stats[category][subcategory] = {
                        "batches":0,
                        "train_items":0,
                        "train_batch": 0,
                        "val_items":0,
                        "val_batch": 0,
                }

        for category in categories:
            for subcategory in categories[category]:
                self.scan(category, subcategory)


    def scan(self, category, subcategory):
        self.log.info(f"Called scan with {category} and {subcategory}")
        data_dir = f"data/{category}/{subcategory}/"

        # Make sure we have a place to write these!
        pathlib.Path(data_dir).mkdir(parents=True, exist_ok=True)

        _filter = {
            "extended.category":category,
            "extended.subcategories":subcategory,
            # "frameType":2,
            "league":"Metamorph", # TODO: Handle this with input arguments
        }
        # self.log.info(_filter)

        item_batch = []


        bins = Bins(
                edges=self.bin_slots, 
                max_edge=self.bin_max_edge,
                bin_cap=self.bin_slot_cap
        )

        # Status tracking
        items_parsed = 0
        t_last_start = time.time()
        t_last_update = time.time()

        # Init fresh lists for use in the writing functions
        self.val_list = []
        self.train_list = []

        for item in self.db.items.sold.find(_filter):
            items_parsed += 1

            # Check to see if item has value we can even understand
            item_value = self.convert_value(item['_value'], item['_value_name'])
            if item_value is None: 
                print(f"Skip {item['_value']},{item['_value_name']}")
                time.sleep(1)
                continue
            # Ignore joke values
            if item_value > 100_000:
                continue

            bins.insert(item_value, item)
            items_parsed += 1

            # If 2/3rds of our bins are full, write um
            if np.count_nonzero(np.asarray(bins.shape)==self.bin_slot_cap) > 2/3*self.bin_slots:
                self.process_batch(bins, data_dir, self.stats[category][subcategory])
                bins.clear()
                # t_last_start = time.time()
                if self.stats[category][subcategory]['train_batch']+1 > self.max_batches:
                    break
            if time.time() - t_last_update > 10:
                t_last_update = time.time()
                self.log.info(f"Found {items_parsed:,d} ({items_parsed/(time.time()-t_last_start):,.0f} items/s)")
        self.flush_lists(data_dir, self.stats[category][subcategory], 0)
        self.log.info(f"Found {items_parsed:,d} ({items_parsed/(time.time()-t_last_start):,.0f} items/s)")


    def convert_value(self, value, value_name):
        if value_name == "Chaos Orb":
            return value
        cache_dict = self.db.items.price.cache.find_one({"typeLine":value_name, "league":"Metamorph"})
        if cache_dict is None:
            return None
        return cache_dict['_value'] * value


    def set_values(self, np_array, mod, _type):
        matches = self.re_pat.findall(mod)
        (mod_r, numbers) = self.re_pat.subn(r"{}",mod)

        result = self.db.items.mods.find_one({"name":mod_r,"type":_type,})

        if result is None:
            return
        if result['numbers']:
            for idx, num in enumerate(matches):
                normalize_value = result['norm'][str(idx)]
                np_array[result['index'] + idx] = float(num) / normalize_value
        else:
            np_array[result['index']] = 1.0


    def process_batch(self, bins, data_dir, stats_dict):
        """                  
            "batches":0,
            "train_items":0,
            "val_items":0,
        """
        for idx in range(len(bins)):
            for item in bins[idx]:
                # Set label of value
                value = np.zeros(self.bin_slots, dtype=np.float32)
                value[idx] = 1

                data = np.zeros(self.array_size, dtype=np.float32)
                try:
                    if "explicitMods" in item:
                        for mod in item['explicitMods']:
                            self.set_values(data, mod, "explicit")

                    if "implicitMods" in item:
                        for mod in item['implicitMods']:
                            self.set_values(data, mod, "implicit")

                    if "craftedMods" in item:
                        for mod in item['craftedMods']:
                            self.set_values(data, mod, "craft")

                    if "enchantMods" in item:
                        for mod in item['enchantMods']:
                            self.set_values(data, mod, "exhant")
                except ZeroDivisionError:
                    continue

                """Additional data:
                [
                    ilvl/100
                    prefixes/3
                    sufixes/3,
                    quality/100
                    required_level/100
                    required_int/500
                    required_dex/500
                    required_str/500
                ]
                """
                add_data = np.zeros(8, dtype=np.float32)
                # data = np.concatenate((data, add_data))

                example = tf.train.Example(features=tf.train.Features(feature={
                        "item_properties": tf.train.Feature(float_list=tf.train.FloatList(value=data)),
                        "item_value": tf.train.Feature(float_list=tf.train.FloatList(value=value)),
                }))

                if np.random.rand() < self.val_ratio:
                    self.val_list.append(example)
                    stats_dict['val_items'] += 1
                else:
                    self.train_list.append(example)
                    stats_dict['train_items'] += 1

                self.flush_lists(data_dir, stats_dict, self.max_batch_size-1)


    def flush_lists(self, data_dir, stats_dict, min_lengh):
        if len(self.train_list) > min_lengh:
            self.write_records_to_disk(f"{data_dir}/train.{stats_dict['train_batch']}.tfrecord", self.train_list)
            stats_dict['train_batch'] += 1
            self.train_list = []
        if len(self.val_list) > min_lengh:
            self.write_records_to_disk(f"{data_dir}/val.{stats_dict['val_batch']}.tfrecord", self.val_list)
            stats_dict['val_batch'] += 1
            self.val_list = []


    def write_records_to_disk(self, file_name, records):
        with tf.io.TFRecordWriter(file_name) as writer:
            for example in records:
                writer.write(example.SerializeToString())
