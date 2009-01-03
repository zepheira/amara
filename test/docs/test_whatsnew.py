# Testing new Amara2 capabilities
# Based on http://wiki.xml3k.org/Amara2/Whatsnew
# lm

import unittest
import cStringIO
import amara
from amara import tree, xml_print

XMLDECL = '<?xml version="1.0" encoding="UTF-8"?>\n'

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

    ###################################################################
    #### Reading with new factories callables
    def test_reading_building(self):
        doc = tree.entity()
        doc.xml_append(tree.processing_instruction(u'xml-stylesheet', 
                                                   u'href="classic.xsl" type="text/xml"'))
        A = tree.element(None, u'A')
        A.xml_attributes[u'a'] = u'b'
        A.xml_append(tree.text(u'One'))
        doc.xml_append(A)
        doc.xml_append(tree.comment(u"This is easy"))
        doc2 = amara.parse('whatsnew_doc1.xml')
        output1 = cStringIO.StringIO()        
        output2 = cStringIO.StringIO()        
        xml_print(doc, stream=output1)
        xml_print(doc2, stream=output2)
        self.assertEqual(output1.getvalue(), output2.getvalue())
        return

        
    def test_reading_without_validation(self):
        ### TODO
        pass
    
    def test_reading_with_validation(self):
        ### TODO
        pass
        
    def test_reading_with_specialized_classes(self):
        ### TODO
        pass
    
    ###################################################################
    #### Creating a document from scratch with new factories
    
    def test_create_new_doc(self):
        EXPECTED = "<spam/>"
        doc = tree.entity()
        doc.xml_append(tree.element(None, u'spam'))
        self.compare_output(doc, XMLDECL+EXPECTED)
        return
    
    def test_create_new_doc_pi(self):
        EXPECTED = '<?xml-stylesheet href="classic.xsl" type="text/xml"?><A a="b">One</A>'
        doc = tree.entity()
        doc.xml_append(tree.processing_instruction(u'xml-stylesheet', 
                                                   u'href="classic.xsl" type="text/xml"'))
        A = tree.element(None, u'A')
        A.xml_attributes[u'a'] = u'b'
        A.xml_append(tree.text(u'One'))
        doc.xml_append(A)
        self.compare_output(doc, XMLDECL+EXPECTED)
        return 
    
    def test_create_new_doc_comment(self):
        EXPECTED = '<A a="b">One</A><!--This is easy-->'
        doc = tree.entity()
        A = tree.element(None, u'A')
        A.xml_attributes[u'a'] = u'b'
        A.xml_append(tree.text(u'One'))
        doc.xml_append(A)
        doc.xml_append(tree.comment(u"This is easy"))
        self.compare_output(doc, XMLDECL+EXPECTED)
        return 
    
    def test_create_new_doc_attr_dict(self):
        EXPECTED = '<?xml-stylesheet href="classic.xsl" type="text/xml"?><A a="b">One</A><!--This is easy-->'
        doc = tree.entity()
        doc.xml_append(tree.processing_instruction(u'xml-stylesheet', 
                                                   u'href="classic.xsl" type="text/xml"'))
        A = tree.element(None, u'A')
        A.xml_attributes[u'a'] = u'b'
        A.xml_append(tree.text(u'One'))
        doc.xml_append(A)
        doc.xml_append(tree.comment(u"This is easy"))
        self.compare_output(doc, XMLDECL+EXPECTED)
        return 
        

    def test_create_new_doc_attr_tree_attr(self):
        EXPECTED = '<A a="b">One</A>'
        doc = tree.entity()
        A = tree.element(None, u'A')
        
        new_attr = tree.attribute(None, u'a', u'b')
        A.xml_attributes.setnode(new_attr)
        A.xml_append(tree.text(u'One'))
        doc.xml_append(A)
        self.compare_output(doc, XMLDECL+EXPECTED)
        return 
    
    def test_create_new_doc_attr_factory(self):
        EXPECTED = '<A a="b">One</A>'
        doc = tree.entity()
        A = tree.element(None, u'A')
        
        new_attr = A.xml_attribute_factory(None, u'a', u'b')
        A.xml_attributes.setnode(new_attr)
        A.xml_append(tree.text(u'One'))
        doc.xml_append(A)
        self.compare_output(doc, XMLDECL+EXPECTED)
        return 

    ###################################################################
    #### Testing writers
    
    ###################################################################
    #### Testing node types
    
    def test_node_types(self):
        doc = amara.parse('<A/>')
        A = doc.xml_children[0]
        self.assertRaises(AttributeError, lambda: A.nodeType)
        self.assertEqual(A.xml_type, 'element')
        self.assertTrue(isinstance(A, tree.element))
                        
    def test_no_longer(self):
        doc = amara.parse('<A/>')
        A = doc.xml_children[0]
        for old_method in ['nodeName', 'nodeValue', 'namespaceURI', 'localName', 
                           'prefix', 'childNodes', 'isSameNode', 'xpath', 'rootNode',
                           'baseURI', 'xmlBase', 'documentURI']:
            self.assertRaises(AttributeError, getattr, A, "%s" % old_method)
    def test_is(self):
        doc = amara.parse('<A/>')
        A1 = doc.xml_select(u'/A')[0]
        A2 = doc.xml_children[0]
        self.assertTrue(A1 is A2)
        
    def test_empty_root(self):
        A = tree.element(None, u'A')
        self.assertEqual(None, A.xml_root)
        no_root = A.xml_select(u'/')
        self.assertTrue(isinstance(no_root, amara.xpath.datatypes.nodeset))
        self.assertEqual(no_root[0], None)
        
    def test_root(self):
        doc = amara.parse('<A><B><C/></B></A>')
        C = doc.xml_select(u'//C').pop()
        self.assertEqual(C.xml_root, doc)
        mynode = C
        while mynode.xml_parent: 
            mynode = mynode.xml_parent
        self.assertEqual(mynode, doc)
    def test_xml_base(self):
        """
        TODO
        """
        pass
    
    def test_ids(self):
        DOC = '<!DOCTYPE xsa PUBLIC "-//LM Garshol//DTD XML Software Autoupdate 1.0//EN//XML" "http://www.garshol.priv.no/download/xsa/xsa.dtd">\n<xsa/>'
        doc = amara.parse(DOC, standalone=True)
        self.assertEqual(doc.xml_system_id, 
                         u'http://www.garshol.priv.no/download/xsa/xsa.dtd')
        self.assertEqual(doc.xml_public_id, 
                         u'-//LM Garshol//DTD XML Software Autoupdate 1.0//EN//XML')        
    
    ###################################################################
    #### copy tests : test/tree/test_copy.py
    
    
    ###################################################################
    #### Testing Attribute Nodes
    def test_attr_no_longer(self):
        doc = amara.parse('<A a="b"/>')
        A = doc.xml_children[0]
        attr_a = A.xml_attributes.getnode(None, u'a')
        for old_method in ['nodeName', 'nodeValue', 'qualifiedName', 'value', 'namespaceURI', 
                           'localName', 'prefix', 'specified']:
            self.assertRaises(AttributeError, getattr, attr_a, "%s" % old_method)

    def test_attr_valid_methods(self):
        new_attr_methods = ['xml_base', 'xml_following_sibling', 'xml_local', 
                           'xml_name', 'xml_namespace', 'xml_nodeid', 
                           'xml_parent', 'xml_preceding_sibling', 'xml_prefix', 
                           'xml_qname', 'xml_root', 'xml_select', 'xml_specified', 
                           'xml_type', 'xml_typecode', 'xml_value']
        doc = amara.parse('<A a="b"/>')
        A = doc.xml_children[0]
        attr_a = A.xml_attributes.getnode(None, u'a')
        new_methods = [attr for attr in dir(attr_a) if attr.startswith('xml')]
        self.assertEqual(new_methods, new_attr_methods)
        self.assertEqual(attr_a.xml_name, (None, u'a'))
        
    ###################################################################
    #### Testing Character Data
    
    def test_chardata_no_longer(self):
        doc = amara.parse('<A>Spam</A><!--eggs-->')
        A = doc.xml_children[0]
        spam = A.xml_children[0]
        for old_method in ['length', 'substringData', 'insertData', 'replaceData',
                           'appendData', 'deleteData']:
            self.assertRaises(AttributeError, getattr, spam, "%s" % old_method)
            
    def test_chardata_valid_methods(self):
        new_chardata_methods = ['xml_base', 'xml_following_sibling', 
                                'xml_nodeid', 'xml_parent', 
                                'xml_preceding_sibling', 'xml_root', 
                                'xml_select', 'xml_type', 'xml_typecode', 
                                'xml_value']
        doc = amara.parse('<A>Spam</A><!--eggs-->')
        A = doc.xml_children[0]
        spam = A.xml_children[0]
        new_methods = [attr for attr in dir(spam) if 'xml_' == attr[:4]]
        self.assertEqual(new_methods, new_chardata_methods)

    def test_chardata(self):
        doc = amara.parse('<A>Spam</A><!--eggs-->')
        A = doc.xml_children[0]
        spam = A.xml_children[0]
        self.assertEqual(spam.xml_value, u'Spam')
        self.assertEqual(len(spam.xml_value), 4)
        self.assertEqual(spam.xml_value[1:3], u'pa')
        spam.xml_value += u' eggs'
        self.assertEqual(spam.xml_value, u'Spam eggs')

    def test_chardata_unb(self):
        spam = tree.text(u'Spam')
        self.assertEqual(spam.xml_value, u'Spam')
        self.assertEqual(len(spam.xml_value), 4)
        self.assertEqual(spam.xml_value[1:3], u'pa')
        spam.xml_value += u' eggs'
        self.assertEqual(spam.xml_value, u'Spam eggs')

    def test_comment_valid_methods(self):
        new_chardata_methods = ['xml_base', 'xml_following_sibling', 
                                'xml_nodeid', 'xml_parent', 
                                'xml_preceding_sibling', 'xml_root', 
                                'xml_select', 'xml_type', 'xml_typecode', 
                                'xml_value']
        doc = amara.parse('<!-- Begin spam --> <A>Spam</A><!-- End spam -->')
        comment  = doc.xml_children[0]
        new_methods = [attr for attr in dir(comment) if 'xml_' == attr[:4]]
        self.assertEqual(new_methods, new_chardata_methods)
        
    def test_comment_data(self):
        doc = amara.parse('<!--Begin spam--> <A>Spam</A><!--End spam-->')
        comment  = doc.xml_children[0]
        self.assertEqual(comment.xml_value, u'Begin spam')
        self.assertEqual(len(comment.xml_value), 10)
        self.assertEqual(comment.xml_value[:5], u'Begin')
        comment.xml_value += u' more spam'
        self.assertEqual(comment.xml_value, u'Begin spam more spam')
        A = doc.xml_children[1]
        self.assertEqual(comment.xml_following_sibling, A)
        self.assertEqual(comment.xml_preceding_sibling, None)
    
    def test_comment_data_unb(self):
        comment  = tree.comment(u'Begin spam')
        self.assertEqual(comment.xml_value, u'Begin spam')
        self.assertEqual(len(comment.xml_value), 10)
        self.assertEqual(comment.xml_value[:5], u'Begin')
        comment.xml_value += u' more spam'
        self.assertEqual(comment.xml_value, u'Begin spam more spam')
        

    ###################################################################
    #### Testing Element Nodes
    def test_element_no_longer(self):
        old_methods = ['nodeName', 'tagName', 'qualifiedName', 'namespaceURI',
                       'localName', 'prefix', 'childNodes', 'hasChildNodes',
                       'firstChild', 'lastChild', 'normalize', 'nextSibling', 
                       'previousSibling', 'getElementById', 'getAttributeNodeNS', 
                       'setAttributeNodeNS', 'getAttributeNS', 'setAttributeNS',
                       'hasAttributeNS', 'removeAttributeNode', 
                       'removeAttribute', 'attributes', 'appendChild', 
                       'removeChild', 'insertBefore', 'replaceChild']
        element = tree.element(None, u'A')
        for old_method in old_methods:
            self.assertRaises(AttributeError, getattr, element, "%s" % old_method)
    def test_element_valid_properties(self):
        new_operations = ['xml_append', 'xml_attribute_added', 
                          'xml_attribute_factory', 'xml_attribute_modified',
                          'xml_attribute_removed', 'xml_attributes', 'xml_base',
                          'xml_child_inserted', 'xml_child_removed', 
                          'xml_children', 'xml_first_child', 
                          'xml_following_sibling', 'xml_index', 'xml_insert', 
                          'xml_last_child', 'xml_local', 'xml_name', 
                          'xml_namespace', 'xml_namespaces', 'xml_nodeid', 
                          'xml_normalize', 'xml_parent', 'xml_preceding_sibling', 
                          'xml_prefix', 'xml_qname', 'xml_remove', 'xml_replace', 
                          'xml_root', 'xml_select', 'xml_type', 'xml_typecode',
                          'xmlns_attributes']
        element = tree.element(None, u'A')
        new_methods = [attr for attr in dir(element) if attr.startswith('xml')]
        for operation in new_methods:
            self.assertTrue(operation in new_operations)
        return
    def test_element_inmutable_properties(self):
        inmutable = ['xml_qname', 'xml_children', 'xml_first_child', 
                     'xml_last_child', 'xml_following_sibling', 
                     'xml_preceding_sibling']
        DOC = '<product id="1144" xmlns="http://example.com/product-info">Computer</product>'
        doc = amara.parse(DOC)
        element = doc.xml_children[0]
        for prop in inmutable:
            self.assertRaises(AttributeError, setattr, element, "%s" % prop, u'spam')
        element.xml_namespaces[u'ns'] = u'urn:bogus'
        self.assertRaises(AttributeError, setattr, element, 'xml_namespace', u'urn:bogus')
        return
    
    def test_element_new_features(self):
       
        DOC = '<A xmlns="urn:bogus" a="aa" b="bb"><B/><B/><B/></A>'
        doc = amara.parse(DOC)
        A = doc.xml_children[0]
        self.assertEqual(len(A.xml_name), 2)
        self.assertEqual(A.xml_name, (u"urn:bogus", u"A"))
        B2 = A.xml_children[1]
        self.assertEqual(A.xml_index(B2), 1)
        # self.assertRaises(ValueError,  A.xml_index(B2, 2))  ### ??? 
        self.assertEqual([u'a', u'b'], [k[1] for k in A.xml_attributes])
        self.assertEqual([u'a', u'b'], [k[1] for k in A.xml_attributes.keys()])
        self.assertEqual([u'aa', u'bb'], [k for k in A.xml_attributes.values()])
        self.assertEqual(len([k for k in A.xml_attributes.nodes()]), 2)
        return
    
   ###################################################################
    #### Testing Processing Instructions
    def test_pi_no_longer(self):
        pi = tree.processing_instruction(
            u'xml-stylesheet',
            u'href="classic.xsl" type="text/xml"')
        
        old_methods = ['nodeName', 'nodeValue', 'target', 'data', 
                       'previousSibling','nextSibling']
        for old_method in old_methods:
            self.assertRaises(AttributeError, getattr, pi, "%s" % old_method)
    def test_pi_valid_properties(self):
        ### REVIEW new properties 
        new_operations = ['xml_data', 'xml_target', 
                          'xml_following_sibling',
                          'xml_preceding_sibling']
        
        pi = tree.processing_instruction(
            u'xml-stylesheet',
            u'href="classic.xsl" type="text/xml"')
        new_methods = [attr for attr in dir(pi) if attr.startswith('xml')]
        for operation in new_operations:
            self.assertTrue(operation in new_methods)
        return
    def test_pi_inmutable_properties(self):
        pi = tree.processing_instruction(
            u'xml-stylesheet',
            u'href="classic.xsl" type="text/xml"')
        inmutable = ['xml_following_sibling', 'xml_preceding_sibling']
        for prop in inmutable:
            self.assertRaises(AttributeError, setattr, pi, "%s" % prop, u'spam')
        return
    
            
if __name__ == '__main__':
    unittest.main()

