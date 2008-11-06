# -*- encoding: utf-8 -*-
# Testing new amara.tree API

# Testing quick reference examples

import unittest
import cStringIO
import copy

import amara
from amara.lib import testsupport
from amara import tree, xml_print
from amara import bindery

TEST1 = '<a x="1"><b>i</b><c>j<d/>k</c><b>l</b></a>'

class Test_constructs(unittest.TestCase):
    def test_empty_doc_shallow(self):
        '''Shallow copy of empty entity'''
        doc = tree.entity()
        copied = copy.copy(doc)
        self.assertNotEqual(doc, copied)
        self.assertEqual(copied.xml_type, tree.entity.xml_type)
        self.assertEqual(len(copied.xml_children), 0)
        return

    def test_empty_doc_deep(self):
        '''Deep copy of empty entity'''
        doc = tree.entity()
        copied = copy.deepcopy(doc)
        self.assertNotEqual(doc, copied)
        self.assertEqual(copied.xml_type, tree.entity.xml_type)
        self.assertEqual(len(copied.xml_children), 0)
        return

    def test_doc1_shallow(self):
        '''Shallow copy of entity'''
        doc = tree.entity()
        elem = doc.xml_element_factory(None, u'A')
        doc.xml_append(elem)
        copied = copy.copy(doc)
        self.assertNotEqual(doc, copied)
        self.assertEqual(copied.xml_type, tree.entity.xml_type)
        self.assertEqual(len(copied.xml_children), 0)
        return

    def test_doc1_deep(self):
        '''Deep copy of entity'''
        doc = tree.entity()
        elem = doc.xml_element_factory(None, u'A')
        doc.xml_append(elem)
        copied = copy.deepcopy(doc)
        self.assertNotEqual(doc, copied)
        self.assertEqual(copied.xml_type, tree.entity.xml_type)
        self.assertEqual(len(copied.xml_children), 0)
        return

    
if __name__ == '__main__':
    testsupport.test_main()
