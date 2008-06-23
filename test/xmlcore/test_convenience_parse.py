import unittest
from amara.lib import testsupport
from amara.lib import Parse   ### Revise imports
from amara.Lib import Uri, Uuid
from xml.dom import Node
import os

#More in-depth testing of DOM structure building is done in other tests.
#Just checking the API for now

TEST_STRING = "<test/>"
TEST_FILE = "Xml/Core/disclaimer.xml"

### modify this url
TEST_URL = "http://cvs.4suite.org/viewcvs/*checkout*/4Suite/test/Xml/Core/disclaimer.xml"


class Test_parse_functions_1(unittest.TestCase):
    """Testing local sources"""
    def test_parse_with_string(self):
        """Parse with string"""
        doc = Parse(TEST_STRING)
        #Minimal node testing
        self.assertEqual(len(doc.childNodes), 1)
        self.assertEqual(doc.childNodes[0].nodeType, Node.ELEMENT_NODE)
        self.assertEqual(doc.childNodes[0].nodeName, 'test')
        self.assertEqual(doc.childNodes[0].namespaceURI, None)
        self.assertEqual(doc.childNodes[0].prefix, None,)
        
    def test_parse_with_stream(self):
        """Parse with stream"""
        stream = open(TEST_FILE)
        doc = Parse(stream)
        #Minimal node testing
        self.assertEqual(len(doc.childNodes), 1)
        self.assertEqual(doc.childNodes[0].nodeType, Node.ELEMENT_NODE)
        self.assertEqual(doc.childNodes[0].nodeName, 'disclaimer')
        self.assertEqual(doc.childNodes[0].namespaceURI, None)
        self.assertEqual(doc.childNodes[0].prefix, None,)
    
    def test_parse_with_file_path(self):
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

    def test_parse_with_url(self):
        doc = Parse(TEST_URL)
        #Minimal node testing
        self.assertEqual(len(doc.childNodes), 1)
        self.assertEqual(doc.childNodes[0].nodeType, Node.ELEMENT_NODE)
        self.assertEqual(doc.childNodes[0].nodeName, 'disclaimer')
        self.assertEqual(doc.childNodes[0].namespaceURI, None)
        self.assertEqual(doc.childNodes[0].prefix, None,)

if __name__ == '__main__':
    testsupport.test_main()