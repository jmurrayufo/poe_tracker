#!/usr/bin/env python


from collections import defaultdict
from poe_tracker.code.POE.trade.price import Price
import datetime
import pymongo
import re
import time
from pprint import pprint
import numpy as np
import sys
import tensorflow as tf

# tzinfo.utcoffset
client = pymongo.MongoClient('atlas.lan:27017', 
                    username='poe', 
                    password='poe', 
                    authSource='admin')

m_db = client.path_of_exile_dev

DATA_URL = 'https://storage.googleapis.com/tensorflow/tf-keras-datasets/mnist.npz'

# path = tf.keras.utils.get_file('mnist.npz', DATA_URL)
# with np.load(path) as data:
#   train_examples = data['x_train']
#   train_labels = data['y_train']
#   test_examples = data['x_test']
#   test_labels = data['y_test']

# train_dataset = tf.data.Dataset.from_tensor_slices((train_examples, train_labels))
# test_dataset = tf.data.Dataset.from_tensor_slices((test_examples, test_labels))


train_examples = np.random.rand(500, 6000)
train_labels = np.random.rand(500)
testing_set = np.random.rand(50, 6000)
testing_labels = np.random.rand(50)

train_dataset = tf.data.Dataset.from_tensor_slices((train_examples, train_labels))
test_dataset = tf.data.Dataset.from_tensor_slices((testing_set, testing_labels))

print(train_examples.shape)
print(train_labels.shape)
# exit()


BATCH_SIZE = 64
SHUFFLE_BUFFER_SIZE = 100

train_dataset = train_dataset.shuffle(SHUFFLE_BUFFER_SIZE).batch(BATCH_SIZE)
test_dataset = test_dataset.batch(BATCH_SIZE)

model = tf.keras.Sequential([
    tf.keras.layers.Flatten(input_shape=(6000,)),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dense(10, activation='softmax')
])

model.compile(optimizer=tf.keras.optimizers.RMSprop(),
                loss=tf.keras.losses.SparseCategoricalCrossentropy(),
                metrics=[tf.keras.metrics.SparseCategoricalAccuracy()])

model.fit(train_dataset, epochs=10)

model.evaluate(test_dataset)
