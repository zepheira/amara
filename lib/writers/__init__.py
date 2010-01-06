# -*- encoding: utf-8 -*-
# 
# amara.writers
# © 2008, 2009 by Uche Ogbuji and Zepheira LLC
#
"""amara.writers

Implements Amara's support for serializing trees as XML, HTML, or XHTML.

Functions for public use:

    lookup(str)          : Returns a printer object for writing DOM elements.
    register(str, class) : Record a printer class for future lookup() calls.

The three most commonly-used names are available as constants: XML_W,
XHTML_W, and HTML_W.

For writing out XML and HTML, use the xml_write() and xml_encode()
methods on Amara node objects.

"""

"""
The writers architecture needs a major overhaul.  It's presently a confusing jumble of
layers with all sorts of inefficiency.

Principles of redesign:

* eliminate writer/printer distinction.  Everything is a writer
* What are now printers become the main code base for the lowest level writers,
  which are really no more than a set of ultra-efficient routines for e.g. character encoding
* Lowest-level writer (a "writerbase" class?) manages no state, and requires a smart caller
  For example it would do nothing about namespace consistenct, and would rely on
  intelligence by the caller
* Higher level writers do try to modularize as much as possible, but with less misuse of OO
  More callbacks & decorators & such

"""


import sys
from amara import Error
from amara.lib.xmlstring import *

__all__ = ['WriterError', 'writer', 'streamwriter',
           'HTML_W', 'XML_W', 'XHTML_W',
           'lookup', 'register', 'xml_print'
          ]

# Constants for the most common writers
HTML_W = 'html'
XML_W = 'xml'
XHTML_W = 'xhtml'

_lookup_table = {}

class WriterError(Error):

    ATTRIBUTE_ADDED_TOO_LATE = 1
    ATTRIBUTE_ADDED_TO_NON_ELEMENT = 2

    @classmethod
    def _load_messages(cls):
        from gettext import gettext as _
        return {
            WriterError.ATTRIBUTE_ADDED_TOO_LATE: _(
                'Children were added to the element'),
            WriterError.ATTRIBUTE_ADDED_TO_NON_ELEMENT: _(
                'Attempted to add attribute to non-element'),
        }

def _init_lookup_table():
    from amara.writers import _xmlprinters, _htmlprinters, _xhtmlprinters

    _lookup_table.update({XML_W: _xmlprinters.xmlprinter, 
                          XML_W + '-indent': _xmlprinters.xmlprettyprinter,
                          XML_W + '-canonical': _xmlprinters.canonicalxmlprinter,
                          HTML_W: _htmlprinters.htmlprinter, 
                          HTML_W + '-indent': _htmlprinters.htmlprettyprinter, 
                          XHTML_W: _xhtmlprinters.xhtmlprinter,
                          XHTML_W + '-indent': _xhtmlprinters.xhtmlprettyprinter,
                          HTML_W + '-nsstrip': _htmlprinters.html_ns_stripper,
                          HTML_W + '-nsstrip-indent': _htmlprinters.html_ns_stripper,
                          })


def lookup(printer_name):
    """(str): Printer class

    Return a printer object for writing DOM elements.

    Currently the following values for 'printer_name' are supported:
      xml html xhtml
    """
    if not _lookup_table:
        _init_lookup_table()

    if printer_name in _lookup_table:
        return _lookup_table[printer_name]
    else:
        raise ValueError("Unknown printer class %r" % printer_name)

def register(printer_name, printer_class):
    """(str, class)

    Record a printer class so that future calls to lookup() will
    return it.

    """
    if not _lookup_table:
        _init_lookup_table()

    if printer_name in _lookup_table:
        raise ValueError("Already a printer registered for name %r"
                         % printer_name)
    _lookup_table[printer_name] = printer_class


def _xml_write(N, writer=XML_W, stream=None, encoding='UTF-8', **kwargs):
    """(node, file, str, class): None

    INTERNAL function.

    Serializes an XML tree, writing it to the specified 'stream' object.
    """
    from amara.writers import node
    if isinstance(writer, str):
        writer_class = lookup(writer)
    else:
        # Assume provided writer is a writer class
        writer_class = writer

    if stream is None:
        import sys
        stream = sys.stdout

    writer = writer_class(stream, encoding)
    if hasattr(writer, "prepare"):
        #Do any writer-specific massaging of the arguments,
        #for example applying exclusive c14n rules
        kwargs = writer.prepare(N, kwargs)

    v = node._Visitor(writer, **kwargs)
    v.visit(N)

def _xml_encode(N, writer=XML_W, encoding='UTF-8', **kwargs):
    """(node, Writer): None
    """
    import cStringIO
    stream = cStringIO.StringIO()
    _xml_write(N, writer, stream, encoding, **kwargs)
    return stream.getvalue()


# Backward-compatibility alias
#FIXME: Remove this function when amara goes beta
def xml_print(root, stream=None, encoding='UTF-8', **kwargs):
    import warnings
    warnings.warn("xml_print() function is deprecated; use xml_write() or xml_encode() method instead")
    _xml_write(root, XML_W, stream, encoding)


