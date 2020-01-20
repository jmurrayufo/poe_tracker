"""
import warnings
warnings.filterwarnings("ignore")
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '50' 
# os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import time

import gc
from itertools import product

from . import predictions, model_trainer, record_generator

print("Predictor online!")
# record_generator.run(max_batch_size=1000, max_batches=100)
# record_generator.run(max_batch_size=250*6, max_batches=5)

# exit()

neurons = [128,256,512]
depths = [2,3,4,5,6,7,8]
activates = [
    'relu',
    # 'elu',
    # 'selu',
    # 'sigmoid',
    # 'linear',
    ]
for n,d,a in product(neurons, depths, activates):
    model_trainer.run(epochs=250, batch_size=1000, layers=d, neurons=n, activation=a)
    try:
        pass
    except:
        print("\nCaught exception, sleeping for 5 second then continueing")
        time.sleep(5)
        continue
    predictions.run(20,f"models/{a}/{d}x{n}")
    gc.collect()
"""
