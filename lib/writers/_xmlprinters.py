########################################################################
# amara/writers/_xmlprinters.py
"""
This module supports document serialization in XML syntax.
"""

import itertools

from amara import tree
from amara.writers import _xmlstream
from amara.namespaces import NULL_NAMESPACE, XML_NAMESPACE, XMLNS_NAMESPACE

__all__ = ('xmlprinter', 'xmlprettyprinter', "BASIC", "EXCLUSIVE")

BASIC = "BASIC"
EXCLUSIVE = "EXCLUSIVE"

class xmlprinter(object):
    """
    An `xmlprinter` instance provides functions for serializing an XML or
    XML-like document to a stream, based on SAX-like event calls
    initiated by a _Visitor instance.

    The methods in this base class attempt to emit a well-formed parsed
    general entity conformant to XML 1.0 syntax, with no extra
    whitespace added for visual formatting. Subclasses may emit
    documents conformant to other syntax specifications or with
    additional whitespace for indenting.

    The degree of well-formedness of the output depends on the data
    supplied in the event calls; no checks are done for conditions that
    would result in syntax errors, such as two attributes with the same
    name, "--" in a comment, etc. However, attribute() will do nothing
    if the previous event was not startElement(), thus preventing
    spurious attribute serializations.

    `canonical_form` must be None, BASIC or EXCLUSIVE
    It controls c14n of the serialization, according to
    http://www.w3.org/TR/xml-c14n ("basic") or
    http://www.w3.org/TR/xml-exc-c14n/ ("exclusive")
    """
    _canonical_form = None

    def __init__(self, stream, encoding):
        """
        `stream` must be a file-like object open for writing binary
        data. `encoding` specifies the encoding which is to be used for
        writing to the stream.
        """
        self.stream = xs = _xmlstream.xmlstream(stream, encoding)
        self.encoding = encoding
        self.write_ascii = xs.write_ascii
        self.write_encode = xs.write_encode
        self.write_escape = xs.write_escape
        self._element_name = None
        self.omit_declaration = False

    def start_document(self, version='1.0', standalone=None):
        """
        Handles a startDocument event.

        Writes XML declaration or text declaration to the stream.
        """
        if not self.omit_declaration:
            self.write_ascii('<?xml version="%s" encoding="%s"' % (version,
                                                                   self.encoding))
            if standalone is not None:
                self.write_ascii(' standalone="%s"' % standalone)
            self.write_ascii('?>\n')
        return

    def end_document(self):
        """
        Handles an endDocument event.

        Writes any necessary final output to the stream.
        """
        if self._element_name:
            if self._canonical_form:
                self.write_ascii('</')
                self.write_encode(self._element_name, 'end-tag name')
                self.write_ascii('>')
            else:
                # No element content, use minimized form
                self.write_ascii('/>')
            self._element_name = None
        return

    def doctype(self, name, publicid, systemid):
        """
        Handles a doctype event.

        Writes a document type declaration to the stream.
        """
        if self._canonical_form:
            return
        if self._element_name:
            self.write_ascii('>')
            self._element_name = None
        if publicid and systemid:
            self.write_ascii('<!DOCTYPE ')
            self.write_encode(name, 'document type name')
            self.write_ascii(' PUBLIC "')
            self.write_encode(publicid, 'document type public-id')
            self.write_ascii('" "')
            self.write_encode(systemid, 'document type system-id')
            self.write_ascii('">\n')
        elif systemid:
            self.write_ascii('<!DOCTYPE ')
            self.write_encode(name, 'document type name')
            self.write_ascii(' SYSTEM "')
            self.write_encode(systemid, 'document type system-id')
            self.write_ascii('">\n')
        return

    def start_element(self, namespace, name, nsdecls, attributes):
        """
        Handles a start-tag event.

        Writes part of an element's start-tag or empty-element tag to
        the stream, and closes the start tag of the previous element,
        if one remained open. Writes the xmlns attributes for the given
        sequence of prefix/namespace-uri pairs, and invokes attribute() as
        neeeded to write the given sequence of attribute qname/value pairs.

        Note, the `namespace` argument is ignored in this class.
        """
        write_ascii, write_escape, write_encode = (
            self.write_ascii, self.write_escape, self.write_encode)

        if self._element_name:
            # Close current start tag
            write_ascii('>')
        self._element_name = name

        write_ascii('<')
        write_encode(name, 'start-tag name')

        if self._canonical_form:
            # Create the namespace "attributes"
            namespace_attrs = [ (prefix and u'xmlns:' + prefix or u'xmlns', uri)
                           for prefix, uri in nsdecls
                          ]
            namespace_attrs.sort()
            # Write the namespaces decls, in alphabetical order of prefixes, with
            # the default coming first (easy since None comes before any actual
            # Unicode value)
            #sorted_attributes = [ name, value for (name, value) in sorted(attributes) ]
            sorted_attributes = sorted(attributes)
            #FIXME: attributes must be sorted using nsuri / local combo (where nsuri is "" for null namespace)
            for name, value in namespace_attrs:
                #FIXME: check there are no redundant NSDecls
                write_ascii(' ')
                write_encode(name, 'attribute name')
                # Replace characters illegal in attribute values and wrap
                # the value with quotes (") in accordance with Canonical XML.
                write_ascii('="')
                write_escape(value, self._attr_entities_quot)
                write_ascii('"')
            for name, value in sorted_attributes:
                write_ascii(' ')
                write_encode(name, 'attribute name')
                # Replace characters illegal in attribute values and wrap
                # the value with quotes (") in accordance with Canonical XML.
                write_ascii('="')
                write_escape(value, self._attr_entities_quot)
                write_ascii('"')
            
        else:
            # Create the namespace "attributes"
            nsdecls = [ (prefix and u'xmlns:' + prefix or u'xmlns', uri)
                           for prefix, uri in nsdecls
                          ]
            # Merge the namespace and attribute sequences for output
            attributes = itertools.chain(nsdecls, attributes)
            for name, value in attributes:
                # Writes an attribute to the stream as a space followed by
                # the name, '=', and quote-delimited value. It is the caller's
                # responsibility to ensure that this is called in the correct
                # context, if well-formed output is desired.

                # Preference is given to quotes (") around attribute values,
                # in accordance with the DomWriter interface in DOM Level 3
                # Load and Save (25 July 2002 WD), although a value that
                # contains quotes but no apostrophes will be delimited by
                # apostrophes (') instead.
                write_ascii(" ")
                write_encode(name, 'attribute name')
                # Special case for HTML boolean attributes (just a name)
                if value is not None:
                    # Replace characters illegal in attribute values and wrap
                    # the value with appropriate quoting in accordance with
                    # DOM Level 3 Load and Save:
                    # 1. Attributes not containing quotes are serialized in
                    #    quotes.
                    # 2. Attributes containing quotes but no apostrophes are
                    #    serialized in apostrophes.
                    # 3. Attributes containing both forms of quotes are
                    #    serialized in quotes, with quotes within the value
                    #    represented by the predefined entity `&quot;`.
                    if '"' in value and "'" not in value:
                        # Use apostrophes (#2)
                        entitymap = self._attr_entities_apos
                        quote = "'"
                    else:
                        # Use quotes (#1 and #3)
                        entitymap = self._attr_entities_quot
                        quote = '"'
                    write_ascii("=")
                    write_ascii(quote)
                    write_escape(value, entitymap)
                    write_ascii(quote)
        return

    def end_element(self, namespace, name):
        """
        Handles an end-tag event.

        Writes the closing tag for an element to the stream, or, if the
        element had no content, finishes writing the empty element tag.

        Note, the `namespace` argument is ignored in this class.
        """
        if self._element_name:
            self._element_name = None
            if self._canonical_form:
                self.write_ascii('>')
            else:    
                # No element content, use minimized form
                self.write_ascii('/>')
                return
        self.write_ascii('</')
        self.write_encode(name, 'end-tag name')
        self.write_ascii('>')
        return

    def text(self, text, disable_escaping=False):
        """
        Handles a text event.

        Writes character data to the stream. If the `disable_escaping` flag
        is not set, then unencodable characters are replaced with
        numeric character references; "&" and "<" are escaped as "&amp;"
        and "&lt;"; and ">" is escaped as "&gt;" if it is preceded by
        "]]". If the `disable_escaping` flag is set, then the characters
        are written to the stream with no escaping of any kind, which
        will result in an exception if there are unencodable characters.
        """
        if self._canonical_form:
            text.replace(u'\r\n', u'\r')
        
        if self._element_name:
            self.write_ascii('>')
            self._element_name = None

        if disable_escaping:
            # Try to write the raw encoded string (may throw exception)
            self.write_encode(text, 'text')
        else:
            # FIXME: only escape ">" if after "]]"
            # (may not be worth the trouble)
            self.write_escape(text, self._text_entities)
        return

    def cdata_section(self, data):
        """
        Handles a cdataSection event.

        Writes character data to the stream as a CDATA section.
        """
        if self._element_name:
            self.write_ascii('>')
            self._element_name = None

        if self._canonical_form:
            #No CDATA sections in c14n
            text.replace(u'\r\n', u'\r')
            self.write_escape(data, self._text_entities)
        else:
            sections = data.split(u']]>')
            self.write_ascii('<![CDATA[')
            self.write_encode(sections[0], 'CDATA section')
            for section in sections[1:]:
                self.write_ascii(']]]]><![CDATA[>')
                self.write_encode(section, 'CDATA section')
            self.write_ascii(']]>')
        return

    def processing_instruction(self, target, data):
        """
        Handles a processingInstruction event.

        Writes a processing instruction to the stream.
        """
        if self._element_name:
            self.write_ascii('>')
            self._element_name = None

        self.write_ascii('<?')
        self.write_encode(target, 'processing instruction target')
        if data:
            self.write_ascii(' ')
            self.write_encode(data, 'processing instruction data')
        self.write_ascii('?>')
        return

    def comment(self, data):
        """
        Handles a comment event.

        Writes a comment to the stream.
        """
        if self._element_name:
            self.write_ascii('>')
            self._element_name = None

        self.write_ascii("<!--")
        self.write_encode(data, 'comment')
        self.write_ascii("-->")
        return

    # Entities as defined by Canonical XML 1.0 (http://www.w3.org/TR/xml-c14n)
    # For XML 1.1, add u'\u0085': '&#133;' and u'\u2028': '&#8232;' to all
    _text_entities = _xmlstream.entitymap({'<' : '&lt;',
                                           '>' : '&gt;',
                                           '&' : '&amp;',
                                           '\r' : '&#13;',
                                           })

    _attr_entities_quot = _xmlstream.entitymap({'<' : '&lt;',
                                                '&' : '&amp;',
                                                '\t' : '&#9;',
                                                '\n' : '&#10;',
                                                '\r' : '&#13;',
                                                '"' : '&quot;',
                                                })

    _attr_entities_apos = _xmlstream.entitymap({'<' : '&lt;',
                                                '&' : '&amp;',
                                                '\t' : '&#9;',
                                                '\n' : '&#10;',
                                                '\r' : '&#13;',
                                                "'" : '&apos;',
                                                })


