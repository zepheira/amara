# Testing new amara.tree API

# Based on Amara1.x Tests mutation.py


import unittest
import cStringIO
import amara
from amara import tree, xml_print, bindery
from xml.dom import Node


XMLDECL = '<?xml version="1.0" encoding="UTF-8"?>\n'
output = cStringIO.StringIO()


class TestBasicMods(unittest.TestCase):
    #def setUp(self):
    #    return

    def compare_output(self, doc, expected):
        """
        Auxiliar method for testing output puposes
        """
        output = cStringIO.StringIO()        
        xml_print(doc, stream=output)
        return self.assertEqual(output.getvalue(), expected)
        
    def test_basic_tree_create_doc1(self):
        EXPECTED = "<A/>"
        doc = bindery.nodes.entity_base()
        A = doc.xml_element_factory(None, u'A')
        doc.xml_append(A)
        self.assertEqual(len(doc.xml_select(u'//A')), 1)
        self.assertEqual(len(doc.xml_children[0]), 1)
        self.assertEqual(len(doc.xml_children[0].xml_children), 0)
        self.assertEqual(len(doc.A.xml_children), 0)
        self.compare_output(doc, XMLDECL+EXPECTED)
        
        #self.assert_(isinstance(doc.xbel.title, unicode))
        #self.assertRaises(AttributeError, binding.xbel.folder.)
        return

    def test_basic_tree_create_doc2(self):
        EXPECTED = '<A xmlns:ns="urn:bogus" ns:a="b"/>'
        doc = bindery.nodes.entity_base()
        A = doc.xml_element_factory(None, u'A')
        doc.xml_append(A)
        doc.A.xmlns_attributes[u'ns']= u'urn:bogus'
        doc.A.xml_attributes[u'ns:a'] = u'b'

        self.assertEqual(len(list(doc.A)), 1)
        self.assertEqual(len(doc.A.xml_children), 0)
        self.compare_output(doc, XMLDECL+EXPECTED)
        
        #self.assert_(isinstance(doc.xbel.title, unicode))
        #self.assertRaises(AttributeError, binding.xbel.folder.)
        return
        
    def test_basic_tree_create_doc3(self):
        EXPECTED = '<A a="b"/>'
        #Namespace-free attr creation, abbreviated
        doc = bindery.nodes.entity_base()
        A = doc.xml_element_factory(None, u'A')
        doc.xml_append(A)
        doc.A.xml_attributes[u'a'] = u'b'
        
        self.assertEqual(len(list(doc.A)), 1)
        self.assertEqual(len(doc.A.xml_children), 0)
        self.compare_output(doc, XMLDECL+EXPECTED)
        
        #Namespace-free attr creation, full
        #self.assert_(isinstance(doc.xbel.title, unicode))
        #self.assertRaises(AttributeError, binding.xbel.folder.)
        return

    def test_basic_tree_create_doc4(self):
        doc = bindery.nodes.entity_base()
        A = doc.xml_element_factory(None, u'A')
        doc.xml_append(A)
        B = doc.xml_element_factory(None, u'B')
        doc.A.xml_append(B)
        doc.A.B.xmlns_attributes[u'ns']= u'urn:bogus'
        doc.A.B.xml_attributes[u'ns:a'] = u'b'
        doc.A.B.xml_append(doc.xml_text_factory(u"One"))
        
        #doc.A.B.xmlns_attributes[u'ns']= u'urn:bogus'  ??
        #doc.A.b.xml_attributes[u'ns:a'] = u'b'

        self.assertEqual(len(list(doc.A)), 1)
        self.assertEqual(len(doc.A.xml_children), 1)
        EXPECTED = '<A><B xmlns:ns="urn:bogus" ns:a="b">One</B></A>'
        
        self.compare_output(doc, XMLDECL+EXPECTED)
        #self.assert_(isinstance(doc.xbel.title, unicode))
        #self.assertRaises(AttributeError, binding.xbel.folder.)
        return

    def test_basic_create_doc4(self):
        EXPECTED = '<A><B a="b">One</B></A>'
        #Namespace-free attr creation, abbreviated
        doc = bindery.nodes.entity_base()
        A = doc.xml_element_factory(None, u'A')
        doc.xml_append(A)
        B = doc.xml_element_factory(None, u'B')
        doc.A.xml_append(B)
        doc.A.B.xml_attributes[u'a'] = u'b'
        doc.A.B.xml_append(doc.xml_text_factory(u"One"))
        
        self.assertEqual(len(list(doc.A)), 1)
        self.assertEqual(len(doc.A.xml_children), 1)
        self.compare_output(doc, XMLDECL+EXPECTED)
       
        return

    def test_basic_create_doc5(self):
        EXPECTED = '<A a="b"/>'
        doc = bindery.nodes.entity_base()
        A = doc.xml_element_factory(None, u'A')
        doc.xml_append(A)
        doc.A.xml_attributes[u'a'] = u"b"
        self.assertEqual(len(list(doc.A)), 1)
        self.assertEqual(len(doc.A.xml_children), 0)
        self.compare_output(doc, XMLDECL+EXPECTED)
        
        #self.assert_(isinstance(doc.xbel.title, unicode))
        #self.assertRaises(AttributeError, binding.xbel.folder.)
        return

    def test_basic_create_doc6(self):
        EXPECTED = '<A xmlns:ns="urn:bogus" ns:a="b"/>'
        doc = bindery.nodes.entity_base()
        A = doc.xml_element_factory(None, u'A')
        doc.xml_append(A)
        doc.A.xmlns_attributes[u'ns']= u'urn:bogus'
        doc.A.xml_attributes[u'ns:a'] = u'b'
        self.assertEqual(len(list(doc.A)), 1)
        self.assertEqual(len(doc.A.xml_children), 0)
        self.compare_output(doc, XMLDECL+EXPECTED)
        #self.assert_(isinstance(doc.xbel.title, unicode))
        #self.assertRaises(AttributeError, binding.xbel.folder.)
        return

    #def testCreateDoc2(self):
        #from amara.writers import outputparameters, xmlwriter
        
        #doc = bindery.nodes.entity_base()
        #A = doc.xml_element_factory(None, u'A')
        #doc.xml_append(A)
        #doc.A.xml_append(doc.xml_element_factory(None, u'A'))
        #doc.A.A.xml_append(doc.xml_text_factory(u"One"))
        #doc.A.xml_append(doc.xml_element_factory(None, u'B'))
        #doc.A.B.xml_append(doc.xml_text_factory(u"Two"))
        #self.assertEqual(len(list(doc.A)), 1)
        #self.assertEqual(len(list(doc.A.A)), 1)
        #self.assertEqual(len(list(doc.A.B)), 1)
        #self.assertEqual(unicode(doc.A.A), u"One")
        #self.assertEqual(unicode(doc.A.B), u"Two")
        #EXPECTED = "<A><A>One</A><B>Two</B></A>"
        #self.compare_output(doc, XMLDECL+EXPECTED)
        #EXPECTED = "<A>\n  <A>One</A>\n  <B>Two</B>\n</A>"
        #op = outputparameters.outputparameters()
        #op.indent = u"yes"
        #stream = cStringIO.StringIO()
        #w = xmlwriter.xmlwriter(op, stream)
        #doc.xml(writer=w)
        #self.assertEqual(stream.getvalue(), XMLDECL+EXPECTED)
        ###PrettyPrint(doc)
        ##self.assert_(isinstance(doc.xbel.title, unicode))
        ##self.assertRaises(AttributeError, binding.xbel.folder.)
        #return

    def testCreateDocNs1(self):
        EXPECTED = '<A xmlns="urn:bogus"/>'
        doc = bindery.nodes.entity_base()
        A = doc.xml_element_factory(u'urn:bogus', u'A')
        doc.xml_append(A)
        self.assertEqual(len(list(doc.A)), 1)
        self.assertEqual(len(doc.A.xml_children), 0)
        self.compare_output(doc, XMLDECL+EXPECTED)
        #self.assert_(isinstance(doc.xbel.title, unicode))
        #self.assertRaises(AttributeError, binding.xbel.folder.)
        return

    def testTemplate1(self):
        EXPECTED = '<A><B a="b">One</B></A>'
        doc = bindery.nodes.entity_base()
        A = doc.xml_element_factory(None, u'A')
        doc.xml_append(A)
        doc.A.xml_append_fragment('<B a="b">One</B>')
        self.assertEqual(len(list(doc.A)), 1)
        self.assertEqual(len(doc.A.xml_children), 1)
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testTemplate2(self):
        EXPECTED = '<A><B xmlns:ns="urn:bogus" ns:a="b">One</B></A>'
        doc = bindery.nodes.entity_base()
        A = doc.xml_element_factory(None, u'A')
        doc.xml_append(A)
        doc.A.xml_append_fragment('<B xmlns:ns="urn:bogus" ns:a="b">One</B>')
        self.assertEqual(len(list(doc.A)), 1)
        self.assertEqual(len(doc.A.xml_children), 1)
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testTemplate3(self):
        EXPECTED = '<A xmlns:ns="urn:bogus" ns:a="b"><B>One</B></A>'
        doc = bindery.nodes.entity_base()
        A = doc.xml_element_factory(None, u'A')
        doc.xml_append(A)
        doc.A.xmlns_attributes[u'ns']= u'urn:bogus'
        doc.A.xml_attributes[u'ns:a'] = u'b'
        doc.A.xml_append_fragment('<B>One</B>')
        self.assertEqual(len(list(doc.A)), 1)
        self.assertEqual(len(doc.A.xml_children), 1)
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testTemplate4(self):
        EXPECTED = '<A><B xmlns:ns="urn:bogus" ns:a="b">One</B></A>'
        doc = bindery.nodes.entity_base()
        A = doc.xml_element_factory(None, u'A')
        doc.xml_append(A)
        doc.A.xml_append(bindery.parse('<B xmlns:ns="urn:bogus" ns:a="b">One</B>').xml_children[0])
        self.assertEqual(len(list(doc.A)), 1)
        self.assertEqual(len(doc.A.xml_children), 1)
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testTemplate5(self):
        EXPECTED = u'<A><B>\u2203</B></A>'.encode('utf-8')
        doc = bindery.nodes.entity_base()
        A = doc.xml_element_factory(None, u'A')
        doc.xml_append(A)
        doc.A.xml_append(bindery.parse(u'<B>\u2203</B>'.encode('utf-8')).xml_children[0])
        self.assertEqual(len(list(doc.A)), 1)
        self.assertEqual(len(doc.A.xml_children), 1)
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testTemplate6(self):
        EXPECTED = u'<A><B>\u00AB\u00BB</B></A>'.encode('utf-8')
        doc = bindery.nodes.entity_base()
        A = doc.xml_element_factory(None, u'A')
        doc.xml_append(A)
        doc.A.xml_append_fragment(u'<B>\u00AB\u00BB</B>'.encode('utf-8'))
        self.assertEqual(len(list(doc.A)), 1)
        self.assertEqual(len(doc.A.xml_children), 1)
        self.compare_output(doc, XMLDECL+EXPECTED)
        return


    def testCreateDocType1(self):
        EXPECTED = '<!DOCTYPE xsa PUBLIC "-//LM Garshol//DTD XML Software Autoupdate 1.0//EN//XML" "http://www.garshol.priv.no/download/xsa/xsa.dtd">\n<xsa/>'
        doc = bindery.nodes.entity_base()
        doc.xml_system_id = u"http://www.garshol.priv.no/download/xsa/xsa.dtd"
        doc.xml_public_id = u"-//LM Garshol//DTD XML Software Autoupdate 1.0//EN//XML"
        doc.xml_append(doc.xml_element_factory(None, u'xsa'))
        self.assertEqual(len(list(doc.xsa)), 1)
        self.assertEqual(len(doc.xsa.xml_children), 0)
        self.compare_output(doc, XMLDECL+EXPECTED)
        #PrettyPrint(doc)
        #self.assert_(isinstance(doc.xbel.title, unicode))
        #self.assertRaises(AttributeError, binding.xbel.folder.)
        return

    #def testCreateDocType2(self):  ???
        #EXPECTED = '<!DOCTYPE xsa PUBLIC "-//LM Garshol//DTD XML Software Autoupdate 1.0//EN//XML" "http://www.garshol.priv.no/download/xsa/xsa.dtd">\n<xsa/>'
        #doc = bindery.nodes.entity_base()
        #doc.xml_system_id = u"http://www.garshol.priv.no/download/xsa/xsa.dtd"
        #doc.xml_public_id = u"-//LM Garshol//DTD XML Software Autoupdate 1.0//EN//XML"
        ## ???
        ##doc = amara.create_document(
            ##u"xsa",
            ##pubid=u"-//LM Garshol//DTD XML Software Autoupdate 1.0//EN//XML",
            ##sysid=u"http://www.garshol.priv.no/download/xsa/xsa.dtd"
            ##)
        #doc.xml_append(doc.xml_element_factory(None, u'xsa'))
        
        #self.assertEqual(len(list(doc.xsa)), 1)
        #self.assertEqual(len(doc.xsa.xml_children), 0)
        #self.compare_output(doc, XMLDECL+EXPECTED)
        ## ??? self.assertEqual(doc.xml(indent=u'yes'), XMLDECL+EXPECTED)
        ##PrettyPrint(doc)
        ##self.assert_(isinstance(doc.xbel.title, unicode))
        ##self.assertRaises(AttributeError, binding.xbel.folder.)
        #return

    #def testCreateDocType4(self):
        #EXPECTED = '<!DOCTYPE xsa PUBLIC "-//LM Garshol//DTD XML Software Autoupdate 1.0//EN//XML" "http://www.garshol.priv.no/download/xsa/xsa.dtd">\n<xsa/>'
        #op = OutputParameters()
        #op.indent = u'yes'
        #op.doctypeSystem = u"http://www.garshol.priv.no/download/xsa/xsa.dtd"
        #op.doctypePublic = u"-//LM Garshol//DTD XML Software Autoupdate 1.0//EN//XML"
        #stream = cStringIO.StringIO()
        #w = XmlWriter(op, stream)
        #doc = amara.create_document(u"xsa")
        #self.assertEqual(len(list(doc.xsa)), 1)
        #self.assertEqual(len(doc.xsa.xml_children), 0)
        #doc.xml(writer=w)
        #self.compare_output(doc,  XMLDECL+EXPECTED)
        
        ##PrettyPrint(doc)
        ##self.assert_(isinstance(doc.xbel.title, unicode))
        ##self.assertRaises(AttributeError, binding.xbel.folder.)
        #return

    def testReplace(self):
        EXPECTED = '<A><B id="1">One</B><B id="2">Two</B></A>'
        DOC = EXPECTED
        doc = bindery.parse(DOC)
        del doc.A.B[1]
        e2 = doc.xml_element_factory(None, u'B')
        e2.xml_attributes[u'id'] = u"2"
        e2.xml_append(doc.xml_text_factory(u'Two'))
        doc.A.xml_append(e2)
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testRepeatEdits1(self):
        EXPECTED = '<A><B a="b">One</B></A>'
        doc = bindery.nodes.entity_base()
        doc.xml_append(doc.xml_element_factory(None, u'A'))
        e1 = doc.xml_element_factory(None, u'B')
        e1.xml_attributes[u'a'] = u"b"
        e1.xml_append(doc.xml_text_factory(u'One'))
        doc.A.xml_append(e1)
        self.assertEqual(len(list(doc.A)), 1)
        self.assertEqual(len(doc.A.xml_children), 1)
        self.compare_output(doc,  XMLDECL+EXPECTED)
        return

    def testSetChildElement1(self):
        DOC = "<a><b>spam</b></a>"
        EXPECTED = '<a><b>eggs</b></a>'
        doc = bindery.parse(DOC)
        doc.a.b = u"eggs"
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testSetChildElement2(self):
        DOC = "<a><b>spam</b></a>"
        EXPECTED = '<a><b>eggs</b></a>'
        doc = bindery.parse(DOC)
        doc.a.b[0] = u"eggs"
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testSetChildElement3(self):
        DOC = "<a><b>spam</b><b>spam</b></a>"
        EXPECTED = '<a><b>eggs</b><b>spam</b></a>'
        doc = bindery.parse(DOC)
        doc.a.b = u"eggs"
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testSetChildElement4(self):
        DOC = "<a><b>spam</b><b>spam</b></a>"
        EXPECTED = '<a><b>eggs</b><b>spam</b></a>'
        doc = bindery.parse(DOC)
        doc.a.b[0] = u"eggs"
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testSetChildElement5(self):
        DOC = "<a><b>spam</b><b>spam</b></a>"
        EXPECTED = '<a><b>spam</b><b>eggs</b></a>'
        doc = bindery.parse(DOC)
        doc.a.b[1] = u"eggs"
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testSetChildElement6(self):
        DOC = "<a><b>spam</b><b>spam</b></a>"
        doc = bindery.parse(DOC)
        def edit():
            doc.a.b[2] = u"eggs"
        self.assertRaises(IndexError, edit)
        return

    def testDelChildElement1(self):
        DOC = "<a><b>spam</b><b>eggs</b></a>"
        EXPECTED = '<a><b>eggs</b></a>'
        doc = bindery.parse(DOC)
        del doc.a.b
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testDelChildElement2(self):
        DOC = "<a><b>spam</b><b>eggs</b></a>"
        EXPECTED = '<a><b>eggs</b></a>'
        doc = bindery.parse(DOC)
        del doc.a.b[0]
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testDelChildElement3(self):
        DOC = "<a><b>spam</b><b>eggs</b></a>"
        EXPECTED = '<a><b>spam</b></a>'
        doc = bindery.parse(DOC)
        del doc.a.b[1]
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testDelChildElement4(self):
        DOC = "<a><b>spam</b><b>spam</b></a>"
        doc = bindery.parse(DOC)
        def edit():
            del doc.a.b[2]
        self.assertRaises(IndexError, edit)
        return

    def testDelChildElement5(self):
        DOC = "<a><b>spam</b><b>eggs</b></a>"
        EXPECTED = '<a><b>eggs</b></a>'
        doc = bindery.parse(DOC)
        del doc.a[u'b']
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testDelChildElement6(self):
        DOC = "<a><b>spam</b><b>eggs</b></a>"
        EXPECTED = '<a><b>eggs</b></a>'
        doc = bindery.parse(DOC)
        del doc.a[u'b'][0]
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testDelChildElement7(self):
        DOC = "<a><b>spam</b><b>eggs</b></a>"
        EXPECTED = '<a><b>spam</b></a>'
        doc = bindery.parse(DOC)
        del doc.a[u'b'][1]
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    #def testDelChildElementWithClash1(self):
        #DOC = '<a-1 b-1=""><b-1/></a-1>'
        #EXPECTED = '<a-1 b-1=""/>'
        #doc = bindery.parse(DOC)
        #E = Node.ELEMENT_NODE
        #del doc[E, None, u'a-1'][E, None, u'b-1']
        #self.compare_output(doc, XMLDECL+EXPECTED)
        #return

    #def testDelAttributeWithClash1(self):
        #DOC = '<a-1 b-1=""><b-1/></a-1>'
        #EXPECTED = '<a-1><b-1/></a-1>'
        #doc = bindery.parse(DOC)
        #E = Node.ELEMENT_NODE
        #A = Node.ATTRIBUTE_NODE
        #del doc[E, None, u'a-1'][A, None, u'b-1']
        #self.compare_output(doc, XMLDECL+EXPECTED)
        #return

    def testDelAttribute1(self):
        DOC = '<a b="spam"><b>spam</b></a>'
        EXPECTED = '<a><b>spam</b></a>'
        doc = bindery.parse(DOC)
        del doc.a.b
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testSetAttribute1(self):
        DOC = '<a b="spam"></a>'
        EXPECTED = '<a b="eggs"/>'
        doc = bindery.parse(DOC)
        doc.a.xml_attributes[u'b'] = u"eggs"
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testSetAttribute2(self):
        DOC = '<a b="spam"><b>spam</b></a>'
        EXPECTED = '<a b="eggs"><b>spam</b></a>'
        doc = bindery.parse(DOC)
        doc.a.xml_attributes[u'b'] = u"eggs"
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testSetAttribute3(self):
        from xml.dom import Node
        DOC = '<a b="spam"><b>spam</b></a>'
        EXPECTED = '<a b="eggs"><b>spam</b></a>'
        doc = bindery.parse(DOC)
        doc.a[Node.ATTRIBUTE_NODE, None, u'b'] = u'eggs'
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testSetAttribute4(self):
        DOC = '<a><b>spam</b></a>'
        EXPECTED = '<a><b xml:lang="en">spam</b></a>'
        doc = bindery.parse(DOC)
        # doc.a.b.xml_set_attribute((u"xml:lang"), u"en")
        doc.a.b.xml_attributes[u'xml:lang'] = u'en'
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testSetAttribute5(self):
        DOC = '<a><b>spam</b></a>'
        EXPECTED = '<a xmlns:ns="urn:bogus" ns:foo="bar"><b>spam</b></a>'
        doc = bindery.parse(DOC)
        doc.a.xmlns_attributes[u'ns']= u'urn:bogus'
        doc.a.xml_attributes[u'ns:foo'] = u'bar'
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    #def testSetAttribute6(self):
        #### Do we need this test now ?
        #DOC = '<a><b>spam</b></a>'
        #EXPECTED = '<a xmlns:ns="urn:bogus" ns:foo="bar"><b>spam</b></a>'
        #doc = amara.parse(DOC, prefixes={u'ns': u'urn:bogus'})
        #doc.a.xml_set_attribute((u"foo", u"urn:bogus"), u"bar")
        #self.compare_output(doc, XMLDECL+EXPECTED)
        #return

    def testSetAttribute7(self):
        DOC = '<a><b>spam</b></a>'
        EXPECTED = '<a foo="bar"><b>spam</b></a>'
        doc = bindery.parse(DOC)
        doc.a.xml_attributes[u"foo"] = u"bar"
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testInsertAfter1(self):
        DOC = "<a><b>spam</b></a>"
        EXPECTED = '<a><b>spam</b><b>eggs</b></a>'
        doc = bindery.parse(DOC)
        new = doc.xml_element_factory(None, u'b')
        new.xml_append(doc.xml_text_factory(u'eggs'))
        doc.a.xml_insert(1, new)
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testInsertAfter2(self):
        DOC = "<a><b>spam</b></a>"
        EXPECTED = '<a><b>spam</b><c>eggs</c></a>'
        doc = bindery.parse(DOC)
        new = doc.xml_element_factory(None, u'c')
        new.xml_append(doc.xml_text_factory(u'eggs'))
        doc.a.xml_insert(doc.a.xml_index(doc.a.b)+1, new)
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testInsertAfter3(self):
        DOC = "<a><b>spam</b><c>ham</c><c>pork</c></a>"
        EXPECTED = "<a><b>spam</b><c>eggs</c><c>ham</c><c>pork</c></a>"
        doc = bindery.parse(DOC)
        new = doc.xml_element_factory(None, u'c')
        new.xml_append(doc.xml_text_factory(u'eggs'))
        doc.a.xml_insert(doc.a.xml_index(doc.a.b) +1, new)
        self.compare_output(doc, XMLDECL+EXPECTED)
        return

    def testInsertBefore1(self):
        DOC = "<a><b>eggs</b></a>"
        EXPECTED = '<a><b>spam</b><b>eggs</b></a>'
        doc = bindery.parse(DOC)
        new = doc.xml_element_factory(None, u'b')
        new.xml_append(doc.xml_text_factory(u'spam'))
        doc.a.xml_insert(0, new)
        self.compare_output(doc, XMLDECL+EXPECTED)
        return


