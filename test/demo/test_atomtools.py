import unittest
import os
from cStringIO import StringIO
import tempfile

from amara.lib import testsupport
from amara.bindery import html
from amara import tree, xml_print, bindery
from amara import tree

from amara.tools.atomtools import *

from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

def tidy_atom(source):
    doc = bindery.parse(source.source)
    tidy_content_element(doc)
    buf = StringIO()
    xml_print(doc, stream=buf, indent=True)
    #self.assertEqual(buf.getvalue(), expected)
    return buf.getvalue()


class Test_tidy_atom(unittest.TestCase):
    """Testing untidy atom 1"""
    def test_parse_file(self):
        """"""
        doc = bindery.parse(tidy_atom(filesource('entry1.atom')))
        self.assertEqual(len(doc.xml_children), 1)
        self.assertEqual(len(list(doc.entry)), 1)
        self.assertEqual(len(list(doc.entry.link)), 1)
        return
        self.assertEqual(doc.xml_children[0].xml_type, tree.element.xml_type)
        self.assertEqual(doc.xml_children[0].xml_qname, 'html')
        self.assertEqual(doc.xml_children[0].xml_namespace, None)
        self.assertEqual(doc.xml_children[0].xml_prefix, None)
        self.assertEqual(len(list(doc.html.xml_elements)), 2)
        return


class Test_atom2rdf_rss(unittest.TestCase):
    """Testing untidy atom 1"""
    def test_atom1(self):
        """"""
        #doc = bindery.parse(tidy_atom(filesource('entry1.atom')))
        isrc = tidy_atom(filesource('rfc4287-1-1-2.atom'))
        print atom2rss1(isrc)
        return 


if __name__ == '__main__':
    testsupport.test_main()

