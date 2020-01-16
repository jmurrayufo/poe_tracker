
from nose.tools import *
import time
import unittest
import os
import logging

# from ..code.POE.trade.change_id import ChangeID
from ..code.POE.objects.stash_tab import StashTabSearch
from .helpers import _run

class TestStash(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """TODO: Setup test data for us to pull against
        """
        os.environ['MONGODB_USERNAME'] = 'poe'
        os.environ['MONGODB_PASSWORD'] = 'poe'
        logging.disable(50)

    def setUp(self):
        pass


    def test_iter(self):
        x = StashTabSearch()

        async def call_iter():
            x = StashTabSearch()
            async for i in x.search(limit=50):
                print(i)

        _run(call_iter())
