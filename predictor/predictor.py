#!/usr/bin/env python

# Pre script setup
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '50' 

import generator
import logging

# Setup Logging
log = logging.getLogger("predictor")
log.setLevel(logging.INFO)
formatter = logging.Formatter('{levelname} {filename}:{funcName}:{lineno} {message}', style='{')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
log.addHandler(ch)

log.info("Logger online")

gen = generator.Generator()
gen()
