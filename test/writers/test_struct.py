# -*- encoding: utf-8 -*-
# 
# amara.lib.xmlstring
# © 2008, 2009 by Uche Ogbuji and Zepheira LLC
#

import unittest
from cStringIO import StringIO
import amara
from amara.lib import treecompare
from amara.writers.struct import structwriter, structencoder, E, NS, ROOT, RAW, E_CURSOR
#from amara import tree
#from amara import bindery

ATOMENTRY1 = '<?xml version="1.0" encoding="UTF-8"?>\n<entry xmlns=\'http://www.w3.org/2005/Atom\'><id>urn:bogus:x</id><title>boo</title></entry>'

XMLDECL = '<?xml version="1.0" encoding="UTF-8"?>\n'

def test_coroutine_example1():
    EXPECTED = """<a><b attr1="val1"><c>1</c><c>2</c><c>3</c></b></a>"""
    output = structencoder()
    f = output.cofeed(ROOT(E(u'a', E_CURSOR(u'b', {u'attr1': u'val1'}))))
    f.send(E(u'c', u'1'))
    f.send(E(u'c', u'2'))
    f.send(E(u'c', u'3'))
    f.close()
    result = output.read()
    treecompare.check_xml(result, XMLDECL+EXPECTED)
    return

#
def test_coroutine_example2():
    EXPECTED = """<b attr1="val1"><c>1</c><c>2</c><c>3</c></b>"""
    output = structencoder()
    f = output.cofeed(ROOT(E_CURSOR(u'b', {u'attr1': u'val1'})))
    f.send(E(u'c', u'1'))
    f.send(E(u'c', u'2'))
    f.send(E(u'c', u'3'))
    f.close()
    result = output.read()
    treecompare.check_xml(result, XMLDECL+EXPECTED)
    return

#
def test_coroutine_with_nsdecls1():
    EXPECTED = """<a xmlns="urn:bogus:x"><b attr1="val1"><c>1</c><c>2</c><c>3</c></b></a>"""
    XNS = u'urn:bogus:x'
    output = structencoder()
    f = output.cofeed(ROOT(E(u'a', NS(None, XNS), E_CURSOR(u'b', {u'attr1': u'val1'}))))
    f.send(E(u'c', u'1'))
    f.send(E(u'c', u'2'))
    f.send(E(u'c', u'3'))
    f.close()
    result = output.read()
    treecompare.check_xml(result, XMLDECL+EXPECTED)
    return

#
def DISABLEDtest_coroutine_with_nsdecls2():
    #FIXME: Puts out redundant nsdecls for now.  Needs to be fixed in code
    #Trick for skipping tests:
    from nose.plugins.skip import SkipTest
    raise SkipTest('reason')
    EXPECTED = """<a><b attr1="val1"><c>1</c><c>2</c><c>3</c></b></a>"""
    XNS = u'urn:bogus:x'
    output = structencoder()
    f = output.cofeed(ROOT(E(u'a', NS(None, XNS), E_CURSOR((XNS, u'b'), {u'attr1': u'val1'}))))
    f.send(E((XNS, u'c'), u'1'))
    f.send(E((XNS, u'c'), u'2'))
    f.send(E((XNS, u'c'), u'3'))
    f.close()
    result = output.read()
    treecompare.check_xml(result, XMLDECL+EXPECTED)
    return


if __name__ == '__main__':
    raise SystemExit("use nosetests")
