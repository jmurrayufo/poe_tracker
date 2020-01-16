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


def _float_feature(value):
  return tf.train.Feature(float_list=tf.train.FloatList(value=value))


def serialize_item(f1, f2):
    feature = {
      'feature0': _float_feature(f1),
      'feature1': _float_feature(f2),
    }
    example_proto = tf.train.Example(features=tf.train.Features(feature=feature))
    return example_proto.SerializeToString()


def read_tfrecord(example):
    item_feature_description = {
        'feature0': tf.io.FixedLenFeature([], tf.float32),
        'feature1': tf.io.FixedLenFeature([], tf.float32),
    }
    example = tf.io.parse_single_example(example, item_feature_description)
    return example


n_samples = 50

with tf.io.TFRecordWriter(f'item_values.0.tfrecord') as writer:
    for i in range(n_samples):
        data = np.random.randn(5)
        values = np.random.randn(2)
        example = serialize_item(data, values)
        writer.write(example)

print("Now try to read that @$#@ back!")

filenames = [
    "item_values.0.tfrecord",
]

raw_dataset = tf.data.TFRecordDataset(filenames)

for record in raw_dataset.batch(2):
    print(record)
    for example in record:
        data = tf.train.Example.FromString(example.numpy())
        print(data)
        print(type(data))
print("Finished gen2")