class canonicalxmlprinter(xmlprinter):
    """
    `canonicalxmlprinter` emits only c14n XML:
      http://www.ibm.com/developerworks/xml/library/x-c14n/
      http://www.w3.org/TR/xml-c14n
    Does not yet:
      * Normalize all attribute values
      * Specify all default attributes
    Note: this class is fully compatible with exclusive c14n:
      http://www.w3.org/TR/xml-exc-c14n/
    whether or not the operation is exclusive depends on preprocessing
    operations appplied by the caller.
    """
    # Enable canonical-form output.
    _canonical_form = True

    #FIXME: A bit inelegant to require the encoding, then throw it away.  Perhaps
    #we should at least issue a warning if they send a non-UTF8 encoding
    def __init__(self, stream, encoding):
        """
        `stream` must be a file-like object open for writing binary
        data.
        """
        xmlprinter.__init__(self, stream, 'utf-8')
        self.omit_declaration = True

    def prepare(self, node, kwargs):
        """
        `inclusive_prefixes` is a list (or None) of namespaces representing the
        "InclusiveNamespacesPrefixList" list in exclusive c14n.
        It may only be a non-empty list if `canonical_form` == EXCLUSIVE
        """
        exclusive = kwargs.get("exclusive", False)
        nshints = kwargs.get("nshints", {})
        inclusive_prefixes = kwargs.get("inclusive_prefixes", [])
        added_attributes = {}  #All the contents should be XML NS attrs
        if not exclusive:
            #Roll in ancestral xml:* attributes
            parent_xml_attrs = node.xml_select(u'ancestor::*/@xml:*')
            for attr in parent_xml_attrs:
                aname = (attr.xml_namespace, attr.xml_qname)
                if (aname not in added_attributes
                    and aname not in node.xml_attributes):
                    added_attributes[attr.xml_qname] = attr.xml_value
        nsnodes = node.xml_select('namespace::*')
        inclusive_prefixes = inclusive_prefixes or []
        if u'#default' in inclusive_prefixes:
            inclusive_prefixes.remove(u'#default')
            inclusive_prefixes.append(u'')
        decls_to_remove = []
        if exclusive:
            used_prefixes = [ n.xml_prefix for n in node.xml_select('self::*|@*') ]
            declared_prefixes = []
            for ans, anodename in node.xml_attributes:
                if ans == XMLNS_NAMESPACE:
                    attr = node.xml_attributes[ans, anodename]
                    prefix = attr.xml_local
                    declared_prefixes.append(prefix)
                    #print attr.prefix, attr.localName, attr.nodeName
                    if attr.xml_local not in used_prefixes:
                        decls_to_remove.append(prefix)
            #for prefix in used_prefixes:
            #    if prefix not in declared_prefixes:
            #        nshints[ns.nodeName] = ns.value
        #Roll in ancestral  NS nodes
        for ns in nsnodes:
            #prefix = ns.xml_qname if isinstance(ns, tree.namespace) else ns.xml_qname
            #print (ns.xml_name, ns.xml_value)
            prefix = ns.xml_name
            if (ns.xml_value != XML_NAMESPACE
                and ns.xml_name not in node.xml_namespaces
                and (not exclusive or ns.xml_name in inclusivePrefixes)):
                #added_attributes[(XMLNS_NAMESPACE, ns.nodeName)] = ns.value
                nshints[prefix] = ns.xml_value
            elif (exclusive
                  and prefix in used_prefixes
                  and prefix not in declared_prefixes):
                nshints[prefix] = ns.xml_value
        kwargs["nshints"] = nshints
        if "inclusive_prefixes" in kwargs: del kwargs["inclusive_prefixes"]
        if "exclusive" in kwargs: del kwargs["exclusive"]
        if "nshints" in kwargs: del kwargs["nshints"]
        #FIXME: nshints not yet actually used.  Required for c14n of nodes below the top-level
        self._nshints = nshints or {}
        return kwargs
    

