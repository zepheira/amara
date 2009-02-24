import unittest
from amara.lib import testsupport
from amara import tree
import os
import tempfile
from functools import *
from itertools import *
from operator import *

from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

from amara import bindery

class Test_doc1(unittest.TestCase):
    """Testing friends document"""
    DOC = '''<?xml version="1.0" encoding="utf-8"?>
<friends>
  <bff rank="1">Suzie Q</bff>
  <bff rank="2">Betty Boost</bff>
</friends>'''

    def test_xpath1(self):
        """Test AVT"""
        doc = bindery.parse(self.DOC)
        self.assertEqual(doc.xml_select(u'friends/bff'), u'Suzie Q')
        self.assertEqual(
            [ unicode(f.xml_select(u'concat(@rank, ": ", .)')) for f in doc.friends.bff ],
            [u'1: Suzie Q', u'2: Betty Boost'])
        return

    def test_avt1(self):
        """Test AVT"""
        doc = bindery.parse(self.DOC)
        self.assertEqual(doc.xml_avt(u'Hello, {friends/bff}'), u'Hello, Suzie Q')
        self.assertEqual(
            [ f.xml_avt(u'Big up, {.}, rank {@rank}') for f in doc.friends.bff ],
            [u'Big up, Suzie Q, rank 1', u'Big up, Betty Boost, rank 2'])
        self.assertEqual(
            [ f.xml_avt(u'{@rank}: {.}') for f in sorted(doc.friends.bff, key=attrgetter("rank")) ],
            [u'1: Suzie Q', u'2: Betty Boost'])
        return


class Test_doc_ns1(unittest.TestCase):
    """Testing friends document with namespaces"""
    PREFIXES = {u'ns': u'urn:bogus:a'}
    DOC = '''<?xml version="1.0" encoding="utf-8"?>
<ns:friends xmlns:ns="urn:bogus:a">
  <ns:bff rank="1">Suzie Q</ns:bff>
  <ns:bff rank="2">Betty Boost</ns:bff>
</ns:friends>'''

    def test_xpath1(self):
        """Test AVT"""
        doc = bindery.parse(self.DOC)
        self.assertEqual(doc.xml_select(u'ns:friends/ns:bff'), u'Suzie Q')
        self.assertEqual(
            [ unicode(f.xml_select(u'concat(@rank, ": ", .)')) for f in doc.friends.bff ],
            [u'1: Suzie Q', u'2: Betty Boost'])
        return

    def test_avt1(self):
        """Test AVT"""
        doc = bindery.parse(self.DOC)
        #FIXME: try to work it so , prefixes= is not needed for this case (declaration in scope)
        self.assertEqual(doc.xml_avt(u'Hello, {ns:friends/ns:bff}', prefixes=self.PREFIXES), u'Hello, Suzie Q')
        self.assertEqual(
            [ f.xml_avt(u'Big up, {.}, rank {@rank}') for f in doc.friends.bff ],
            [u'Big up, Suzie Q, rank 1', u'Big up, Betty Boost, rank 2'])
        self.assertEqual(
            [ f.xml_avt(u'{@rank}: {.}') for f in sorted(doc.friends.bff, key=attrgetter("rank")) ],
            [u'1: Suzie Q', u'2: Betty Boost'])
        return

class Test_doc_ns2(unittest.TestCase):
    """Testing friends document with defaulted namespaces"""
    PREFIXES = {u'ns': u'urn:bogus:a'}
    DOC = '''<?xml version="1.0" encoding="utf-8"?>
<friends xmlns="urn:bogus:a">
  <bff rank="1">Suzie Q</bff>
  <bff rank="2">Betty Boost</bff>
</friends>'''

    def test_xpath1(self):
        """Test AVT"""
        doc = bindery.parse(self.DOC)
        self.assertEqual(doc.xml_select(u'ns:friends/ns:bff', prefixes=self.PREFIXES), u'Suzie Q')
        self.assertEqual(
            [ unicode(f.xml_select(u'concat(@rank, ": ", .)')) for f in doc.friends.bff ],
            [u'1: Suzie Q', u'2: Betty Boost'])
        return

    def test_avt1(self):
        """Test AVT"""
        doc = bindery.parse(self.DOC)
        self.assertEqual(doc.xml_avt(u'Hello, {ns:friends/ns:bff}', prefixes=self.PREFIXES), u'Hello, Suzie Q')
        self.assertEqual(
            [ f.xml_avt(u'Big up, {.}, rank {@rank}') for f in doc.friends.bff ],
            [u'Big up, Suzie Q, rank 1', u'Big up, Betty Boost, rank 2'])
        print repr(attrgetter("rank")(doc.friends.bff))
        self.assertEqual(
            [ f.xml_avt(u'{@rank}: {.}') for f in sorted(doc.friends.bff, key=attrgetter("rank")) ],
            [u'1: Suzie Q', u'2: Betty Boost'])
        return

if __name__ == '__main__':
    testsupport.test_main()

