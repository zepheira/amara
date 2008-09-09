import unittest
from amara.lib import testsupport
from amara.bindery import parse
from xml.dom import Node
import os

MONTY_XML = """<monty>
  <python spam="eggs">What do you mean "bleh"</python>
  <python ministry="abuse">But I was looking for argument</python>
</monty>"""

NS_XML = """<doc xmlns:a="urn:bogus:a" xmlns:b="urn:bogus:b">
  <a:monty/>
</doc>"""

#TEST_FILE = "Xml/Core/disclaimer.xml"

### modify this url
TEST_URL = "http://cvs.4suite.org/viewcvs/*checkout*/4Suite/test/Xml/Core/disclaimer.xml"


class Test_parse_functions_1(unittest.TestCase):
    """Testing local sources"""
    def test_parse_with_string(self):
        """Parse with string"""
        doc = parse(MONTY_XML)
        print doc
        print doc.xml_children[0]
        print doc.xml_children[0].xml_qname
        print doc.monty
        print dir(doc.xml_children[0])
        #Minimal node testing
        self.assertEqual(len(doc.xml_children), 1)
        self.assertEqual(doc.xml_children[0].xml_node_type, Node.ELEMENT_NODE)
        self.assertEqual(doc.xml_children[0].xml_qname, 'monty')
        self.assertEqual(doc.xml_children[0].xml_namespace, None)
        self.assertEqual(doc.xml_children[0].xml_prefix, None,)
        
    def Xtest_parse_with_stream(self):
        """Parse with stream"""
        stream = open(TEST_FILE)
        doc = Parse(stream)
        #Minimal node testing
        self.assertEqual(len(doc.childNodes), 1)
        self.assertEqual(doc.childNodes[0].nodeType, Node.ELEMENT_NODE)
        self.assertEqual(doc.childNodes[0].nodeName, 'disclaimer')
        self.assertEqual(doc.childNodes[0].namespaceURI, None)
        self.assertEqual(doc.childNodes[0].prefix, None,)
    
    def Xtest_parse_with_file_path(self):
        """Parse with file path"""
        doc = Parse(TEST_FILE)
        #Minimal node testing
        self.assertEqual(len(doc.childNodes), 1)
        self.assertEqual(doc.childNodes[0].nodeType, Node.ELEMENT_NODE)
        self.assertEqual(doc.childNodes[0].nodeName, 'disclaimer')
        self.assertEqual(doc.childNodes[0].namespaceURI, None)
        self.assertEqual(doc.childNodes[0].prefix, None,)
        

class Test_parse_functions_2(unittest.TestCase):
    """Convenience parse functions, part 2. 
    May be slow; requires Internet connection"""

    def Xtest_parse_with_url(self):
        doc = parse(TEST_URL)
        #Minimal node testing
        self.assertEqual(len(doc.childNodes), 1)
        self.assertEqual(doc.childNodes[0].nodeType, Node.ELEMENT_NODE)
        self.assertEqual(doc.childNodes[0].nodeName, 'disclaimer')
        self.assertEqual(doc.childNodes[0].namespaceURI, None)
        self.assertEqual(doc.childNodes[0].prefix, None,)

if __name__ == '__main__':
    testsupport.test_main()
