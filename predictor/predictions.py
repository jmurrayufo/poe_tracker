#!/usr/bin/env python3.7


import pymongo
from pprint import pprint
import time
import datetime
import re
import numpy as np
import tensorflow as tf
import pathlib


def parse_record(rr):
    features={"item_properties": tf.io.FixedLenSequenceFeature([], tf.float32, allow_missing=True),
              "item_value": tf.io.FixedLenSequenceFeature([], tf.float32, allow_missing=True),
             }
    ex = tf.io.parse_single_example(rr, features)
    return ex['item_properties'], ex['item_value']


def run(n_examples=5, model_name="test.model"):

    model = tf.keras.models.load_model(model_name, compile=True)

    filenames = list(map(str, pathlib.Path().glob("item_values.*.tfrecord")))
    raw_dataset = tf.data.TFRecordDataset(filenames, "GZIP")

    mapped_data = raw_dataset.map(parse_record)

    example = list(mapped_data.shuffle(500).take(n_examples))
    example = np.asarray(example)

    examples = np.asarray([x.numpy() for x in example.T[0]])
    answers = np.asarray([x.numpy() for x in example.T[1]]).T[0]

    try:
        prediction = model.predict(examples)
        prediction = np.sum(prediction, axis=1)
        for i in range(n_examples):
            print()
            print(i)
            print(f"Predict: {prediction[i]*100:5.1f}")
            print(f" Listed: {answers[i]*100:5.1f}")
            print(f"  Error: {(prediction[i] - answers[i])*100:5.1f}")
    except Exception as e:
        print(type(e), e)
        raise
