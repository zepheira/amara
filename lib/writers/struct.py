# -*- encoding: utf-8 -*-
# 
# amara.writers.struct
# © 2008, 2009 by Uche Ogbuji and Zepheira LLC
#
"""
XML/HTML writers (serializers) that work on Python objects that proxy
XML structure (similar to, but simpler and more and directly geared to
serialization than amara.tree and bindery nodes).

Based on an old idea for a friendly markup serialization interface, with a hat-tip
to pyfo ( http://foss.cpcc.edu/pyfo/ )

Note: this module has some departures from the reguler PEP 8 naming convention
for considered reasons of clarity in use
"""

import sys
from itertools import *
import amara
from amara.lib.util import coroutine
from amara import tree
from amara.writers import WriterError
from amara import XML_NAMESPACE
from amara.lib.xmlstring import *
import _xmlprinters, _htmlprinters

UNSPECIFIED_NAMESPACE = u":"

__all__ = ['structwriter', 'structencoder', 'E', 'NS', 'ROOT', 'RAW', 'E_CURSOR']

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
    """
    XML/HTML writer (serializer) that works on Python objects that proxy
    XML structure (similar to, but simpler and more and directly geared to
    serialization than amara.tree and bindery nodes).  Writes the serialized
    result to an output stream (sys.stdout by default).
    
    Usage examples:
    
    from amara.writers.struct import structwriter, E, NS, ROOT, RAW
    output = structwriter(indent=u"yes")
    output.feed(
    ROOT(
      E(u'a', (E(u'b', unicode(i)) for i in range(10)))
    ))

    Using namespaces:

    from amara.writers.struct import structwriter, E, NS, ROOT, RAW
    from amara.namespaces import ATOM_NAMESPACE
    output = structwriter(stream=open("spam.xml"), indent=u"yes")
    output.feed(
    ROOT(
      E((ATOM_NAMESPACE, u'entry'),
        E((ATOM_NAMESPACE, u'id'), u'urn:bogus:x'),
        E((ATOM_NAMESPACE, u'title'), u'Hello world'),
        E((ATOM_NAMESPACE, u'link'), {u'href': u'http://example.org'}),
      )
    ))

    Using coroutine mode, and a cursor:
    
    from amara.writers.struct import structwriter, E, NS, ROOT, RAW, E_CURSOR
    output = structwriter()
    f = output.cofeed(ROOT(E(u'a', E_CURSOR(u'b', {u'attr1': u'val1'}))))
    f.send(E(u'c', u'1'))
    f.send(E(u'c', u'2'))
    f.send(E(u'c', u'3'))
    f.close()
    
    Output:
    
    <?xml version="1.0" encoding="utf-8"?>
    <a><b attr1="val1"><c>1</c><c>2</c><c>3</c></b></a>
    
    See documentation for more extensive examples.
    
    """
    def __init__(self, stream=sys.stdout, **kwargs):
        #self.printer = writer or xmlwriter()
        self.printer = get_printer(stream, **kwargs)

    def feed(self, obj, prefixes=None):
        """
        Feed a structure to the writer.  The structure is interpreted as XML and
        serialized.
        
        obj - XML node proxy structure (or iterator thereof), such as
        amara.writers.struct.ROOT (proxy for a root (entity) node) or
        amara.writers.struct.E (proxy for an element).

        See documentation for other proxy node classes
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
            #First attempt used tee.  Seems we ran into the warning at
            #http://www.python.org/doc/2.4.3/whatsnew/node13.html
            #"Note that tee() has to keep copies of the values returned by the iterator;
            #in the worst case, it may need to keep all of them.
            #This should therefore be used carefully if the leading iterator can run
            #far ahead of the trailing iterator in a long stream of inputs.
            #If the separation is large, then you might as well use list() instead.
            #When the iterators track closely with one another, tee()" is ideal. Possible
            #applications include bookmarking, windowing, or lookahead iterators.
            #(Contributed by Raymond Hettinger.)"
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
        return

    @coroutine
    def cofeed(self, obj, prefixes=None):
        """
        Feed a structure to the writer, including a cursor.  The structure is
        interpreted as XML and serialized.  The initially fed structure becomes
        the outer envelope of the serialized XML, and then the operation is
        suspended (this method engenders a coroutine).  The user can then send additional
        substructures to the coroutine, which get serialized at the point of the cursor,
        until the user closes the coroutine, at which point the serialization is
        completed.
        
        obj - XML node proxy structure (or iterator thereof), such as
        amara.writers.struct.ROOT (proxy for a root (entity) node),
        amara.writers.struct.E (proxy for an element), or
        amara.writers.struct.E_CURSOR (proxy for a cursor element, whose children
        are then later provided by sending proxy nodes to the coroutine).
        See documentation for other proxy node classes
        """
        #This method is largely a dupe of feed, but rather than calling self.feed to
        #recursively deal with compound structures, it sets up a child coroutine
        #and forwards values sent by the parent.  There is a lot of inelegant
        #duplication because we often can't tidy things up with functions without
        #Breaking the character of cofeed as a coroutine
        #this is one are where Python could very much use cpp-style macros
        #FIXME.  There is some inelegant duplication that might well be refatcored
        #away, even without the benefit of cpp-style macros
        prefixes = prefixes or {}
        if isinstance(obj, ROOT):
            self.printer.start_document()
            for subobj in obj.content:
                try:
                    buf = self.cofeed(subobj, prefixes=None)
                    try:
                        while True:
                            val = (yield)
                            buf.send(val)
                    except GeneratorExit:
                        buf.close()
                except StopIteration:
                    pass
                #self.feed(subobj)
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
        if isinstance(obj, E_CURSOR):
            new_prefixes = []
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

            try:
                buf = obj.do(self)
                while True:
                    val = (yield)
                    buf.send(val)
            except GeneratorExit:
                buf.close()

            self.printer.end_element(obj.ns, obj.qname)
            return
        if isinstance(obj, E):
            #First attempt used tee.  Seems we ran into the warning at
            #http://www.python.org/doc/2.4.3/whatsnew/node13.html
            #"Note that tee() has to keep copies of the values returned by the iterator;
            #in the worst case, it may need to keep all of them.
            #This should therefore be used carefully if the leading iterator can run
            #far ahead of the trailing iterator in a long stream of inputs.
            #If the separation is large, then you might as well use list() instead.
            #When the iterators track closely with one another, tee()" is ideal. Possible
            #applications include bookmarking, windowing, or lookahead iterators.
            #(Contributed by Raymond Hettinger.)"
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
                if isinstance(lead, E_CURSOR) or isinstance(lead, E):
                    try:
                        buf = self.cofeed(lead, prefixes=None)
                        try:
                            while True:
                                val = (yield)
                                buf.send(val)
                        except GeneratorExit:
                            buf.close()
                    except StopIteration:
                        pass
                else:
                    self.feed(lead, prefixes)
                for subobj in content:
                    if isinstance(subobj, E_CURSOR) or isinstance(subobj, E):
                        try:
                            buf = self.cofeed(subobj, prefixes=None)
                            try:
                                while True:
                                    val = (yield)
                                    buf.send(val)
                            except GeneratorExit:
                                buf.close()
                        except StopIteration:
                            pass
                    else:
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
        return


class structencoder(structwriter):
    """
    XML/HTML writer (serializer) that works on Python objects that proxy
    XML structure (similar to, but simpler and more and directly geared to
    serialization than amara.tree and bindery nodes).  Buffers the serialized
    result, for retrieval as a string using the read() method.
    
    Usage examples:
    
    from amara.writers.struct import structencoder, E, NS, ROOT, RAW
    output = structencoder(indent=u"yes")
    output.feed(
    ROOT(
      E(u'a', (E(u'b', unicode(i)) for i in range(10)))
    ))
    print output.read()

    Using namespaces:

    from amara.writers.struct import structencoder, E, NS, ROOT, RAW
    from amara.namespaces import ATOM_NAMESPACE
    output = structencoder(indent=u"yes")
    output.feed(
    ROOT(
      E((ATOM_NAMESPACE, u'entry'),
        E((ATOM_NAMESPACE, u'id'), u'urn:bogus:x'),
        E((ATOM_NAMESPACE, u'title'), u'Hello world'),
        E((ATOM_NAMESPACE, u'link'), {u'href': u'http://example.org'}),
      )
    ))
    print output.read()

    Using coroutine mode, and a cursor:
    
    from amara.writers.struct import structencoder, E, NS, ROOT, RAW, E_CURSOR
    output = structencoder()
    f = output.cofeed(ROOT(E(u'a', E_CURSOR(u'b', {u'attr1': u'val1'}))))
    f.send(E(u'c', u'1'))
    f.send(E(u'c', u'2'))
    f.send(E(u'c', u'3'))
    f.close()
    print output.read()
    
    Outputs:
    
    <?xml version="1.0" encoding="utf-8"?>
    <a><b attr1="val1"><c>1</c><c>2</c><c>3</c></b></a>
    
    See documentation for more extensive examples.
    """
    def __init__(self, **kwargs):
        self.chunks = []
        structwriter.__init__(self, stream=self, **kwargs)

    def write(self, chunk):
        self.chunks.append(chunk)

    def read(self):
        chunks = self.chunks
        self.chunks = []
        return ''.join(chunks)


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


class E_CURSOR(E):
    def __init__(self, name, *items):
        if len(items) > 1:
            #FIXME: L10N
            raise ValueError('E_COROUTINE objects can only be initialized with a name and optional attribute mapping')
        E.__init__(self, name, *items)
        
    @coroutine
    def do(self, sink):
        while True:
            try:
                obj = (yield)
                sink.feed(obj)
            except GeneratorExit:
                break


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

