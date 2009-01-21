#Test garbage collection


# Translating old Amara/test/bindery/gc.py
# lm

# Resources:
#   http://www.skymind.com/~ocrow/python_string/
#   http://code.activestate.com/recipes/286222/

import unittest
import os
import gc
from cStringIO import StringIO
import commands, os
import itertools
from amara.lib import testsupport

import amara

#from Ft.Xml import InputSource
#from Ft.Lib import Uri

SCALE = 1000
PID = os.getpid()
PS_COMMAND = 'ps up '


class TestPushbindLoopPatterns(unittest.TestCase):
    def setUp(self):
        self.bigdoc1 = ["<A>"]
        self.bigdoc1.extend(["<B/>"]*(SCALE*100))
        self.bigdoc1.extend(["</A>"])
        self.bigdoc1 = ''.join(self.bigdoc1)
        #len(self.bigdoc1) is 400007 for SCALE = 1000
        self.doc = amara.parse(self.bigdoc1)
        gc.enable()
        return

    def testPushbindGC(self):
        #Use a simplistic trend watcher to make sure that memory
        #Usage is not growing unreasonably
        #Cum is a measure of the cumulative growth trend in GC profile
        cum = 0.0
        elems = iter(self.doc.xml_select(u'//B'))  # Makes nodeset iterable
        init_gc = gc.collect()
        #print init_gc
        e = elems.next()
        iter1_gc = gc.collect()
        #print iter1_gc
        for i in xrange(100):
            e = elems.next()
            iter_gc = gc.collect()
            #print iter_gc
            try:
                increase = iter_gc - old_iter_gc
                #Uncomment the following lines for more info
                #if increase > 0:
                #    print "Increase ", increase, "(cumulative)", cum
                cum += increase
            except NameError:
                pass
            old_iter_gc = iter_gc
            self.assert_(cum/SCALE < 0.01)
        return

    def testPushbindSystemMem(self):
        try:
            int(commands.getoutput(PS_COMMAND + `PID`).split()[15])
        except:
            #Test won't work on this platform
            #FIXME: improve/broaden the test
            pass
        prev_size = start_size = ps_stat()
        #elems = amara.pushbind(self.bigdoc1, u"B")
        runs = 100
        for i in xrange(runs):
            doc = amara.parse('<title>title</title>')
            value = unicode(iter(doc.xml_select(u'//title')).next())
            #Parse('<title>title</title>')
            gc.collect()
            size = ps_stat()
            growth = (size - prev_size)*100.0/size
            self.assert_(growth < 2.5, 'Greater than 2.5%% virtual memory size growth detected after one run (%i%%)'%growth)
            prev_size = size
        growth = (size - start_size)*100.0/size
        self.assert_(growth < 10, 'Greater than 10%% virtual memory size growth detected over %i runs (%i%%)'%(runs, growth))
        return


    def testParseSystemMem(self):
        try:
            int(commands.getoutput(PS_COMMAND + `PID`).split()[15])
        except:
            #Test won't work on this platform
            #FIXME: improve/broaden the test
            pass
        prev_size = start_size = ps_stat()
        #elems = amara.pushbind(self.bigdoc1, u"B")
        runs = 100
        for i in xrange(runs):
            amara.parse('<title>title</title>')
            gc.collect()
            size = ps_stat()
            growth = (size - prev_size)*100.0/size
            self.assert_(growth < 2.5, 'Greater than 2.5%% virtual memory size growth detected after one run (%i%%)'%growth)
            prev_size = size
        growth = (size - start_size)*100.0/size
        self.assert_(growth < 10, 'Greater than 10%% virtual memory size growth detected over %i runs (%i%%)'%(runs, growth))
        return


def ps_stat():
    ps = commands.getoutput(PS_COMMAND + `PID`)
    process_size = int(ps.split()[15])
    #process_size = ps.split()[15]
    return process_size


if __name__ == '__main__':
    testsupport.test_main()

