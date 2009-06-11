# -*- encoding: utf-8 -*-
import unittest
from amara.lib import testsupport
from amara.bindery import parse
from amara import tree
from xml.dom import Node
import os
import tempfile

MONTY_XML = """<monty>
  <python spam="eggs">What do you mean "bleh"</python>
  <python ministry="abuse">But I was looking for argument</python>
</monty>"""

SILLY_XML = """<parent>
  <element name="a">A</element>
  <element name="b">B</element>
</parent>"""

SILLY_NS_XML = """<a:parent xmlns:a="urn:bogus:a" xmlns:b="urn:bogus:b">
  <b:sillywrap>
    <a:element name="a">A</a:element>
    <a:element name="b">B</a:element>
  </b:sillywrap>
</a:parent>"""

NS_XML = """<doc xmlns:a="urn:bogus:a" xmlns:b="urn:bogus:b">
  <a:monty/>
  <b:python/>
</doc>"""

SANE_DEFAULT_XML = """<doc xmlns="urn:bogus:a">
  <monty/>
  <python/>
</doc>"""

SANE_DEFAULT_XML_PREFIXES = {u'x': u'urn:bogus:a'}


class Test_sane_default_1(unittest.TestCase):
    """Testing a sane document using default NS"""
    def test_specify_ns(self):
        """Parse with string"""
        doc = parse(SANE_DEFAULT_XML, prefixes=SANE_DEFAULT_XML_PREFIXES)
        #print doc.xml_namespaces
        self.assertEqual(len(list(doc.xml_select(u'//x:monty'))), 1)
        return


if __name__ == '__main__':
    testsupport.test_main()

