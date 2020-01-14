
from nose.tools import *
import time
import unittest
import os
import logging

# from ..code.POE.trade.change_id import ChangeID
import numpy as np

class TestStash(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """TODO: Setup test data for us to pull against
        """
        cls.m = 2

    def test_outliers(self):
        data = [[1,2007],[1,22]]
        data = np.asarray(data)
        data = np.asarray(data)
        print("Before:",data)
        print("Before:",data[:,0])
        data = self.reject_outliers(data)
        print("\nAfter:",data)
        print(data.shape)
        assert data.shape == (2,2)

        print("\nData1")
        data = [
            [1,2],
            [1,5],
            [50,5],
        ]
        data = np.asarray(data)
        print("Before:",data)
        print("Before:",data[:,0])
        data = self.reject_outliers(data)
        print("\nAfter:",data)
        print(data.shape)
        assert data.shape == (2,2)


    def test_weighted_percentile(self):
        x = np.array([1,2,3,4,5,6,7,8,9,10])
        w = np.array([1,1,1,1,1,1,1,1,1,10000])
        print(self.weighted_percentile(x, 25, w))
        assert False

    def reject_outliers(self, data):
        d = np.abs(data[:,0] - np.median(data[:,0]))
        mdev = np.mean(d)
        s = d/mdev if mdev else 0.
        ret_val = data[s<self.m]
        if ret_val.ndim > 2:
            return ret_val[0]
        else:
            return ret_val

    @staticmethod
    def weighted_percentile(data, percents, weights=None):
        ''' percents in units of 1%
            weights specifies the frequency (count) of data.
        '''
        if weights is None:
            return np.percentile(data, percents)
        ind=np.argsort(data)
        d=data[ind]
        w=weights[ind]
        p=1.*w.cumsum()/w.sum()*100
        y=np.interp(percents, p, d)
        return y