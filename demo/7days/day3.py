import sys

print '---------' 'Grouping'

import itertools
import operator
import amara
from amara.writers.struct import *

XML="""\
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

doc = amara.parse(XML)

leaves = sorted(doc.xml_select(u'/env/*'), key=operator.attrgetter('xml_name'))

w = structwriter(indent=u"yes")
w.feed(
ROOT(
    E(u'env',
        ( E(ename + u'-wrapper',
            ( E(ename, e.xml_attributes.copy(), e.xml_children) for e in elems )
        ) for ename, elems in itertools.groupby(leaves, lambda x: x.xml_qname) ),
    )
))

print
print '---------' 'Bindery and operator'

RSS = 'http://feeds.feedburner.com/ClevelandClinicHealthTalkPodcast'
ATOM1 = 'http://uche.ogbuji.net/tech/publications.atom'

import operator
import itertools
from amara import bindery

ATOM1 = 'http://zepheira.com/news/atom/entries/'
ATOM2 = 'http://ma.gnolia.com/atom/full/people/Uche'

doc1 = bindery.parse(ATOM1)
doc2 = bindery.parse(ATOM2)
combined = itertools.chain(*[doc.feed.entry for doc in (doc1, doc2)])
for node in sorted(combined, key=operator.attrgetter('updated')):
    print node.title

print '---------' 'Merge XBEL'

BM1 = 'bm1.xbel'
BM2 = 'bm2.xbel'
from amara import bindery, xml_print

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

doc1 = bindery.parse(BM1)
doc2 = bindery.parse(BM2)
xbel_merge(doc1.xbel, doc2.xbel)
xml_print(doc1, indent=True)

print
print '---------' 'Merge XBEL by grouping iterators'

BM1 = 'bm1.xbel'
BM2 = 'bm2.xbel'
import itertools
import functools
from amara import bindery, xml_print
from amara.bindery.util import property_str_getter

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
    #All non-folder, non-title elements
    for e in f2.xml_select(u'*[not(self::folder or self::title)]'):
        f1.xml_append(e)
    return

doc1 = bindery.parse(BM1)
doc2 = bindery.parse(BM2)
merge(doc1.xbel, doc2.xbel)
xml_print(doc1, indent=True)

print
print '---------' 'Merge XBEL by grouping iterators, with model'


XBEL_DTDECL = '''<!DOCTYPE xbel PUBLIC 
       "+//IDN python.org//DTD XML Bookmark Exchange Language 1.0//EN//XML" 
       "http://www.python.org/topics/xml/dtds/xbel-1.0.dtd">'''

XBEL_MODEL = '''<?xml version="1.0"?>
<xbel version="1.0" xmlns:eg="http://examplotron.org/0/" xmlns:ak="http://purl.org/dc/org/xml3k/akara">
  <info eg:occurs="?">
    <metadata owner="http://example.com" eg:occurs="?">MD1</metadata>
  </info>
  <folder eg:occurs="*">
    <info eg:occurs="?">
      <metadata owner="http://example.com" eg:occurs="?">MD1</metadata>
    </info>
    <title>F1</title>
    <bookmark href="http://www.example.com" eg:occurs="*">
      <info eg:occurs="?">
        <metadata owner="http://example.com" eg:occurs="?">MD1</metadata>
      </info>
      <title eg:occurs="?">B1</title>
      <desc eg:occurs="?">DESC-B1</desc>
    </bookmark>
  </folder>
  <bookmark href="http://www.example.com">
    <info eg:occurs="?">
      <metadata owner="http://example.com" eg:occurs="?">MD1</metadata>
    </info>
    <title eg:occurs="?">B1</title>
    <desc eg:occurs="?">DESC-B1</desc>
  </bookmark>
</xbel>
'''

#...

