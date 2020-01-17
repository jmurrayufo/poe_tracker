from nose.tools import *
import time
import unittest

from ..code.POE.trade.change_id import ChangeID

class TestChangeID(unittest.TestCase):

    def test_args(self):
        ChangeID()
        ChangeID("1-2-3-4-5")
        ChangeID(1,2,3,4,5.0)
        ChangeID([1,2,3,4,5.0])
        ChangeID((1,2,3,4,5.0))
        ChangeID("1.2-2-3-4-5")
        ChangeID("1e12-1-1-1-1")
        x = ChangeID(1,2,3,4,5)
        y = ChangeID(x)
        assert_equal(x,y)
        assert_is_not(x,y)

        # Must give legal values
        with assert_raises(ValueError):
            ChangeID("frog-1-1-1-1")

    def test_compare(self):
        x = ChangeID(1,2,3,4,5)
        y = ChangeID(2,4,6,8,10)
        assert_equal(x,x)
        assert_not_equal(x,y)
        assert_less(x,y)
        assert_greater(y,x)
        assert_greater(y,1)
        assert_less(x,6)

    def test_math(self):
        x = ChangeID(1,2,3,4,5)
        y = ChangeID(2,4,6,8,10)

        assert_equal(x*2,y)
        assert_equal(x+2, ChangeID(3,4,5,6,7))
        assert_equal(x**2, ChangeID(1,2**2,3**2,4**2,5**2))

    def test_strings(self):
        x = ChangeID(1,2,3,4,5)
        assert_equal(str(x),"1-2-3-4-5")

    @unittest.skip("Don't bother with ninja testing most of the time")
    def test_poe_ninja(self):
        x = ChangeID(1,2,3,4,5)
        y = ChangeID(x)

        x.sync_poe_ninja()
        assert_not_equal(x,y)

        #time.sleep(10)
        #y.sync_poe_ninja()
        #assert_not_equal(x,y)

    def test_get_set(self):
        x = ChangeID()
        x[0] = 9
        x[1] = 9
        x[2] = 9
        x[3] = 9
        x[4] = 9
        assert_equal(x, ChangeID(9,9,9,9,9))
        with assert_raises(IndexError):
            x[5]

        
