

import warnings
warnings.filterwarnings("ignore")
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '50' 
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

import gc

from . import predictions, model_trainer, record_generator

print("Predictor online!")

record_generator.run(max_batch_size=1000, max_batches=100)
model_trainer.run(epochs=1, batch_size=100)
for i in range(100):
    model_trainer.run(epochs=25, batch_size=100, resume="test.model")
    predictions.run(10)
    gc.collect(2)
