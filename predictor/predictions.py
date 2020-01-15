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

    filenames = list(map(str, pathlib.Path().glob("data/item_values.*.tfrecord")))
    raw_dataset = tf.data.TFRecordDataset(filenames)

    mapped_data = raw_dataset.map(parse_record)

    example = list(mapped_data.shuffle(500).take(n_examples))
    example = np.asarray(example)

    examples = np.asarray([x.numpy() for x in example.T[0]])
    answers = np.asarray([x.numpy() for x in example.T[1]])

    np.set_printoptions(precision=2, suppress=True, linewidth=1000)
    try:
        prediction = model.predict(examples)
        # prediction = np.sum(prediction, axis=1)
        for i in range(n_examples):
            print()
            print(i)
            p_argmax = np.argmax(prediction[i])
            a_argmax = np.argmax(answers[i])
            # print(f"Predict: {prediction[i]}")
            # print(f" Listed: {answers[i]}")
            combo = [prediction[i], answers[i]]
            #print(f"Combo: \n{np.asarray(combo)}")
            print(f"P: {p_argmax} ({prediction[i][np.argmax(prediction[i])]:.0%})")
            print(f"A: {a_argmax}")
            print(f"E: {abs(a_argmax-p_argmax)}")
            # print(f"  Error: {(prediction[i] - answers[i])}")
    except Exception as e:
        print(type(e), e)
        raise
