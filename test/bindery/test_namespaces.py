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
    
    def test_attr_assignment(self):
        doc = parse(SANE_DEFAULT_XML, prefixes=SANE_DEFAULT_XML_PREFIXES)
        monty = doc.doc.monty

        # Create attribute node 
        attr_node = tree.attribute(u'urn:bogus:a', 'setitem', 'value')
        monty[u'urn:bogus:a', 'setitem'] = attr_node
        self.assertEqual(monty.xml_attributes[(u'urn:bogus:a', u'setitem')], 
                         'value')

        # Check for mismatched namespace
        attr_node = tree.attribute(u'urn:bogus:a', 'setitem2', 'value')
        def f():
            monty[u'urn:wrong-value', 'setitem2'] = attr_node
        self.assertRaises(ValueError, f)

        # Check for mismatched local name
        def f():
            monty[u'urn:bogus:a', 'setitem'] = attr_node
        self.assertRaises(ValueError, f)

        # Test with no namespace supplied on node.
        attr_node = tree.attribute(None, 'setitem3', 'value')
        monty[u'urn:bogus:a', 'setitem3'] = attr_node
        self.assertEqual(monty.xml_attributes[(u'urn:bogus:a', u'setitem3')], 
                         'value')

        # Test with no namespace supplied in key.
        attr_node = tree.attribute(u'urn:bogus:a', 'setitem4', 'value')
        monty[None, 'setitem4'] = attr_node
        self.assertEqual(monty.xml_attributes[(u'urn:bogus:a', u'setitem4')], 
                         'value')

        # Test with no namespace supplied at all.
        attr_node = tree.attribute(None, 'setitem5', 'value')
        monty[None, 'setitem5'] = attr_node
        self.assertEqual(monty.xml_attributes[(u'urn:bogus:a', u'setitem5')], 
                         'value')

if __name__ == '__main__':
    testsupport.test_main()

