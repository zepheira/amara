import unittest
from amara.lib import testsupport

### revise these imports
from amara.lib import Parse, CreateInputSource
from amara.lib.Domlette import Print, EntityReader, GetAllNs, ParseFragment
from amara.lib import Uri, Uuid
from xml.dom import Node
import cStringIO

SOURCE1 = "<p>hello<b>world</b>.  How ya doin'?</p>"

EXPECTED1 = '<p>hello<b>world</b>.  How ya doin\'?</p>'

EXPECTED2 = '<p xmlns="http://www.w3.org/1999/xhtml">hello<b>world</b>.  How ya doin\'?</p>'

SOURCE2 = "<p>hello<b xmlns=''>world</b>.  How ya doin'?</p>"

EXPECTED3 = '<p xmlns="http://www.w3.org/1999/xhtml">hello<b xmlns="">world</b>.  How ya doin\'?</p>'

SOURCE3 = "<h:p xmlns:h='http://www.w3.org/1999/xhtml'>hello<h:b>world</h:b>.  How ya doin'?</h:p>"

EXPECTED4 = '<h:p xmlns:h="http://www.w3.org/1999/xhtml">hello<h:b>world</h:b>.  How ya doin\'?</h:p>'


class Test_fragment_parse(unittest.TestCase):
    """Fragment parse"""
    def test_plain_parse(self):
        """Parse plain text"""
        isrc = CreateInputSource(SOURCE1)
        doc = ParseFragment(isrc)
        stream = cStringIO.StringIO()
        Print(doc, stream)
        self.assertEqual(EXPECTED1, stream.getvalue())
        #Minimal node testing
        self.assertEqual(len(doc.childNodes), 1)
        self.assertEqual(doc.childNodes[0].nodeType, Node.ELEMENT_NODE)
        self.assertEqual(doc.childNodes[0].nodeName, u'p')
        self.assertEqual(doc.childNodes[0].namespaceURI, None)
        self.assertEqual(doc.childNodes[0].prefix, None,)
    
    def test_parse_with_overridden_default_namespace(self):
        """Parse with overridden default namespace"""
        nss = {u'xml': u'http://www.w3.org/XML/1998/namespace',
               None: u'http://www.w3.org/1999/xhtml'}
        isrc = CreateInputSource(SOURCE1)
        doc = ParseFragment(isrc, nss)
        stream = cStringIO.StringIO()
        Print(doc, stream)
        self.assertEqual(EXPECTED2, stream.getvalue())
        #doc = ParseFragment(TEST_STRING)
        #Minimal node testing
        self.assertEqual(len(doc.childNodes), 1)
        self.assertEqual(doc.childNodes[0].nodeType, Node.ELEMENT_NODE)
        self.assertEqual(doc.childNodes[0].nodeName, u'p')
        self.assertEqual(doc.childNodes[0].namespaceURI, u'http://www.w3.org/1999/xhtml')
        self.assertEqual(doc.childNodes[0].prefix, None,)    
        
    def test_parse_overridden_default_namespace_reoverridden_child(self):
        """Parse with overridden default namespace and re-overridden child"""
        nss = {u'xml': u'http://www.w3.org/XML/1998/namespace',
               None: u'http://www.w3.org/1999/xhtml'}
        isrc = CreateInputSource(SOURCE2)
        doc = ParseFragment(isrc, nss)
        stream = cStringIO.StringIO()
        Print(doc, stream)
        self.assertEqual(EXPECTED3, stream.getvalue())
        #Minimal node testing
        self.assertEqual(len(doc.childNodes), 1)
        self.assertEqual(doc.childNodes[0].nodeType, Node.ELEMENT_NODE)
        self.assertEqual(doc.childNodes[0].nodeName, u'p')
        self.assertEqual(doc.childNodes[0].namespaceURI, u'http://www.w3.org/1999/xhtml')
        self.assertEqual(doc.childNodes[0].prefix, None,)    
        
    def test_parse_overridden_non_default_namespace(self):
        """Parse with overridden non-default namespace"""
        nss = {u'xml': u'http://www.w3.org/XML/1998/namespace',
               u'h': u'http://www.w3.org/1999/xhtml'}
        isrc = CreateInputSource(SOURCE3)
        doc = ParseFragment(isrc, nss)
        stream = cStringIO.StringIO()
        Print(doc, stream)
        self.assertEqual(EXPECTED4, stream.getvalue())
        #doc = ParseFragment(TEST_STRING)
        #Minimal node testing
        self.assertEqual(len(doc.childNodes), 1)
        self.assertEqual(doc.childNodes[0].nodeType, Node.ELEMENT_NODE)
        self.assertEqual(doc.childNodes[0].nodeName, u'h:p')
        self.assertEqual(doc.childNodes[0].namespaceURI, u'http://www.w3.org/1999/xhtml')
        self.assertEqual(doc.childNodes[0].prefix, u'h')   
        

if __name__ == '__main__':
    testsupport.test_main()
