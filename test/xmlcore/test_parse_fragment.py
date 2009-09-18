import unittest

### revise these imports
from amara import tree
from amara.lib import inputsource
from amara.tree import parse_fragment
from xml.dom import Node

SOURCE1 = "<p>hello<b>world</b>.  How ya doin'?</p>"

DECL = '<?xml version="1.0" encoding="UTF-8"?>\n'

EXPECTED1 = DECL + '<p>hello<b>world</b>.  How ya doin\'?</p>'

EXPECTED2 = DECL + '<p xmlns="http://www.w3.org/1999/xhtml">hello<b>world</b>.  How ya doin\'?</p>'

SOURCE2 = "<p>hello<b xmlns=''>world</b>.  How ya doin'?</p>"

EXPECTED3 = DECL + '<p xmlns="http://www.w3.org/1999/xhtml">hello<b xmlns="">world</b>.  How ya doin\'?</p>'

SOURCE3 = "<h:p xmlns:h='http://www.w3.org/1999/xhtml'>hello<h:b>world</h:b>.  How ya doin'?</h:p>"

EXPECTED4 = DECL + '<h:p xmlns:h="http://www.w3.org/1999/xhtml">hello<h:b>world</h:b>.  How ya doin\'?</h:p>'


class Test_fragment_parse(unittest.TestCase):
    """Fragment parse"""
    def test_plain_parse(self):
        """Parse plain text"""
        isrc = inputsource(SOURCE1)
        doc = parse_fragment(isrc)
        self.assertEqual(EXPECTED1, doc.xml_encode())
        #Minimal node testing
        self.assertEqual(len(doc.xml_children), 1)
        first_child = doc.xml_children[0]
        self.assertEqual(first_child.xml_typecode, tree.element.xml_typecode)
        self.assertEqual(first_child.xml_qname, u'p')
        self.assertEqual(first_child.xml_namespace, None)
        self.assertEqual(first_child.xml_prefix, None,)
    
    def test_parse_with_overridden_default_namespace(self):
        """Parse with overridden default namespace"""
        nss = {u'xml': u'http://www.w3.org/XML/1998/namespace',
               None: u'http://www.w3.org/1999/xhtml'}
        isrc = inputsource(SOURCE1)
        doc = parse_fragment(isrc, nss)
        self.assertEqual(EXPECTED2, doc.xml_encode())
        #doc = parse_fragment(TEST_STRING)
        #Minimal node testing
        self.assertEqual(len(doc.xml_children), 1)
        first_child = doc.xml_children[0]
        self.assertEqual(first_child.xml_typecode, tree.element.xml_typecode)
        self.assertEqual(first_child.xml_qname, u'p')
        self.assertEqual(first_child.xml_namespace, u'http://www.w3.org/1999/xhtml')
        self.assertEqual(first_child.xml_prefix, None,)    
    
    def test_parse_overridden_default_namespace_reoverridden_child(self):
        """Parse with overridden default namespace and re-overridden child"""
        nss = {u'xml': u'http://www.w3.org/XML/1998/namespace',
               None: u'http://www.w3.org/1999/xhtml'}
        isrc = inputsource(SOURCE2)
        doc = parse_fragment(isrc, nss)
        self.assertEqual(EXPECTED3, doc.xml_encode())
        #Minimal node testing
        self.assertEqual(len(doc.xml_children), 1)
        first_child = doc.xml_children[0]
        self.assertEqual(first_child.xml_typecode, tree.element.xml_typecode)
        self.assertEqual(first_child.xml_qname, u'p')
        self.assertEqual(first_child.xml_namespace, u'http://www.w3.org/1999/xhtml')
        self.assertEqual(first_child.xml_prefix, None,)    
    
    def test_parse_overridden_non_default_namespace(self):
        """Parse with overridden non-default namespace"""
        nss = {u'xml': u'http://www.w3.org/XML/1998/namespace',
               u'h': u'http://www.w3.org/1999/xhtml'}
        isrc = inputsource(SOURCE3)
        doc = parse_fragment(isrc, nss)
        self.assertEqual(EXPECTED4, doc.xml_encode())
        #doc = parse_fragment(TEST_STRING)
        #Minimal node testing
        self.assertEqual(len(doc.xml_children), 1)
        first_child = doc.xml_children[0]
        self.assertEqual(first_child.xml_typecode, tree.element.xml_typecode)
        self.assertEqual(first_child.xml_qname, u'h:p')
        self.assertEqual(first_child.xml_namespace, u'http://www.w3.org/1999/xhtml')
        self.assertEqual(first_child.xml_prefix, u'h')   
        

if __name__ == '__main__':
    raise SystemExit("use nosetests")
