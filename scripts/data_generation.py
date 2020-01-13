#!/usr/bin/env python3.7

# STFU tensor flow!
# import warnings
# warnings.filterwarnings("ignore")
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '50' 

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

import pymongo
from pprint import pprint
import time
import datetime
import re
import numpy as np
import tensorflow as tf
import pathlib

def set_values(np_array, mod, _type):
    matches = re_pat.findall(mod)
    (mod_r, numbers) = re_pat.subn(r"{}",mod)

    result = db.items.mods.find_one({"name":mod_r,"type":_type,})

    if result is None:
        return
    if result['numbers']:
        for idx, num in enumerate(matches):
            np_array[result['index'] + idx] = float(num)
    else:
        np_array[result['index']] = 1.0

client = pymongo.MongoClient('atlas.lan:27017', username='poe', password='poe', authSource='admin')
db = client.path_of_exile_dev

re_pat = re.compile(r"-?\d+(?:.\d+)?")

array_size = 0
for mod in db.items.mods.find():
    array_size += max(1, mod['numbers'])

print(array_size)

_filter = {
    "extended.category":"armour",
    "frameType":2,
    "extended.subcategories":"boots",
    "_value":{"$lt": 100}
}

max_batch_size = 500
max_batches = 5
item_batch = []
current_batch = 0

# Cleanup old files
files = pathlib.Path().glob("item_values.*.tfrecord")
for f in files:
    f.unlink()

for item in db.items.sold.find(_filter):

    data = np.zeros(array_size, dtype=np.float32)
    value = np.asarray([item['_value']/100.0], dtype=np.float32)

    if "explicitMods" in item:
        for mod in item['explicitMods']:
            set_values(data, mod, "explicit")

    if "implicitMods" in item:
        for mod in item['implicitMods']:
            set_values(data, mod, "implicit")

    if "craftedMods" in item:
        for mod in item['craftedMods']:
            set_values(data, mod, "craft")

    if "enchantMods" in item:
        for mod in item['enchantMods']:
            set_values(data, mod, "exhant")

    # data = data[data>0]

    example = tf.train.Example(features=tf.train.Features(feature={
            "item_properties": tf.train.Feature(float_list=tf.train.FloatList(value=data)),
            "item_value": tf.train.Feature(float_list=tf.train.FloatList(value=value)),
    }))

    item_batch.append(example)
    if len(item_batch) >= max_batch_size:
        print(current_batch)
        with tf.io.TFRecordWriter(f'item_values.{current_batch}.tfrecord', "GZIP") as writer:
            for item in item_batch:
                writer.write(item.SerializeToString())
        item_batch = []
        current_batch += 1
    if current_batch >= max_batches:
        break

print("Now try to read that @$#@ back!")

def parse_item(imagerecord):
    return imagerecord.features.feature['item_properties'].float_list.value, \
           imagerecord.features.feature['item_value'].float_list.value

def parse_record(rr):
    features={"item_properties": tf.io.FixedLenSequenceFeature([], tf.float32, allow_missing=True),
              "item_value": tf.io.FixedLenSequenceFeature([], tf.float32, allow_missing=True),
             }
    ex = tf.io.parse_single_example(rr, features)
    return ex['item_properties'], ex['item_value']


filenames = list(map(str, pathlib.Path().glob("item_values.*.tfrecord")))
raw_dataset = tf.data.TFRecordDataset(filenames, "GZIP")

mapped_data = raw_dataset.map(parse_record)

fmnist_train_ds = mapped_data
fmnist_train_ds = fmnist_train_ds.shuffle(500).batch(500)

model = tf.keras.Sequential([
  tf.keras.layers.Flatten(),
  tf.keras.layers.Dense(10, activation='softmax'),
])

model.compile(optimizer='adam',
              loss='mean_squared_error', 
              metrics=['accuracy'])
model.fit(fmnist_train_ds, epochs=10)


loss, accuracy = model.evaluate(fmnist_train_ds)
print()
print("Loss :", loss)
print("Accuracy :", accuracy)

example = next(iter(mapped_data.shuffle(50).take(1)))

print("\n\n\n")
x = np.asarray([example[0].numpy()])
print(example[1][0].numpy())
print("\n")
try:
    prediction = model.predict(x)
    print(prediction[0][0])
except Exception as e:
    print(type(e), e)

model.save("test.model")