MONTY = """\
<?xml version="1.0" encoding="utf-8"?>
<monty>
  <python spam="eggs">
    What do you mean "bleh"
  </python>
  <python ministry="abuse">
    But I was looking for argument
  </python>
</monty>
"""


class TestTransforms(unittest.TestCase):
    def compare_output(self, doc, expected):
        """
        Auxiliar method for testing output puposes
        """
        output = cStringIO.StringIO()        
        xml_print(doc, stream=output)
        return self.assertEqual(output.getvalue(), expected)

    def test_deep_copy_entity(self):
        #FIXME really goes in manual.py, since it's based on a manual example
        EXPECTED1 = '<python spam="eggs">\n    What do you mean "bleh"\n  </python>'
        EXPECTED2 = '<python spam="abcd">\n    What do you mean "bleh"\n  </python>'
        import copy
        doc = bindery.parse(MONTY)
        doc2 = copy.deepcopy(doc)
        doc2.monty.python.xml_attributes[u'spam'] = u"abcd"
        self.compare_output(doc.monty.python, EXPECTED1)
        self.compare_output(doc2.monty.python, EXPECTED2)
        return

    def test_deep_copy_element(self):
        #FIXME really goes in manual.py, since it's based on a manual example
        EXPECTED1 = '<python spam="eggs">\n    What do you mean "bleh"\n  </python>'
        EXPECTED2 = '<python spam="abcd">\n    What do you mean "bleh"\n  </python>'
        import copy
        doc = bindery.parse(MONTY)
        doc2 = bindery.nodes.entity_base()
        root_elem = copy.deepcopy(doc.xml_first_child)
        doc2.xml_append(root_elem)
        doc2.monty.python.xml_attributes[u'spam'] = u"abcd"
        self.compare_output(doc.monty.python, EXPECTED1)
        self.compare_output(doc2.monty.python, EXPECTED2)
        return


if __name__ == '__main__':
    unittest.main()

