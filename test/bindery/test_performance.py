#Test bindery performance

# Resources:
#   http://www.skymind.com/~ocrow/python_string/
#   http://code.activestate.com/recipes/286222/
#   http://www.oreillynet.com/onlamp/blog/2007/09/pymotw_timeit.html

import sys
import unittest
import gc
import os
from cStringIO import StringIO
import commands, os
import itertools

from timeit import Timer

from amara.lib import testsupport

import amara
from amara import bindery

from nose.plugins.skip import SkipTest

SCALE = 100
TIMER_COUNT = 100

class Test_increment_over_core_tree(unittest.TestCase):
    '''Warning. SLOW TEST'''
    def setUp(self):
        raise SkipTest("Too slow and will make for a good deal of thrashing")
        self.bigdoc1 = ["<A>"]
        self.bigdoc1.extend(["<B/>"]*SCALE)
        self.bigdoc1.extend(["</A>"])
        self.bigdoc1 = ''.join(self.bigdoc1)
        #len(self.bigdoc1) is 4007 for SCALE = 1000
        self.doc = amara.parse(self.bigdoc1)
        t0 = Timer('amara.parse(doc)', 'import amara; doc = %r'%(self.bigdoc1))
        #self.base_tree_time = min(t0.repeat(3))
        self.base_tree_time = t0.timeit(TIMER_COUNT)
        #print >> sys.stderr, self.base_tree_time
        gc.disable()
        t0 = Timer('amara.parse(doc)', 'import amara; doc = %r'%(self.bigdoc1))
        #self.base_tree_time = min(t0.repeat(3))
        self.base_tree_time_no_gc = t0.timeit(TIMER_COUNT)
        print >> sys.stderr, self.base_tree_time_no_gc
        gc.enable()
        gc.collect()

    def test_bindery_parse(self):
        #self.assert_(diff/SCALE < 0.01)
        t1 = Timer('bindery.parse(doc)', 'from amara import bindery; doc = %r'%(self.bigdoc1))
        #t = min(t1.repeat(3))
        t = t1.timeit(TIMER_COUNT)
        #print >> sys.stderr, 'test_bindery_parse', t, (t - self.base_tree_time)/self.base_tree_time
        #self.assert_(diff/SCALE < 0.01)
        self.assert_(t < 5)

    def test_bindery_parse_gcdisabled(self):
        #self.assert_(diff/SCALE < 0.01)
        t1 = Timer('gc.disable(); bindery.parse(doc); gc.enable(); gc.collect()', 'from amara import bindery; doc = %r'%(self.bigdoc1))
        #t = min(t1.repeat(3))
        t = t1.timeit(TIMER_COUNT)
        #print >> sys.stderr, 'test_bindery_parse_gcdisabled', t, (t - self.base_tree_time_no_gc)/self.base_tree_time_no_gc
        #self.assert_(diff/SCALE < 0.01)
        self.assert_(t < 20)


if __name__ == '__main__':
    raise SystemExit("Use nosetests")

