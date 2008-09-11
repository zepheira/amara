#Import the basic writer class for users
from amara import writer
w = writer(indent=u"yes") #Operates in streaming mode
w.start_document()
w.start_element(u'xsa')
w.start_element(u'vendor')
#Element with simple text (#PCDATA) content
w.simple_element(u'name', content=u'Centigrade systems')
#Note writer.text(content) still works
w.simple_element(u'email', content=u"info@centigrade.bogus")
w.end_element(u'vendor')
#Element with an attribute
w.start_element(u'product', attributes={u'id': u"100\u00B0"})
#Note w.attribute(name, value, namespace=None) still works
w.simple_element(u'name', content=u"100\u00B0 Server")
#XML fragment
#w.xml_fragment('<version>1.0</version><last-release>20030401</last-release>')
#Empty element
w.simple_element(u'changes')
w.end_element(u'product')
w.end_element(u'xsa')
w.end_document()
print

#Now an HTML example

w = writer(method=u"html") #indent=u"yes" is default in this mode
w.start_document()
w.start_element(u'html')
w.start_element(u'head')
w.simple_element(u'title', content=u'Hello')
w.end_element(u'head')
w.start_element(u'body')
#w.start_element(u'body', attributes={u'id': u"100\u00B0"})
w.simple_element(u'p', content=u"World")
#XML fragment
#w.xml_fragment('<version>1.0</version><last-release>20030401</last-release>')
#Empty element
w.simple_element(u'br')
w.end_element(u'html')
w.end_document()
print

from amara.writers.struct import *

w = structwriter(indent=u"yes").feed(
ROOT(
  E(u'doc',
    E(u'a', u'hello'),
    #E('float-content', 3.14),
    E((None, u'b'), u'this is unicode: \u221e'),
    #E(u'list-content', [E('child', 'a'), RAW('<raw-node message="hello"/>'), E('child', 'b')]),
    E(u'c', {u'parrot': u'dead', u'spam': u'eggs'}),
    E((None, u'c'), {u'parrot': u'dead', (None, u'spam'): u'eggs'}, u'again'),
    E(u'gen-content', (E('node', x) for x in range(6))),
    E(u'monty', E('spam', 'eggs')),
    E(u'empty'),
    E(u'func', lambda: u'this is a func'),
    #E(u'raw-xml-content', RAW('<a>b</a>', '<c>d</c>')) #The multiple raw text bits are just concatenated
  )
))

print