class writer(object):
    # Note, any changes to __slots__ require a change in treewriter.c as well
    __slots__ = ('output_parameters',)

    def __init__(self, output_parameters):
        self.output_parameters = output_parameters

    def get_result(self):
        return None

    def start_document(self):
        """
        Called once at the beginning of output writing.
        """
        return

    def end_document(self):
        """
        Called once at the end of output writing.
        """
        return

    def start_element(self, name, namespace=None, namespaces=None,
                      attributes=None):
        """
        Called when an element node is generated in the result tree.
        Subsequent method calls generate the element's attributes and content.

        name - the local name.
        namespace - the namespace URI.
        namespaces - new namespace bindings (dictionary of prefixes to URIs)
                     established by this element.
        attributes - mapping of qualified-name to attribute-value
        """
        return

    def end_element(self, name, namespace=None):
        """
        Called at the end of element node generation.

        name - the local name.
        namespace - the namespace URI.
        """
        return

    def namespace(self, prefix, namespace):
        """
        Called when a namespace node is explicitly generated in the result tree
        (as by the xsl:namespace instruction).

        prefix - the prefix.
        namespace - the namespace URI.
        """
        return

    def attribute(self, name, value, namespace=None):
        """
        Called when an attribute node is generated in the result tree.

        name - the local name.
        value - the attribute value.
        namespace - the namespace URI.
        """
        return

    def text(self, data, disable_escaping=False):
        """
        Called when a text node is generated in the result tree.

        data - content of the text node
        disable_escaping - if true, no escaping of characters is performed
        """
        return

    def processing_instruction(self, target, data):
        """
        Called when an processing instruction node is generated in the result tree.

        target - the instruction target.
        data - the instruction.
        """
        return

    def comment(self, body):
        """
        Called when a comment node is generated in the result tree.

        body - comment text.
        """
        return


class streamwriter(writer):

    def __init__(self, output_parameters, stream):
        """
        output_parameters - instance of
                            `amara.writers.outputparameters.outputparameters`
        stream - a stream that takes a byte stream (not a unicode object)
        """
        self.output_parameters = output_parameters
        self.stream = stream


class _userwriter(object):
    def start_element(self, name, namespace=None, namespaces=None,
                      attributes=None):
        """
        Create a start tag with optional attributes.  Must eventually
        be matched with an endElement call
        
        Note: all "strings" in these parameters must be unicode objects
        name - qualified name of the element (must be unicode)
        namespace - optional namespace URI
        attributes - optional dictionary mapping name to unicode value
                    the name can either be a unicode QName or a tuple
                    of (QName, namespace URI)
        namespaces - optional dictionary (defaults to an empty one) that
                   creates additional namespace declarations that the
                   user wants to place on the specific element. Each key
                   is a ns prefix, and each value a ns name (URI).
                   You do not need to use extraNss if you will be using
                   a similar namespace parameter.  In fact, most people
                   will never need this parameter.
        """
        name = U(name)
        normalized_attrs = {}
        if attributes is not None:
            normalized_attrs = dict((
                (((U(aname[0]), U(aname[1])), U(value))
                    if isinstance(aname, tuple) else ((U(aname), None), U(value)))
                for (aname, value) in attributes.iteritems()
            ))
        #Be careful, viz. http://fuhm.net/super-harmful/ but should be safe here
        super(_userwriter, self).start_element(name, namespace, namespaces, normalized_attrs)
        return

    def simple_element(self, name, namespace=None, namespaces=None,
                      attributes=None, content=u""):
        """
        Create a simple tag with optional attributes and content.  The
        complete element, start tag, optional text content, end tag, will
        all be generated by this one call.  Must *not* be matched with
        an endElement call.

        Note: all "strings" in these parameters must be unicode objects
        tagName - qualified name of the element
        namespace - optional namespace URI
        attributes - optional dictionary mapping name to unicode value
                    the name can either be a unicode QName or a tuple
                    of (QName, namespace URI)
        content   - optional unicode object with the text body of the
                    simple element
        namespaces - optional dictionary (defaults to an empty one) that
                   creates additional namespace declarations that the
                   user wants to place on the specific element. Each key
                   is a ns prefix, and each value a ns name (URI).
                   You do not need to use namespaces if you will be using
                   a similar namespace parameter.  In fact, most people
                   will never need this parameter.
        """
        if name.startswith('xml:'):
            #We can use such a raw test because of the very special case
            #nature of the XML prefix
            namespace = XML_NAMESPACE
        self.start_element(name, namespace, namespaces, attributes)
        if content:
            self.text(U(content))
        self.end_element(name, namespace)
        return

    def xml_fragment(self, fragment):
        """
        Incorporate a well-formed general entity into the output.
        fragment of
        fragment - string (must not be a Unicode object) to be incorporated
                   verbatim into the output, after testing for wellp-formedness
        """
        raise NotImplementedErr