class xmlprettyprinter(xmlprinter):
    """
    An xmlprettyprinter instance provides functions for serializing an
    XML or XML-like document to a stream, based on SAX-like event calls.

    The methods in this subclass of xmlprinter produce the same output
    as the base class, but with extra whitespace added for visual
    formatting. The indent attribute is the string used for each level
    of indenting. It defaults to 2 spaces.
    """

    # The amount of indent for each level of nesting
    indent = '  '

    def __init__(self, stream, encoding):
        xmlprinter.__init__(self, stream, encoding)
        self._level = 0
        self._can_indent = False  # don't indent first element

    def start_element(self, namespace, name, namespaces, attributes):
        if self._element_name:
            self.write_ascii('>')
            self._element_name = None
        if self._can_indent:
            self.write_ascii('\n' + (self.indent * self._level))
        xmlprinter.start_element(self, namespace, name, namespaces,
                                 attributes)
        self._level += 1
        self._can_indent = True
        return

    def end_element(self, namespace, name):
        self._level -= 1
        # Do not break short tag form (<tag/>)
        if self._can_indent and not self._element_name:
            self.write_ascii('\n' + (self.indent * self._level))
        xmlprinter.end_element(self, namespace, name)
        # Allow indenting after endtags
        self._can_indent = True
        return

    def text(self, data, disable_escaping=False):
        xmlprinter.text(self, data, disable_escaping)
        # Do not allow indenting for elements with mixed content
        self._can_indent = False
        return

    def cdata_section(self, data):
        xmlprinter.cdata_section(self, data)
        # Do not allow indenting for elements with mixed content
        self._can_indent = False
        return

    def processing_instruction(self, target, data):
        if self._element_name:
            self.write_ascii('>')
            self._element_name = None
        if self._can_indent:
            self.write_ascii('\n' + (self.indent * self._level))
        xmlprinter.processing_instruction(self, target, data)
        # Allow indenting after processing instructions
        self._can_indent = True
        return

    def comment(self, data):
        if self._element_name:
            self.write_ascii('>')
            self._element_name = None
        if self._can_indent:
            self.write_ascii('\n' + (self.indent * self._level))
        xmlprinter.comment(self, data)
        # Allow indenting after comments
        self._can_indent = True
        return
