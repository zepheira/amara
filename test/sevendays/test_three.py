import os
import unittest
import cStringIO

import operator
import itertools
import functools
import amara
from amara.writers.struct import *
from amara.writers import lookup
from amara import bindery
from amara.bindery.util import property_str_getter

from amara.test import file_finder

FILE = file_finder(__file__)

def merge_folders(folder1, folder2):
    #Yes, the list must be copied to avoid mutate-while-iterate bugs
    for child in folder2.xml_select('*'):
        #No need to copy title element
        if child.xml_qname == u'title': continue
        elif child.xml_qname == u'folder':
            for a_folder in folder1.folder:
                if unicode(child.title) == unicode(a_folder.title):
                    merge_folders(a_folder, child)
                    break
            else:
                folder1.xml_append(child)
        else:
            folder1.xml_append(child)
    return

def xbel_merge(xbel1, xbel2):
    for child in xbel2.xml_select('*'):
        if child.xml_qname == u'folder':
            for a_folder in xbel1.folder:
                if unicode(child.title) == unicode(a_folder.title):
                    merge_folders(a_folder, child)
                    break
            else:
                xbel1.xml_append(child)
        elif child.xml_qname == u'bookmark':
            xbel1.xml_append(child)
    return

def normalize_whitespace(doc):
    """Normalize DOM tree and remove whitespace.

    Necessary to ensure that the pretty-printed XML tree
    looks correct.
    """
    doc.xml_normalize()         # Merge text nodes where possible
    for text in list(doc.xml_select('descendant::text()')):
        # If text node is all whitespace or empty, remove it.
        if not text.xml_value.strip():
            text.xml_parent.xml_remove(text)

title_getter = functools.partial(property_str_getter, 'title')
def merge(f1, f2):
    folders = sorted(itertools.chain(f1.folder or [], f2.folder or []),
                     key=title_getter)
    folder_groups = itertools.groupby(folders, title_getter)
    for ftitle, folders in folder_groups:
        main = folders.next()
        rest = list(folders)
        for f in rest:
            merge(main, f)
        if main.xml_parent != f1:
            f1.xml_append(main)
    #All elements that are not folder, title, or info
    for e in f2.xml_select(u'*[not(self::folder or self::title or self::info)]'):
        f1.xml_append(e)
    return


class TestIterators(unittest.TestCase):
    def setUp(self):
        self.XML ="""\
<env>
  <a id="1"/>
  <b id="1.1"/>
  <c id="1.2"/>
  <a id="2"/>
  <b id="2.1"/>
  <c id="2.2"/>
  <a id="3"/>
  <b id="3.1"/>
  <c id="3.2"/>
</env>
"""
    def test_iterator(self):
        doc = amara.parse(self.XML)
        output = cStringIO.StringIO()
        XML_groupby="""\
<?xml version="1.0" encoding="utf-8"?>
<env>
  <a-wrapper>
    <a id="1"/>
    <a id="2"/>
    <a id="3"/>
  </a-wrapper>
  <b-wrapper>
    <b id="1.1"/>
    <b id="2.1"/>
    <b id="3.1"/>
  </b-wrapper>
  <c-wrapper>
    <c id="1.2"/>
    <c id="2.2"/>
    <c id="3.2"/>
  </c-wrapper>
</env>"""
        leaves = sorted(doc.xml_select(u'/env/*'), key=operator.attrgetter('xml_name'))
        
        w = structwriter(indent=u"yes", stream=output)
        w.feed(
            ROOT(
                E(u'env',
                  ( E(ename + u'-wrapper',
                      ( E(ename, e.xml_attributes.copy(), e.xml_children) for e in elems )
                      ) for ename, elems in itertools.groupby(leaves, lambda x: x.xml_qname) ),
                  )
            ))
        self.assertEqual(output.getvalue(), XML_groupby)
        
    def test_combined(self):
        #ATOM1 = 'http://zepheira.com/news/atom/entries/'
        #ATOM2 = 'http://ma.gnolia.com/atom/full/people/Uche'
        ATOM1 = FILE('zepheira_atom.xml')  #local download for testing
        ATOM2 = FILE('magnolia_uche.xml')  #local download for testing
        output = cStringIO.StringIO()
        combined_output = open(FILE('entries_combined.txt')).read()  #local file for testing
        doc1 = bindery.parse(ATOM1)
        doc2 = bindery.parse(ATOM2)
        combined = itertools.chain(*[doc.feed.entry for doc in (doc1, doc2)])
        for node in sorted(combined, key=operator.attrgetter('updated')):
            print >> output, node.title
        self.assertEqual(output.getvalue(), combined_output)
           
    def test_xbel_1(self):
        #BM1 = 'http://hg.4suite.org/amara/trunk/raw-file/bb6c40828b2d/demo/7days/bm1.xbel'
        #BM2 = 'http://hg.4suite.org/amara/trunk/raw-file/bb6c40828b2d/demo/7days/bm2.xbel'
        doc1 = bindery.parse(FILE('bm1.xbel'))
        doc2 = bindery.parse(FILE('bm2.xbel'))

        xbel_merge(doc1.xbel, doc2.xbel)
        normalize_whitespace(doc1)
        output = doc1.xml_encode(lookup("xml-indent")) + '\n'
        self.assertEqual(output, open(FILE('merged-1.xbel')).read())
        
    def test_xbel_2(self):  
        #BM1 = 'http://hg.4suite.org/amara/trunk/raw-file/bb6c40828b2d/demo/7days/bm1.xbel'
        #BM2 = 'http://hg.4suite.org/amara/trunk/raw-file/bb6c40828b2d/demo/7days/bm2.xbel'
        doc1 = bindery.parse(FILE('bm1.xbel'))
        doc2 = bindery.parse(FILE('bm2.xbel'))
        
        merge(doc1.xbel, doc2.xbel)
        normalize_whitespace(doc1)
        output = doc1.xml_encode(lookup("xml-indent")) + '\n'
        self.assertEqual(output, open(FILE('merged-2.xbel')).read())
        
if __name__ == '__main__':
    unittest.main()
        
