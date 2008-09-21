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
from amara import tree
from amara.writers import WriterError
from amara import XML_NAMESPACE
from amara.lib.xmlstring import *
import _xmlprinters, _htmlprinters

UNSPECIFIED_NAMESPACE = u":"

__all__ = ['structwriter', 'E', 'NS', 'ROOT', 'RAW']

class StructWriterError(WriterError):

    ATTRIBUTE_ADDED_TOO_LATE = 1
    ATTRIBUTE_ADDED_TO_NON_ELEMENT = 2


def get_printer(stream, encoding='utf-8', ns_hints=None, is_html=False,
             indent=False, canonical=False, added_attributes=None,
             removed_ns_decls=None):
    """
    Initializes an instance of the class, selecting the appropriate
    printer to use, depending on the isHtml and indent flags.
    ns_hints, if given, is a dictionary of namespace mappings that
    help determine if namespace declarations need to be emitted when
    visiting the first Element node.
    """
    if indent and is_html:
        printer = _htmlprinters.htmlprettyprinter(stream, encoding)
    elif indent:
        printer = _xmlprinters.xmlprettyprinter(stream, encoding)
    elif is_html:
        printer = _htmlprinters.htmlprinters(stream, encoding)
    elif canonical:
        printer = _xmlprinters.CanonicalXmlPrinter(stream, encoding)
    else:
        printer = _xmlprinters.xmlprinter(stream, encoding)
    return printer

class structwriter(object):
    def __init__(self, stream=sys.stdout, **kwargs):
        #writer - instance of `amara.writers.writer`, or None to create a default instance
        """
        """
        #self.printer = writer or xmlwriter()
        self.printer = get_printer(stream, **kwargs)

    def feed(self, obj, prefixes=None):
        """
        obj - an object or iterator of objects matching the structwriter's specifications
        """
        prefixes = prefixes or {}
        if isinstance(obj, ROOT):
            self.printer.start_document()
            for subobj in obj.content:
                self.feed(subobj)
            self.printer.end_document()
            return
        if isinstance(obj, NS):
            return
        if isinstance(obj, E):
            #First attempt used tee.  Seems we ran into the warning at http://www.python.org/doc/2.4.3/whatsnew/node13.html
            #"Note that tee() has to keep copies of the values returned by the iterator; in the worst case, it may need to keep all of them. This should therefore be used carefully if the leading iterator can run far ahead of the trailing iterator in a long stream of inputs. If the separation is large, then you might as well use list() instead. When the iterators track closely with one another, tee()" is ideal. Possible applications include bookmarking, windowing, or lookahead iterators. (Contributed by Raymond Hettinger.)"
            #obj.namespaces = {}
            new_prefixes = []
            lead = None
            content = iter(obj.content)
            for subobj in content:
                if isinstance(subobj, NS):
                    new_prefixes.append((subobj.prefix, subobj.namespace))
                else:
                    lead = subobj
                    break

            prefix, local = splitqname(obj.qname)
            prefix = prefix or u''
            if obj.ns == UNSPECIFIED_NAMESPACE:
                obj.ns = prefixes.get(prefix, u'')
            elif prefix not in prefixes or prefixes[prefix] != obj.ns:
                new_prefixes.append((prefix, obj.ns or u''))
            attrs = [ a for a in obj.attributes.itervalues() ] if obj.attributes else ()
            if new_prefixes:
                prefixes = prefixes.copy()
                prefixes.update(dict(new_prefixes))
            self.printer.start_element(obj.ns, obj.qname, new_prefixes, attrs)
            if lead:
                self.feed(lead, prefixes)
                for subobj in content:
                    self.feed(subobj, prefixes)
            self.printer.end_element(obj.ns, obj.qname)
            return
        if isinstance(obj, basestring):
            self.printer.text(U(obj))
            return
        if isinstance(obj, tree.element):
            #Be smart about bindery nodes
            self.printer.text(unicode(obj))
            return
        try:
            obj = iter(obj)
        except TypeError, e:
            if callable(obj):
                self.feed(obj(), prefixes)
            else:
                #Just try to make it text, i.e. punt
                self.feed(unicode(obj), prefixes)
        else:
            for subobj in obj:
                self.feed(subobj, prefixes)

class E(object):
    def __init__(self, name, *items):
        if isinstance(name, tuple):
            self.ns, self.qname = imap(U, name)
        else:
            self.ns, self.qname = UNSPECIFIED_NAMESPACE, U(name)
        if items and isinstance(items[0], dict):
            attributes = items[0]
            self.content = items[1:]
        else:
            self.content = items
            attributes = None
        #XXX: Move to dictionary set expr in 2.6 or 3.0
        self.attributes = None
        if attributes:
            self.attributes = {}
            for name, value in attributes.iteritems():
                if isinstance(name, tuple):
                    ns, qname = imap(U, name)
                else:
                    ns, qname = None, U(name)
                #Unicode value coercion to help make it a bit smarter
                self.attributes[ns, qname] = qname, unicode(value)

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

