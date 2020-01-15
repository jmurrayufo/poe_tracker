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


def run(epochs=10, batch_size=100, resume=None, layers=2, neurons=64, activation='relu'):
    print(f"{activation}/{layers}x{neurons}")
    log_dir=f"logs/fit/{activation}/D:{layers}xN:{neurons}-{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}"
    tensorboard_callback = tf.keras.callbacks.TensorBoard(
        log_dir=log_dir, 
        histogram_freq=1,
        profile_batch=0,
        )

    filenames = list(map(str, pathlib.Path().glob("item_values.*.tfrecord")))
    raw_dataset = tf.data.TFRecordDataset(filenames, "GZIP")
    
    raw_dataset = raw_dataset.prefetch(tf.data.experimental.AUTOTUNE)

    # raw_dataset = raw_dataset.cache()

    mapped_data = raw_dataset.map(parse_record, num_parallel_calls=tf.data.experimental.AUTOTUNE)

    # mapped_data = raw_dataset.map(parse_record)

    validation_ds = mapped_data.take(1000).batch(1000)

    fmnist_train_ds = mapped_data.skip(1000).batch(batch_size)

    if resume:
        print("loading model from memory")
        model = tf.keras.models.load_model(resume, compile=True)
    else:
        model = tf.keras.Sequential()
        for i in range(layers):
            model.add(tf.keras.layers.Dense(neurons, activation=activation))
        model.add(tf.keras.layers.Dense(16, activation='softmax'))

        model.compile(
                optimizer='adam',
                loss='mean_squared_error', 
                metrics=['accuracy'],
        )

    early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_accuracy',
            mode='max',
            patience=150,
            min_delta=0.01
    )

    hist = model.fit(
            x=fmnist_train_ds, 
            epochs=epochs, 
            verbose=1,
            callbacks=[
                tensorboard_callback, 
                early_stopping,
            ],
            validation_data=validation_ds,
    )

    model.save(f"models/{activation}/{layers}x{neurons}")

