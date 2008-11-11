# -*- encoding: utf-8 -*-
# Testing new amara.tree API

# Testing namespaces
#See "Working with namespaces" section in http://wiki.xml3k.org/Amara2/Whatsnew

import unittest
import cStringIO

import amara
from amara.lib import testsupport
from amara import tree, xml_print

TEST1 = '''<a:top xmlns:a="urn:bogus:a" xmlns:b="urn:bogus:b"><a:monty/></a:top>
'''

NS_A = u"urn:bogus:a"
NS_B = u"urn:bogus:b"

class Test_basics(unittest.TestSuite):
    class Test_namespace_mutation(unittest.TestCase):
        def test_namespace_fixup_from_scratch(self):
            '''Basic ns fixup upon mutation'''
            doc = tree.entity()
            elem = doc.xml_element_factory(NS_A, u'top')
            doc.xml_append(elem)
            self.assertEqual(doc.xml_first_child.xml_namespace, NS_A)
            return

        def test_namespace_fixup(self):
            '''Basic ns fixup upon mutation'''
            doc = amara.parse(TEST1)
            doc.xml_first_child.xml_namespace = NS_B
            #Side-effect is doc.monty.xml_prefix = u"b"
            self.assertEqual(doc.xml_first_child.xml_namespace, NS_B)
            self.assertEqual(doc.xml_first_child.xml_prefix, u'b')
            return

    
if __name__ == '__main__':
    testsupport.test_main()
