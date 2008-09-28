print '---------' 'Core tree'

import amara
from amara import tree

MONTY_XML = """<monty>
  <python spam="eggs">What do you mean "bleh"</python>
  <python ministry="abuse">But I was looking for argument</python>
</monty>"""

doc = amara.parse(MONTY_XML)
#Node types use string rather than numerical constants now
#The root node type is called entity
assert doc.xml_type == tree.entity.xml_type
m = doc.xml_children[0] #xml_children is a sequence of child nodes
assert m.xml_local == u'monty' #local name, i.e. without any prefix
assert m.xml_qname == u'monty' #qualified name, e.g. includes prefix
assert m.xml_prefix == None
assert m.xml_qname == u'monty' #qualified name, e.g. includes prefix
assert m.xml_namespace == None
assert m.xml_name == (None, u'monty') #The "universal name" or "expanded name"
assert m.xml_parent == doc

p1 = m.xml_children[0]

from amara import xml_print
#<python spam="eggs">What do you mean "bleh"</python>
xml_print(p1)
print
print p1.xml_attributes[(None, u'spam')]

#Some manipulation
p1.xml_attributes[(None, u'spam')] = u"greeneggs"
p1.xml_children[0].xml_value = u"Close to the edit"
xml_print(p1)
print

print
print '---------' 'Bindery'

from amara import bindery
from amara import xml_print

MONTY_XML = """<monty>
  <python spam="eggs">What do you mean "bleh"</python>
  <python ministry="abuse">But I was looking for argument</python>
</monty>"""

doc = bindery.parse(MONTY_XML)
m = doc.monty
p1 = doc.monty.python #or m.python; p1 is just the first python element
print
print p1.xml_attributes[(None, u'spam')]
print p1.spam

for p in doc.monty.python: #The loop will pick up both python elements
    xml_print(p)
    print

print
print '---------' 'DOM'

from amara import dom
from amara import xml_print

MONTY_XML = """<monty>
  <python spam="eggs">What do you mean "bleh"</python>
  <python ministry="abuse">But I was looking for argument</python>
</monty>"""

doc = dom.parse(MONTY_XML)
for p in doc.getElementsByTagNameNS(None, u"python"): #A generator
    xml_print(p)
    print

p1 = doc.getElementsByTagNameNS(None, u"python").next()
print p1.getAttributeNS(None, u'spam')

print
print '---------' 'XPath'

from amara import bindery
from amara import xml_print

MONTY_XML = """<monty>
  <python spam="eggs">What do you mean "bleh"</python>
  <python ministry="abuse">But I was looking for argument</python>
</monty>"""

doc = bindery.parse(MONTY_XML)
m = doc.monty
p1 = doc.monty.python
print p1.xml_select(u'string(@spam)')

for p in doc.xml_select(u'//python'):
    xml_print(p)
    print

print
print '---------' 'HTML'

import html5lib
from html5lib import treebuilders
from amara.bindery import html
from amara import xml_print

f = open("eg.html")
parser = html5lib.HTMLParser(tree=html.treebuilder)
doc = parser.parse(f)
print unicode(doc.html.head.title)
xml_print(doc.html.head.title)
print
print doc.xml_select(u"string(/html/head/title)")

