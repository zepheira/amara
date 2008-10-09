import sys

print '---------' 'Basic constraints'

from amara import bindery, xml_print
from amara.bindery.model import *

MONTY_XML = """<monty>
  <python spam="eggs">What do you mean "bleh"</python>
  <python ministry="abuse">But I was looking for argument</python>
</monty>"""

doc = bindery.parse(MONTY_XML)

c = constraint(u'@ministry')
try:
    doc.monty.python.xml_model.add_constraint(c, validate=True)
except bindery.BinderyError, e:
    print e

doc.monty.python.xml_attributes[None, u'ministry'] = u'argument'
doc.monty.python.xml_model.add_constraint(c, validate=True)

#print dir(doc)
#print dir(doc.monty.python)

#print doc.monty.python.xml_namespaces[None]
#print doc.xml_namespaces

print
print '---------' 'Attribute constraint class'

doc = bindery.parse(MONTY_XML)

c = attribute_constraint(None, u'ministry', u'nonesuch')
doc.monty.python.xml_model.add_constraint(c, validate=True)

xml_print(doc)

print
print '---------' 'Child element constraint class'

SVG = """<?xml version="1.0" encoding="utf-8"?>
<svg version="1.1" baseProfile="full"
    xmlns="http://www.w3.org/2000/svg">
  <title>A pair of lines and a pair of ellipses</title>
  <g>
    <ellipse cx="150" cy="100" rx="100" ry="50"/>
    <line x1="450" y1="50" x2="550" y2="150"/>
  </g>
  <g>
    <title>Rotated shapes</title>
    <ellipse cx="150" cy="300" rx="100" ry="50"
        transform="rotate(20)"/>
    <line x1="350" y1="200" x2="450" y2="300"
        transform="rotate(20)"/>
  </g>
</svg>
"""

from amara.namespaces import *
doc = bindery.parse(SVG)

c = child_element_constraint(SVG_NAMESPACE, u'title', u'[NO TITLE]')
doc.svg.g.xml_model.add_constraint(c, validate=True)

xml_print(doc)

print
print '---------' 'Examplotron model def'

LABEL_MODEL = '''<?xml version="1.0" encoding="utf-8"?>
<labels>
  <label>
    <name>[Addressee name]</name>
    <address>
      <street>[Address street info]</street>
      <city>[City]</city>
      <state>[State abbreviation]</state>
    </address>
  </label>
</labels>
'''

VALID_LABEL_XML = '''<?xml version="1.0" encoding="utf-8"?>
<labels>
  <label>
    <name>Thomas Eliot</name>
    <address>
      <street>3 Prufrock Lane</street>
      <city>Stamford</city>
      <state>CT</state>
    </address>
  </label>
</labels>
'''

INVALID_LABEL_XML = '''<?xml version="1.0" encoding="utf-8"?>
<labels>
  <label>
    <quote>What thou lovest well remains, the rest is dross</quote>
    <name>Ezra Pound</name>
    <address>
      <street>45 Usura Place</street>
      <city>Hailey</city>
      <state>ID</state>
    </address>
  </label>
</labels>
'''

from amara.bindery.model import *
label_model = examplotron_model(LABEL_MODEL)
doc = bindery.parse(VALID_LABEL_XML, model=label_model)
doc.xml_validate()

doc = bindery.parse(INVALID_LABEL_XML, model=label_model)
try:
    doc.xml_validate()
except bindery.BinderyError, e:
    print e

xml_print(doc)

print
print '---------' 'Binding defaults'

LABEL_MODEL = '''<?xml version="1.0" encoding="utf-8"?>
<labels>
  <label>
    <quote>What thou lovest well remains, the rest is dross</quote>
    <name>Ezra Pound</name>
    <address>
      <street>45 Usura Place</street>
      <city>Hailey</city>
      <state>ID</state>
    </address>
  </label>
</labels>
'''

TEST_LABEL_XML = '''<?xml version="1.0" encoding="utf-8"?>
<labels>
  <label>
    <name>Thomas Eliot</name>
    <address>
      <street>3 Prufrock Lane</street>
      <city>Stamford</city>
      <state>CT</state>
    </address>
  </label>
</labels>
'''

#An alternative to fixup that updates the binding object behavior without updating the XML itself
#Note: you can choose to combine binding defaults with fixup, if you like, but many usage patterns will tend to use one or the other: either you want a mechnism to normalize the XML itself, or a mechanism for smooth handling of non-normalized XML

#doc = bindery.parse(LABEL_XML)
#doc.labels.label.xml_model.set_default_value(None, u'quote', None)

from amara.bindery.model import *
label_model = examplotron_model(LABEL_MODEL)
doc = bindery.parse(TEST_LABEL_XML, model=label_model)
print doc.labels.label.quote #None, rather than raising AttributeError
#doc.xml_validate()



sys.exit(0)

doc = bindery.parse(INVALID_LABEL_XML, model=label_model)
doc.labels.label.xml_model.debug(doc.labels.label)
doc.labels.label.xml_model.validate()
doc.xml_model.validate()

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

