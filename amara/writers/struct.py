########################################################################
# amara/writers/struct.py

"""
An old idea for a friendly markup serialization interface, with a big hat-tip to pyfo
http://foss.cpcc.edu/pyfo/

Note: this module has some departures from the reguler PEP 8 naming convention
for considered reasons of clarity in use
"""

import sys
from itertools import *
from amara.writers import WriterError
#from amara.writers.xmlwriter import *
from amara import XML_NAMESPACE
from amara.lib.xmlstring import *

__all__ = ['structwriter', 'E', 'NS', 'ROOT', 'RAW']

class StructWriterError(WriterError):

    ATTRIBUTE_ADDED_TOO_LATE = 1
    ATTRIBUTE_ADDED_TO_NON_ELEMENT = 2


class structwriter(object):
    def __init__(self, stream=sys.stdout, **kwargs):
        #writer - instance of `amara.writers.writer`, or None to create a default instance
        """
        """
        #self.writer = writer or xmlwriter()
        from amara import writer
        self.writer = writer(stream, **kwargs)

    def feed(self, obj):
        """
        obj - an object or iterator of objects matching the structwriter's specifications
        """
        if isinstance(obj, ROOT):
            self.writer.start_document()
            for subobj in obj.content:
                self.feed(subobj)
            self.writer.end_document()
            return
        if isinstance(obj, NS):
            return
        if isinstance(obj, E):
            sniffer, content = tee(obj.content)
            obj.namespaces = {}
            for subobj in sniffer:
                if isinstance(subobj, NS):
                    #Consume it from the twin, too
                    content.next()
                    obj.namespaces[subobj.prefix] = subobj.namespace
                else:
                    break
            self.writer.start_element(obj.qname, obj.ns, namespaces=obj.namespaces, attributes=obj.attributes or {})
            for subobj in obj.content:
                self.feed(subobj)
            self.writer.end_element(obj.qname, obj.ns)
            return
        if isinstance(obj, basestring):
            self.writer.text(U(obj))
            return
        try:
            for subobj in obj:
                self.feed(subobj)
        except TypeError:
            if callable(obj):
                self.feed(obj())
            else:
                #Just try to make it text, i.e. punt
                self.feed(unicode(obj))

class E(object):
    def __init__(self, name, *items):
        if items and isinstance(items[0], dict):
            attributes = items[0]
            self.content = items[1:]
        else:
            self.content = items
            attributes = {}
        #if len(self.content) > 1:
        #    self.content = chain(*(( i if (hasattr(i, 'next') and hasattr(i, '__iter__')) else [i] ) for i in self.content))
        if isinstance(name, tuple):
            self.ns, self.qname = imap(U, name)
        else:
            self.ns, self.qname = None, U(name)
        #XXX: Move to dictionary set expr in 2.6 or 3.0
        self.attributes = {} if attributes else None
        for name, value in attributes.iteritems():
            if isinstance(name, tuple):
                ns, qname = imap(U, name)
            else:
                ns, qname = None, U(name)
            self.attributes[qname, ns] = value

class NS(object):
    def __init__(self, prefix, namespace):
        self.prefix = prefix
        self.namespace = namespace

class RAW(object):
    def __init__(self, *content):
        self.content = content

class ROOT(object):
    def __init__(self, *content):
        self.content = content

"""
test_input = \
ROOT(
  E(u'string-content', u'hello'),
  #You can use string objects (UTF-8 assumed), though we strongly suggest always using Unicode
  E('string-content', 'yuck'),
  E('float-content', 3.14),
  E(u'int-content', 5),
  E(u'unicode-content', u'this is unicode: \u221e'),
  E(u'list-content', [E('child', 'a'), RAW('<raw-node message="hello"/>'), E('child', 'b')]),
  E(u'dict-content', {u'parrot': u'dead', u'spam': u'eggs'}),
  #Again using string objects
  E(u'dict-content', dict(parrot='dead', spam='eggs')),
  E(u'gen-content', (('node', x) for x in range(6))),
  E(u'monty', E('spam', 'eggs')),
  E(u'empty'),
  E(u'object-content', type('obj', (), dict(__repr__=lambda s: "object repr"))()),
  E(u'func', lambda: u'this is a func'),
  E(u'raw-xml-content', RAW('<a>b</a>', '<c>d</c>')) #The multiple raw text bits are just concatenated
)


<?xml version="1.0" encoding="ascii"?>
<root>
  <string>hello</string>
  <float>3.14</float>
  <int>5</int>
  <unicode>this is unicode: &#8734;</unicode>
  <list>
    <node>hello</node>
    <raw-node message="hello"/>
  </list>
  <dictionary>
    <parrot>dead</parrot>
    <spam>eggs</spam>
  </dictionary>
  <generator>
    <node>0</node>
    <node>1</node>
    <node>2</node>
    <node>3</node>
    <node>4</node>
    <node>5</node>
  </generator>
  <tuple>
    <one>two</one>
  </tuple>
  <None/>
  <int-zero>0</int-zero>
  <float-zero>0.0</float-zero>
  <empty-string/>
  <object>object repr</object>
  <func>this is a func</func>
  <escaping> &gt; &lt; &amp; </escaping>
</root>


from Ft.Xml import MarkupWriter

# Set the output doc type details (required by XSA)
SYSID = u"http://www.garshol.priv.no/download/xsa/xsa.dtd"
PUBID = u"-//LM Garshol//DTD XML Software Autoupdate 1.0//EN//XML"
writer = MarkupWriter(indent=u"yes", doctypeSystem=SYSID,
                      doctypePublic=PUBID)
writer.startDocument()
writer.startElement(u'xsa')
writer.startElement(u'vendor')

# Element with simple text (#PCDATA) content
writer.simpleElement(u'name', content=u'Centigrade systems')
writer.simpleElement(u'email', content=u"info@centigrade.bogus")
writer.endElement(u'vendor')

# Element with an attribute
writer.startElement(u'product', attributes={u'id': u"100\u00B0"})
writer.simpleElement(u'name', content=u"100\u00B0 Server")
writer.simpleElement(u'version', content=u"1.0")
writer.simpleElement(u'last-release')
writer.text(u"20030401")

# Empty element
writer.simpleElement(u'changes')
writer.endElement(u'product')
writer.endElement(u'xsa')
writer.endDocument()
"""

