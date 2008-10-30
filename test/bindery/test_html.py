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
        """Parse ugly HTML file"""
        f = filesource('nastytagsoup1.html')
        doc = html.parse(f.source)
        self.assertEqual(len(doc.xml_children), 1)
        self.assertEqual(doc.xml_children[0].xml_type, tree.element.xml_type)
        self.assertEqual(doc.xml_children[0].xml_qname, 'html')
        self.assertEqual(doc.xml_children[0].xml_namespace, None)
        self.assertEqual(doc.xml_children[0].xml_prefix, None)
        self.assertEqual(len(list(doc.html.xml_elements)), 2)
        return

class Test_rdfa1(unittest.TestCase):
    """Testing RDFa 1"""
    def test_tagsoup1(self):
        """Test RDFa interpretation from tagsoup"""
        f = filesource('tagsouprdfa1.html')
        doc = html.parse(f.source)
        h = doc.xml_select(u'//h1')[0]
        self.assertEqual(h.property, u'dc:title')
        self.assertEqual(h.xml_attributes[None, u'property'], u'dc:title')
        #print h.xml_namespaces.copy()[u'xml']
        #print h.xml_namespaces.copy()
        self.assertEqual(h.xml_namespaces.copy()[u'xml'], u'http://www.w3.org/XML/1998/namespace')
        self.assertEqual(h.xml_namespaces[u'xml'], u'http://www.w3.org/XML/1998/namespace')
        self.assertEqual(h.xml_namespaces[u'd'], u'http://purl.org/dc/elements/1.1/')
        self.assertEqual(h.xml_namespaces[u'xlink'], u'http://www.w3.org/1999/xlink')
        self.assertEqual(h.xml_namespaces[u'mml'], u'http://www.w3.org/1998/Math/MathML')
        self.assertEqual(h.xml_namespaces[u'xs'], u'http://www.w3.org/2001/XMLSchema')
        self.assertEqual(h.xml_namespaces[u'aml'], u'http://topazproject.org/aml/')
        return

if __name__ == '__main__':
    testsupport.test_main()

