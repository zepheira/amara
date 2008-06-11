########################################################################
# amara/writers/_xmlprinters.py
"""
This module supports document serialization in XML syntax.
"""

import re
from amara import XML_NAMESPACE
from amara._xmlstring import SplitQName
from amara.writers import _xmlstream

class xmlprinter:
    """
    An `xmlprinter` instance provides functions for serializing an XML or
    XML-like document to a stream, based on SAX-like event calls
    initiated by an Ft.Xml.Lib.Print.PrintVisitor instance.

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
    """

    def __init__(self, stream, encoding, byte_order_mark=None,
                 canonical_form=None):
        """
        `stream` must be a file-like object open for writing binary
        data. `encoding` specifies the encoding which is to be used for
        writing to the stream.
        """
        self.stream = xs = _xmlstream.xmlstream(stream, encoding,
                                                #byte_order_mark
                                                )
        self.encoding = encoding
        self.write_ascii = xs.write_ascii
        self.write_encode = xs.write_encode
        self.write_escape = xs.write_escape
        self._canonical_form = canonical_form
        self._element_name = None
        return

    def start_document(self, version='1.0', standalone=None):
        """
        Handles a startDocument event.

        Writes XML declaration or text declaration to the stream.
        """
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
                # No element content, use minimized form
                self.write_ascii('/>')
            else:
                self.write_ascii('</')
                self.write_encode(self._element_name, 'end-tag name')
                self.write_ascii('>')
            self._element_name = None
        return

    def doctype(self, name, publicid, systemid):
        """
        Handles a doctype event.

        Writes a document type declaration to the stream.
        """
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

    def start_element(self, namespace, name, namespaces, attributes):
        """
        Handles a start-tag event.

        Writes part of an element's start-tag or empty-element tag to
        the stream, and closes the start tag of the previous element,
        if one remained open. Writes the xmlns attributes for the given
        sequence of prefix/namespace-uri pairs, and invokes attribute() as
        neeeded to write the given sequence of attribute name/value pairs.

        Note, the `namespace` argument is ignored in this class.
        """
        if self._element_name:
            # Close current start tag
            self.write_ascii('>')
        self._element_name = name

        self.write_ascii('<')
        self.write_encode(name, 'start-tag name')

        # Write the namespaces
        for prefix, uri in namespaces:
            if prefix:
                self.attribute(namespace, name, u"xmlns:"+prefix, uri)
            else:
                self.attribute(namespace, name, u"xmlns", uri)

        # Now the attributes
        for attr, value in attributes:
            self.attribute(namespace, name, attr, value)
        return

    def end_element(self, namespace, name):
        """
        Handles an end-tag event.

        Writes the closing tag for an element to the stream, or, if the
        element had no content, finishes writing the empty element tag.

        Note, the `namespace` argument is ignored in this class.
        """
        if self._element_name:
            if self._canonical_form:
                # No element content, use minimized form
                self.write_ascii('/>')
                return
            self._element_name = None
        self.write_ascii('</')
        self.write_encode(name, 'end-tag name')
        self.write_ascii('>')
        return

    # elementUri and elementName are only needed for HTML output
    def attribute(self, element_namespace, element_name, name, value):
        """
        Handles an attribute event.

        Writes an attribute to the stream as a space followed by
        the name, '=', and quote-delimited value. It is the caller's
        responsibility to ensure that this is called in the correct
        context, if well-formed output is desired.

        Preference is given to quotes (\") around attribute values, in
        accordance with the DomWriter interface in DOM Level 3 Load and
        Save (25 July 2002 WD), although a value that contains quotes
        but no apostrophes will be delimited by apostrophes (') instead.
        The elementName arguments are not used by default,
        but may be used by subclasses.
        """
        self.write_ascii(" ")
        self.write_encode(name, 'attribute name')
        self.write_ascii("=")

        # Replace characters illegal in attribute values
        # Wrap the value with appropriate quoting in accordance with
        # DOM Level 3 Load and Save:
        # 1. Attributes not containing quotes are serialized in quotes.
        # 2. Attributes containing quotes but no apostrophes are serialized
        #    in apostrophes.
        # 3. Attributes containing both forms of quotes are serialized in
        #    quotes, with quotes within the value represented by the
        #    predefined entity &quot;.
        if '"' in value and "'" not in value and not self._canonical_form:
            # Use apostrophes (#2)
            entitymap = self._attr_entities_apos
            quote = "'"
        else:
            # Use quotes (#1 and #3)
            entitymap = self._attr_entities_quot
            quote = '"'

        self.write_ascii(quote)
        self.write_escape(value, entitymap)
        self.write_ascii(quote)
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
                                           '\r' : '&#D;',
                                           })

    _attr_entities_quot = _xmlstream.entitymap({'<' : '&lt;',
                                                '&' : '&amp;',
                                                '\t' : '&#9;',
                                                '\n' : '&#A;',
                                                '\r' : '&#D;',
                                                '"' : '&quot;',
                                                })

    _attr_entities_apos = _xmlstream.entitymap({'<' : '&lt;',
                                                '&' : '&amp;',
                                                '\t' : '&#9;',
                                                '\n' : '&#A;',
                                                '\r' : '&#D;',
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
    operations appplied by the caller.  See Ft.Xml.Lib.Print, for example
    """


class xmlprettyprinter(xmlprinter):
    """
    An XmlPrettyPrinter instance provides functions for serializing an
    XML or XML-like document to a stream, based on SAX-like event calls
    initiated by an Ft.Xml.Lib.Print.PrintVisitor instance.

    The methods in this subclass of XmlPrinter produce the same output
    as the base class, but with extra whitespace added for visual
    formatting. The indent attribute is the string used for each level
    of indenting. It defaults to 2 spaces.
    """

    # The amount of indent for each level of nesting
    indent = '  '

    def __init__(self, stream, encoding, byte_order_mark=None,
                 canonical_form=None):
        assert not canonical_form
        xmlprinter.__init__(self, stream, encoding, byte_order_mark, False)
        self._level = 0
        self._can_indent = False  # don't indent first element
        return

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

    def endElement(self, namespace, name):
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
