import unittest
import os
from amara import tree, ReaderError
from amara.tree import parse   ### Revise imports
from amara.test import file_finder

FILE = file_finder(__file__)

#More in-depth testing of DOM structure building is done in other tests.
#Just checking the API for now

TEST_STRING = "<test/>"
TEST_FILE = FILE('disclaimer.xml') #test/xmlcore/disclaimer.xml

### modify this url
TEST_URL = "http://hg.4suite.org/amara/trunk/raw-file/tip/test/xmlcore/disclaimer.xml"


class Test_parse_functions_1(unittest.TestCase):
    """Testing local sources"""
    def test_parse_with_string(self):
        """Parse with string"""
        doc = parse(TEST_STRING)
        #Minimal node testing
        self.assertEqual(len(doc.xml_children), 1)
        self.assertEqual(doc.xml_children[0].xml_typecode, tree.element.xml_typecode)
        self.assertEqual(doc.xml_children[0].xml_qname, 'test')
        self.assertEqual(doc.xml_children[0].xml_namespace, None)
        self.assertEqual(doc.xml_children[0].xml_prefix, None,)
        
    def test_parse_with_stream(self):
        """Parse with stream"""
        stream = open(TEST_FILE)
        doc = parse(stream)
        #Minimal node testing
        self.assertEqual(len(doc.xml_children), 1)
        self.assertEqual(doc.xml_children[0].xml_typecode, tree.element.xml_typecode)
        self.assertEqual(doc.xml_children[0].xml_qname, 'disclaimer')
        self.assertEqual(doc.xml_children[0].xml_namespace, None)
        self.assertEqual(doc.xml_children[0].xml_prefix, None,)
    
    def test_parse_with_file_path(self):
        """Parse with file path"""
        doc = parse(TEST_FILE)
        #Minimal node testing
        self.assertEqual(len(doc.xml_children), 1)
        self.assertEqual(doc.xml_children[0].xml_typecode, tree.element.xml_typecode)
        self.assertEqual(doc.xml_children[0].xml_qname, 'disclaimer')
        self.assertEqual(doc.xml_children[0].xml_namespace, None)
        self.assertEqual(doc.xml_children[0].xml_prefix, None,)

    def test_expat_segfault(self):
        "Check malformed input that caused an Expat segfault error."
        try:
            doc = parse("<?xml version\xc2\x85='1.0'?>\r\n")
            self.fail()
        except ReaderError as e:
            self.assertTrue(str(e).endswith(
                    'line 1, column 14: XML declaration not well-formed'))

        import StringIO
        stream = StringIO.StringIO("\0\r\n")
        try:
            doc = parse(stream)
            self.fail()
        except ReaderError as e:
            self.assertTrue(str(e).endswith(
                    'line 2, column 1: no element found'))
        
        

class Test_parse_functions_2(unittest.TestCase):
    """Convenience parse functions, part 2. 
    May be slow; requires Internet connection"""

    def test_parse_with_url(self):
        doc = parse(TEST_URL)
        #Minimal node testing
        self.assertEqual(len(doc.xml_children), 1)
        self.assertEqual(doc.xml_children[0].xml_typecode, tree.element.xml_typecode)
        self.assertEqual(doc.xml_children[0].xml_qname, 'disclaimer')
        self.assertEqual(doc.xml_children[0].xml_namespace, None)
        self.assertEqual(doc.xml_children[0].xml_prefix, None,)

if __name__ == '__main__':
    raise SystemExit("use nosetests")
