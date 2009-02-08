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

#TEST_FILE = "Xml/Core/disclaimer.xml"

### modify this url
TEST_URL = "http://cvs.4suite.org/viewcvs/*checkout*/4Suite/test/Xml/Core/disclaimer.xml"


class Test_parse_functions_1(unittest.TestCase):
    """Testing local sources"""
    def run_checks(self, doc):
        """Parse with string"""
        #Minimal node testing
        self.assertEqual(len(doc.xml_children), 1)
        self.assertEqual(doc.xml_children[0].xml_type, tree.element.xml_type)
        self.assertEqual(doc.xml_children[0].xml_qname, 'monty')
        self.assertEqual(doc.xml_children[0].xml_namespace, None)
        self.assertEqual(doc.xml_children[0].xml_prefix, None)
        self.assertEqual(len(doc.monty.xml_children), 5)
        self.assertEqual(doc.monty.xml_children[0].xml_type, tree.text.xml_type)
        self.assertEqual(doc.monty.xml_children[1].xml_type, tree.element.xml_type)
        self.assertEqual(doc.monty.xml_children[1].xml_qname, 'python')
        self.assertEqual(doc.monty.xml_children[1].xml_namespace, None)
        self.assertEqual(doc.monty.xml_children[1].xml_prefix, None)
        self.assertEqual(len(doc.monty.python), 2)
        self.assertEqual(doc.monty.python[1].xml_qname, 'python')
        self.assertEqual(';'.join([ e.xml_qname for e in doc.monty.python ]), u'python;python')
        
    def test_parse_with_string(self):
        """Parse with string"""
        doc = parse(MONTY_XML)
        self.run_checks(doc)

    def test_parse_with_stream(self):
        """Parse with stream"""
        fname = tempfile.mktemp('.xml')
        fout = open(fname, 'w')
        fout.write(MONTY_XML)
        fout.close()
        fout = open(fname, 'r')
        doc = parse(fout)
        fout.close()
        self.run_checks(doc)
    
    def test_parse_with_file_path(self):
        """Parse with file path"""
        fname = tempfile.mktemp('.xml')
        fout = open(fname, 'w')
        fout.write(MONTY_XML)
        fout.close()
        doc = parse(fname)
        self.run_checks(doc)

    def test_attribute_series(self):
        """Iterate over attributes with the same name on elements with the same name"""
        doc = parse(SILLY_XML)
        self.assertEqual(';'.join([ e.name for e in doc.parent.element ]), u'a;b')
        
    def test_attribute_series(self):
        """Iterate over attributes with the same name on elements with the same name"""
        doc = parse(SILLY_NS_XML)
        self.assertEqual(';'.join([ e.name for e in doc.parent.sillywrap.element ]), u'a;b')
        

class Test_parse_functions_2(unittest.TestCase):
    """Convenience parse functions, part 2. 
    May be slow; requires Internet connection"""

    def Xtest_parse_with_url(self):
        doc = parse(TEST_URL)
        #Minimal node testing
        self.assertEqual(len(doc.xml_children), 1)
        self.assertEqual(doc.xml_children[0].xml_type, tree.element.xml_type)
        self.assertEqual(doc.xml_children[0].xml_qname, 'disclaimer')
        self.assertEqual(doc.xml_children[0].xml_namespace, None)
        self.assertEqual(doc.xml_children[0].xml_prefix, None,)

if __name__ == '__main__':
    testsupport.test_main()
