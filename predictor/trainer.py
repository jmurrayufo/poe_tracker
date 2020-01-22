#!/usr/bin/env python3.7

import pymongo
from pprint import pprint
import time
import datetime
import re
import numpy as np
import tensorflow as tf
import pathlib
import logging

from .categories import categories

class Trainer:


    def __init__(self, input_size, output_size, layers, neurons, activation, epochs):
        self.input_size = input_size
        self.output_size = output_size
        self.layers = layers
        self.neurons = neurons
        self.activation = activation
        self.epochs = epochs
        self.log = logging.getLogger("predictor")


    def __call__(self):
        self.log.info("Called")
        for category in categories:
            for subcategory in categories[category]:
                self.train_model(category, subcategory)


    def make_model(
            self,
            layers=2, 
            neurons=64, 
            activation='relu', 
            dropout=None,
    ):
        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Dense(neurons, activation=activation, input_shape=(self.input_size,)))
        if dropout is not None:
            model.add(tf.keras.layers.Dropout(dropout))
        for i in range(layers-1):
            model.add(tf.keras.layers.Dense(neurons, activation=activation,))
            if dropout is not None:
                model.add(tf.keras.layers.Dropout(dropout))
        model.add(tf.keras.layers.Dense(self.output_size, activation='softmax'))

        model.compile(
                optimizer='adam',
                loss='mean_squared_error', 
                metrics=[
                    'accuracy',
                    # 'binary_crossentropy',
                ],
        )
        return model

    @staticmethod
    def parse_record(rr):
        features={"item_properties": tf.io.FixedLenSequenceFeature([], tf.float32, allow_missing=True),
                  "item_value": tf.io.FixedLenSequenceFeature([], tf.float32, allow_missing=True),
                 }
        ex = tf.io.parse_single_example(rr, features)
        return ex['item_properties'], ex['item_value']

    def train_model(self, category, subcategory):
        data_dir = f"data/{category}/{subcategory}/"
        data_dir_path = pathlib.Path(data_dir)
        if not data_dir_path.exists():
            return

        subcategory = "None" if subcategory is None else subcategory
        self.log.info(f"Begin to train on {category}/{subcategory}")
        callbacks = []
        if True:
            # -{datetime.datetime.now().strftime('%dT%H%M')}
            log_dir=f"logs/fit/{category[:5]}-{subcategory[:5]}"
            tensorboard_callback = tf.keras.callbacks.TensorBoard(
                    log_dir=log_dir, 
                    histogram_freq=1,
                    profile_batch=0,
            )
            callbacks.append(tensorboard_callback)

        if True:
            early_stopping = tf.keras.callbacks.EarlyStopping(
                    monitor='val_accuracy',
                    mode='max',
                    patience=50,
                    min_delta=0.001
            )
            callbacks.append(early_stopping)

        # Setup Training DS
        filenames = list(map(str, pathlib.Path(data_dir).glob("train.*.tfrecord")))
        raw_dataset = tf.data.TFRecordDataset(filenames, num_parallel_reads=1)
        raw_dataset = raw_dataset.prefetch(tf.data.experimental.AUTOTUNE)
        # raw_dataset = raw_dataset.cache()
        mapped_data = raw_dataset.map(self.parse_record, num_parallel_calls=tf.data.experimental.AUTOTUNE)
        training_ds = mapped_data.batch(1000)
        # training_ds = mapped_data
        

        # Setup Validation DS
        filenames = list(map(str, pathlib.Path(data_dir).glob("val.*.tfrecord")))
        raw_dataset = tf.data.TFRecordDataset(filenames, num_parallel_reads=1)
        raw_dataset = raw_dataset.prefetch(tf.data.experimental.AUTOTUNE)
        # raw_dataset = raw_dataset.cache()
        mapped_data = raw_dataset.map(self.parse_record, num_parallel_calls=tf.data.experimental.AUTOTUNE)
        validation_ds = mapped_data.batch(1000)
        # validation_ds = mapped_data

        model = self.make_model(dropout=0.25)

        hist = model.fit(
                x=training_ds, 
                epochs=self.epochs, 
                verbose=1,
                callbacks=callbacks,
                validation_data=validation_ds,
        )

        model.save(f"models/{category}/{subcategory}/{self.activation}/{self.layers}x{self.neurons}")

