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
from amara.test.xslt import filesource, stringsource

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
        doc = bindery.parse(tidy_atom(filesource('entry1.atom')))
        self.assertEqual(len(doc.xml_children), 1)
        self.assertEqual(len(list(doc.entry)), 1)
        self.assertEqual(len(list(doc.entry.link)), 1)
        return


class Test_atom2rdf_rss(unittest.TestCase):
    """Testing atom to RSS conversion"""
    def test_atom1(self):
        #doc = bindery.parse(tidy_atom(filesource('entry1.atom')))
        isrc = tidy_atom(filesource('rfc4287-1-1-2.atom'))
        print atom2rss1(isrc)
        return 

#
class Test_ejsonize(unittest.TestCase):
    """Testing conversion to simple data structure"""
    def test_ejsonize1(self):
        EXPECTED = [{u'updated': u'2005-07-31T12:29:29Z', u'title': u'Atom draft-07 snapshot', u'label': u'tag:example.org,2003:3.2397', u'content_text': u'\n     \n       [Update: The Atom draft is finished.]\n     \n   ', u'link': u'http://example.org/2005/04/02/atom', u'authors': [u'Mark Pilgrim'], u'summary': u'None', u'type': u'Entry'}]
        results = ejsonize(filesource('rfc4287-1-1-2.atom').source)
        self.assertEqual(results, EXPECTED)
        return


if __name__ == '__main__':
    testsupport.test_main()

