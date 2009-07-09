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
import amara
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
        printer = _htmlprinters.htmlprinter(stream, encoding)
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
        if isinstance(obj, RAW):
            doc = amara.parse(obj.content)
            from amara.writers._treevisitor import visitor
            v = visitor(printer=self.printer)
            for child in doc.xml_children:
                v.visit(child)
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
                self.attributes[ns, qname] = qname, U(value)

class NS(object):
    def __init__(self, prefix, namespace):
        self.prefix = prefix
        self.namespace = namespace

class RAW(object):
    '''
    >>> from amara.writers.struct import *
    >>> w = structwriter(indent=u"yes").feed(ROOT(
      E((u'urn:x-bogus1', u'n:a'), {(u'urn:x-bogus1', u'n:x'): u'1'},
        E((u'urn:x-bogus2', u'b'), u'c'), RAW(u'<test />')
      )))
    
    '''
    def __init__(self, *content):
        #Eventually use incremental parse and feed()
        self.content = ''.join(content)

class ROOT(object):
    def __init__(self, *content):
        self.content = content

