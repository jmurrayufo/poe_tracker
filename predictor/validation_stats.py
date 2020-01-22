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
from collections import defaultdict

from .categories import categories

class ValidationStats:

    def __init__(self, layers, neurons, activation):
        self.log = logging.getLogger("predictor")
        self.layers = layers
        self.neurons = neurons
        self.activation = activation


    def __call__(self):
        self.log.info("Called")
        for category in categories:
            for subcategory in categories[category]:
                self.run_validation(category, subcategory)


    @staticmethod
    def parse_record(rr):
        features={"item_properties": tf.io.FixedLenSequenceFeature([], tf.float32, allow_missing=True),
                  "item_value": tf.io.FixedLenSequenceFeature([], tf.float32, allow_missing=True),
                 }
        ex = tf.io.parse_single_example(rr, features)
        return ex['item_properties'], ex['item_value']        


    def run_validation(self, category, subcategory):
        model_name = f"models/{category}/{subcategory}/{self.activation}/{self.layers}x{self.neurons}"
        if not pathlib.Path(model_name).exists():
            # self.log.info("Model path doesn't exist")
            return
        print(f"\n\nValidation of {category}/{subcategory}")
        model = tf.keras.models.load_model(model_name, compile=True)

        data_dir = f"data/{category}/{subcategory}/"

        # Setup Validation DS
        filenames = list(map(str, pathlib.Path(data_dir).glob("val.*.tfrecord")))
        raw_dataset = tf.data.TFRecordDataset(filenames, num_parallel_reads=1)
        raw_dataset = raw_dataset.prefetch(tf.data.experimental.AUTOTUNE)
        # raw_dataset = raw_dataset.cache()
        mapped_data = raw_dataset.map(self.parse_record, num_parallel_calls=tf.data.experimental.AUTOTUNE)
        validation_ds = mapped_data.batch(100)



        np.set_printoptions(precision=2, suppress=True, linewidth=1000)
        errors = defaultdict(lambda: {"count": 0, "total_error": 0, "total_correct":0})
        for examples in validation_ds:
            examples = np.asarray(examples)
            answers = np.asarray([x.numpy() for x in examples.T[:,1]])
            inputs = np.asarray([x.numpy() for x in examples.T[:,0]])
            predictions = model.predict(inputs)
            for idx in range(len(predictions)):
                correct_answer = np.argmax(answers[idx])
                predicted_answer = np.argmax(predictions[idx])
                errors[correct_answer]['count'] += 1
                if correct_answer == predicted_answer:
                    errors[correct_answer]['total_correct'] += 1
                errors[correct_answer]['total_error'] += abs(correct_answer - predicted_answer)
        
        total_count = 0
        total_correct = 0
        total_error = 0
        for bin_value in errors:
            print(f"\nFor Bin Value: {bin_value:2}  ", end='')

            print(f"Count: {errors[bin_value]['count']:6,d}    ", end='')
            print(f"Accuracy: {errors[bin_value]['total_correct']/errors[bin_value]['count']:6.1%}    ", end='')
            print(f"Avg Error: {errors[bin_value]['total_error']/errors[bin_value]['count']:6.3f}", end='')
            total_count += errors[bin_value]['count']
            total_correct += errors[bin_value]['total_correct']
            total_error += errors[bin_value]['total_error']
        print(f"\nTOTALS:")
        print(f"        Count: {total_count}")
        print(f"     Accuracy: {total_correct/total_count:.1%}")
        print(f"    Avg Error: {total_error/total_count:.3f}")



def run(n_examples=5, model_name="test.model"):


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
