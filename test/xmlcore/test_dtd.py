# -*- encoding: utf-8 -*-
# 
# © 2008, 2009 by Uche Ogbuji and Zepheira LLC
#

import unittest
from cStringIO import StringIO
from amara import parse
from amara.lib import treecompare
from amara.test import file_finder
#from amara import tree
#from amara import bindery

ATOMENTRY1 = '<?xml version="1.0" encoding="UTF-8"?>\n<entry xmlns=\'http://www.w3.org/2005/Atom\'><id>urn:bogus:x</id><title>boo</title></entry>'

XMLDECL = '<?xml version="1.0" encoding="UTF-8"?>\n'

FILE = file_finder(__file__)

def test_parse_with_dtd():
    TEST_FILE = FILE('4suite.xsa') #test/xmlcore/disclaimer.xml
    #print str(TEST_FILE)
    doc = parse(TEST_FILE, validate=True)
    return

#

if __name__ == '__main__':
    raise SystemExit("use nosetests")
