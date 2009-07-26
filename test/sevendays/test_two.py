import unittest
import cStringIO

import amara
from amara import tree, xml_print, bindery, dom


class TestTree(unittest.TestCase):
    def setUp(self):
        self.MONTY_XML = """<monty>
<python spam="eggs">What do you mean "bleh"</python>
<python ministry="abuse">But I was looking for argument</python>
</monty>"""
        self.lines_py = [u'<python spam="eggs">What do you mean "bleh"</python>',
                 u'<python ministry="abuse">But I was looking for argument</python>']
    def test_tree(self):
        #Node types use string rather than numerical constants now
        #The root node type is called entity
        doc = amara.parse(self.MONTY_XML)

        self.assertEqual(doc.xml_type, tree.entity.xml_type)
        m = doc.xml_children[0] #xml_children is a sequence of child nodes
        self.assertEqual(m.xml_local, u'monty') #local name, i.e. without any prefix
        self.assertEqual (m.xml_qname, u'monty') #qualified name, e.g. includes prefix
        self.assertEqual(m.xml_prefix, None)
        self.assertEqual(m.xml_qname, u'monty') #qualified name, e.g. includes prefix
        self.assertEqual(m.xml_namespace, None)
        self.assertEqual(m.xml_name,  (None, u'monty')) #The "universal name" or "expanded name"
        self.assertEqual(m.xml_parent, doc)
        
        p1 = m.xml_children[0]
        XML_output = '<python spam="eggs">What do you mean "bleh"</python>'
        output = cStringIO.StringIO()
        xml_print(p1, stream=output)
        self.assertEqual(output.getvalue(), XML_output)
        
        self.assertEqual(p1.xml_attributes[(None, u'spam')], u"eggs")
        #Some manipulation
        p1.xml_attributes[(None, u'spam')] = u"greeneggs"
        self.assertEqual(p1.xml_attributes[(None, u'spam')], u"greeneggs")
        p1.xml_children[0].xml_value = u"Close to the edit"
        output = cStringIO.StringIO()
        xml_print(p1, stream=output)
        self.assertEqual(output.getvalue(),
                         '<python spam="greeneggs">Close to the edit</python>')

    def test_bindery(self):
        doc = bindery.parse(self.MONTY_XML)
        m = doc.monty
        p1 = doc.monty.python #or m.python; p1 is just the first python element
        self.assertEqual(p1.xml_attributes[(None, u'spam')], u'eggs')
        self.assertEqual(p1.spam, u'eggs')
        
        for p, line in zip(doc.monty.python, self.lines_py): #The loop will pick up both python elements
            output = cStringIO.StringIO()
            xml_print(p, stream=output)
            self.assertEqual(output.getvalue(), line)
                
    def test_dom(self):
        doc = dom.parse(self.MONTY_XML)
        for p, line in zip(doc.getElementsByTagNameNS(None, u"python"), self.lines_py): #A generator
            output = cStringIO.StringIO()
            xml_print(p, stream=output)
            self.assertEqual(output.getvalue(), line)
        p1 = doc.getElementsByTagNameNS(None, u"python").next()
        self.assertEqual(p1.getAttributeNS(None, u'spam'), u'eggs')
    def test_xpath(self):
        doc = bindery.parse(self.MONTY_XML)
        m = doc.monty
        p1 = doc.monty.python
        self.assertEqual(p1.xml_select(u'string(@spam)'), u'eggs')
        for p, line in zip(doc.xml_select(u'//python'), self.lines_py):
            output = cStringIO.StringIO()
            xml_print(p, stream=output)
            self.assertEqual(output.getvalue(), line)
            

if __name__ == '__main__':
    unittest.main()
        