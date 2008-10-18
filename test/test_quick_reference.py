# -*- encoding: utf-8 -*-
# Testing new amara.tree API

# Testing quick reference examples

import unittest
import cStringIO
import amara
from amara.lib import testsupport
from amara import tree, xml_print
from amara import bindery

XML = '<a x="1"><b>i</b><c>j<d/>k</c><b>l</b></a>'
#self.assertEqual(doc[u'a'], doc.xml_select(u'//a')[0])              #object representing a element (instance of a),

class Test_quick_reference(unittest.TestSuite):
    class Test_basic_access(unittest.TestCase):
        def test_basic_access(self):
            doc = amara.parse(XML)
            a = doc.xml_children[0]
            self.assertEqual(doc.xml_type, tree.entity.xml_type)
            #self.assertEqual(len(doc.xml_element_children), 1)
            self.assertEqual(len(doc.xml_children), 1)
            self.assertEqual(a.xml_type, tree.element.xml_type)
            self.assertEqual(doc.xml_element_children[0].xml_local, u'a')
            self.assertEqual(doc.xml_children[0].xml_local, u'a')
            self.assertEqual(a.xml_attributes[u'x'], u"1")
            self.assertEqual(a.xml_local, u'a')
            self.assertEqual(a.xml_qname, u'a')
            self.assertEqual(a.xml_name, (None, u'a'))
            self.assertEqual(len(a.xml_children), 3)
            self.assertEqual(a.xml_parent, doc)
            self.assertEqual(a.xml_attributes.items(), [((None, u'x'), u'1')])

            
    class Test_basic_document_update(unittest.TestCase):
        
        def test_update_domlette(self):
            doc = amara.parse(XML)
            a = doc.xml_children[0]
            #Add a new text node to a (--> last child)
            new_text = amara.tree.text(u'New Content')
            a.xml_append(new_text)
            self.assertEqual(a.xml_children[-1], new_text)
            
            new_text = amara.tree.text(u'New Content')
            a.xml_insert(1, new_text)
            self.assertEqual(a.xml_children[1], new_text)
            
            #Remove the las b child from a
            num_kids = len(a.xml_children)
            e1 = a.xml_select(u"./b")[-1]
            e1.xml_parent.xml_remove(e1)
            self.assertEqual(len(a.xml_children), num_kids-1)
            
            doc.a.xml_clear()  #Remove all children from a

            
    class Test_bindery(unittest.TestCase):
        def test_bindery(self):
            XML = '<a x="1"><b>i</b><c>j<d/>k</c><b>l</b></a>'
            doc = bindery.parse(XML)  # bindery doc
            self.assertEqual(doc[u'a'], doc.xml_select(u'//a')[0])              #object representing a element (instance of a),
            self.assertEqual(doc.a.xml_type, 'element')      #object representing a element (instance of class a),
            self.assertEqual(doc.a.b, doc.xml_select(u'//a/b')[0])               #first instance of b
            self.assertEqual(doc.a.x, u'1')               #u"1"
            self.assertEqual(doc.a[u'x'], u'1')            #u"1"
            self.assertEqual(doc.a.b[0], doc.xml_select(u'//b')[0])           #first instance of b
            self.assertEqual(doc.a.b[1], doc.xml_select(u'//b')[1])            #second instance of b
            self.assertEqual(doc.a[u'b'][1], doc.xml_select(u'//b')[1])         #second instance of b
            #iter(doc.a.b)         #iterator over both instances of b
            self.assertEqual(unicode(doc.a.b), u'i')      #u"i"
            self.assertEqual(unicode(doc.a.b[1]), u'l')   #u"l"
            self.assertEqual(unicode(doc.a), u"ijkl")        #u"ijkl"

    class Test_namespaces(unittest.TestCase):
        def setUp(self):
            self.XML = '<n:a xmlns:n="urn:x-bogus1" n:x="1"><b xmlns="urn:x-bogus2">c</b></n:a>'
            NS1 = u'urn:x-bogus1'
            NS2 = u'urn:x-bogus2'
            self.doc = amara.parse(self.XML)
            return
        
        def test_parsing_namespaces(self):
            #a = self.doc.xml_element_children[0] #element node  ¿?   -->
            #'amara._domlette.Document' object has no attribute 'xml_element_children'
            a = self.doc.xml_children[0] #element node
            self.assertEqual(type(a), tree.element)
            self.assertEqual(a.xml_attributes[(u'urn:x-bogus1', u'x')], u'1')
            self.assertEqual(a.xml_local, u'a')
            self.assertEqual(a.xml_prefix, u'n')
            self.assertEqual(a.xml_qname, u'n:a')
            self.assertEqual(a.xml_name, (u'urn:x-bogus1', u'a'))
            self.assertEqual(a.xml_namespace, u'urn:x-bogus1')
            return
        
    class Test_xpath(unittest.TestCase):
        def test_single_xpath(self):
            doc = amara.parse(XML)
            b_els = doc.xml_select(u"//b")
            self.assertEqual(len(b_els), 2)
            self.assertEqual(doc.xml_select(u"count(//b)"), 2)
            self.assertEqual(doc.xml_select(u"/a/@x")[0].xml_value , u'1')
            self.assertEqual(doc.xml_select(u'string(/a/b)'), u'i')
            return
            
    
if __name__ == '__main__':
    testsupport.test_main()
