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

def run(epochs=10, batch_size=100, resume=None):

    filenames = list(map(str, pathlib.Path().glob("item_values.*.tfrecord")))
    raw_dataset = tf.data.TFRecordDataset(filenames, "GZIP")

    mapped_data = raw_dataset.map(parse_record)

    fmnist_train_ds = mapped_data
    fmnist_train_ds = fmnist_train_ds.shuffle(batch_size).batch(batch_size)

    if resume:
        print("loading model from memory")
        model = tf.keras.models.load_model(resume, compile=True)
    else:
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(1),
        ])

        model.compile(
                optimizer='adam',
                loss='mean_squared_error', 
                metrics=['accuracy'],
        )
    hist = model.fit(
            x=fmnist_train_ds, 
            epochs=epochs, 
            verbose=1
    )
    
    print(hist.history)
    model.save("test.model")


    # loss, accuracy = model.evaluate(fmnist_train_ds)
    # print()
    # print("Loss :", loss)
    # print("Accuracy :", accuracy)