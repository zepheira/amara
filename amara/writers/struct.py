########################################################################
# amara/writers/struct.py

"""
An old idea for a friendly markup serialization interface, with a big hat-tip to pyfo
http://foss.cpcc.edu/pyfo/

Note: Python stdlib has a struct module so you might want to consider importng as follows:

from amara.writers.struct import struct as structwriter
"""

from amara.writers import *
from amara.writers.xmlwriter import *
from amara import XML_NAMESPACE

__all__ = ['struct', 'E', 'ROOT', 'RAW']

class StructWriterError(Error):

    ATTRIBUTE_ADDED_TOO_LATE = 1
    ATTRIBUTE_ADDED_TO_NON_ELEMENT = 2


class struct(object):
    def __init__(self, writer=None):
        """
        writer - instance of `amara.writers.writer`, or None to create a default instance
        """
        self.writer = writer or xmlwriter()

    def feed(self, obj):
        """
        obj - an object or iterator of objects matching the structwriter's specifications
        """
        if isinstance(obj, ROOT):
            for subobj in obj.content:
                self.feed(subobj)
        if isinstance(obj, E):
            try:
                ns, tagname = E.name
            except TypeError:
                ns, tagname = None, E.name
            if tagname.startswith('xml:'):
                #Can use such a raw test because of the special restrictions on XML prefix
                ns = XML_NAMESPACE
            if ns == EMPTY_NAMESPACE and u':' in tagname:
                #If there's a prefix, but not a namespace, complain
                #raise MarkupWriterException(MarkupWriterException.ELEM_PREFIX_WITHOUT_NAMESPACE)
                raise TypeError("Prefixed name %s specified without namespace.  Namespace should be provided in the tuple."%(tagname))
            self.writer.startElement(name, ns)
            if attributes is not None:
                for name in attributes:
                    if isinstance(name, tuple):
                        qname, namespace = name
                        value = attributes[name]
                        self.writer.attribute(qname, value, namespace)
                    else:
                        if u':' in tagName:
                            #If they supplied a prefix, but not a namespace, complain
                            raise TypeError("Prefixed name %s specified without namespace.  Namespace should be provided by using the attribute name form (<qualified-name>, <namespace>)."%(name))
                        value = attributes[name]
                        self.writer.attribute(name, value)
            for subobj in obj.content:
                self.feed(subobj)
            self.writer.endElement(name, ns)
            
class E(object):
    def __init__(self, name, attributes=None, content=None):
        self.name = name
        self.attributes = attributes
        self.content = content
        if not isinstance(attributes, dict) and not content:
            #Then attributes were omitted, but we do have content
            self.attributes = None
            self.content = attributes

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

