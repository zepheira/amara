import unittest
from amara.lib import testsupport
from amara.dom import parse
from xml.dom import Node
from amara import tree
import os
import tempfile

MONTY_XML = """<monty>
  <python spam="eggs">What do you mean "bleh"</python>
  <python ministry="abuse">But I was looking for argument</python>
</monty>"""

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
        self.assertEqual(len(doc.documentElement.xml_children), 2)
        self.assertEqual(doc.xml_children[0].xml_children[0].xml_type, tree.element.xml_type)
        self.assertEqual(doc.xml_children[0].xml_children[0].xml_qname, u'python')
        self.assertEqual(doc.xml_children[0].xml_children[0].xml_namespace, None)
        self.assertEqual(doc.xml_children[0].xml_children[0].xml_prefix, None)
        self.assertEqual(len(list(doc.getElementsByTagNameNS(None, u'python'))), 2)
        self.assertEqual(';'.join([ e.xml_qname for e in doc.getElementsByTagNameNS(None, u'python') ]), u'python;python')
        
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
