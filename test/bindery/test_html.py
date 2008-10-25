import unittest
from amara.lib import testsupport
from amara.bindery import html
from amara import tree
from xml.dom import Node
import os
import tempfile

from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class Test_parse_nasty_tagsoup1(unittest.TestCase):
    """Testing nasty tag soup 1"""
    def test_parse_file(self):
        """Parse with string"""
        #Minimal node testing
        f = filesource('nastytagsoup1.html')
        doc = html.parse(f.source)
        self.assertEqual(len(doc.xml_children), 1)
        self.assertEqual(doc.xml_children[0].xml_type, tree.element.xml_type)
        self.assertEqual(doc.xml_children[0].xml_qname, 'html')
        self.assertEqual(doc.xml_children[0].xml_namespace, None)
        self.assertEqual(doc.xml_children[0].xml_prefix, None)
        self.assertEqual(len(list(doc.html.xml_elements)), 2)
        return

if __name__ == '__main__':
    testsupport.test_main()

