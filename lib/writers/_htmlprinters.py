########################################################################
# amara/writers/_htmlprinters.py
"""
This module supports document serialization in HTML syntax.
"""

import re

from amara.lib.xmlstring import isspace
from amara.writers import _xmlstream, htmlentities
from amara.writers._xmlprinters import xmlprinter

__all__ = ('htmlprinter', 'htmlprettyprinter')

class htmlprinter(xmlprinter):
    """
    An `htmlprinter` instance provides functions for serializing an XML
    or XML-like document to a stream, based on SAX-like event calls.

    The methods in this subclass of `xmlprinter` attempt to emit a
    document conformant to the HTML 4.01 syntax, with no extra
    whitespace added for visual formatting. The degree of correctness
    of the output depends on the data supplied in the event calls; no
    checks are done for conditions that would result in syntax errors,
    such as two attributes with the same name, "--" in a comment, etc.
    """

    _disable_ouput_escaping = 0

    def __init__(self, stream, encoding, byte_order_mark=None,
                 canonical_form=None):
        assert not canonical_form
        xmlprinter.__init__(self, stream, encoding, byte_order_mark, False)

    def start_document(self, version='4.0', standalone=None):
        """
        Handles a start-document event.

        Differs from the overridden method in that no XML declaration
        is written.
        """
        # Set the entity maps to the particular version of HTML being output.
        # If the version isn't one we know how to handle, fallback to 4.0.
        try:
            entities = self._versioned_entities[version]
        except KeyError:
            entities = self._versioned_entities['4.0']
        (self._text_entities,
         self._attr_entities_quot,
         self._attr_entities_apos) = entities
        return

    def doctype(self, name, publicid, systemid):
        """
        Handles a doctype event.

        Extends the overridden method by adding support for the case
        when there is a publicid and no systemid, which is allowed in
        HTML but not in XML.
        """
        if publicid and not systemid:
            self.write_ascii('<!DOCTYPE ')
            self.write_encode(name, 'document type name')
            self.write_ascii(' PUBLIC "')
            self.write_encode(publicid, 'document type public-id')
            self.write_ascii('">\n')
        else:
            xmlprinter.doctype(self, name, publicid, systemid)
        return

    def _translate_attributes(self, element, attributes):
        bool_attrs, uri_attrs = self._boolean_attributes, self._uri_attributes
        for name, value in attributes:
            attr = name.lower()
            if attr in bool_attrs and element in bool_attrs[attr]:
                if attr == value.lower():
                    # A boolean attribute, just write out the name
                    value = None
            elif attr in uri_attrs and element in uri_attrs[attr]:
                # From HTML 4.0 Section B.2.1
                # We recommend that user agents adopt the following convention
                # for handling non-ASCII characters:
                # 1. Represent each character in UTF-8 (see [RFC2279]) as one
                #    or more bytes.
                # 2. Escape these bytes with the URI escaping mechanism
                #    (i.e., by converting each byte to %HH, where HH is the
                #     hexadecimal notation of the byte value).
                # (Although this recommendation is for HTML user agents
                # that encounter HTML with improperly escaped URI refs,
                # we implement it in order to comply with XSLT's html
                # output method, and because there's no compelling reason
                # not to do it for non-XSLT serializations as well)
                value = unicode(re.sub('[\x80-\xff]',
                                lambda match: '%%%02X' % ord(match.group()),
                                value.encode('UTF-8')))
            yield (name, value)
        return

    def start_element(self, namespace, name, namespaces, attributes):
        """
        Handles a start-tag event.

        Extends the overridden method by disabling output escaping for
        the content of certain elements (SCRIPT and STYLE).
        """
        if namespace is not None:
            xmlprinter.start_element(self, namespace, name, namespaces,
                                     attributes)
            return

        element = name.lower()
        if element in self._no_escape_elements:
            self._disable_ouput_escaping += 1

        # Translate attribute values as required
        if namespace is None:
            attributes = self._translate_attributes(element, attributes)

        xmlprinter.start_element(self, namespace, name, namespaces,
                                 attributes)

        # HTML tags are never in minimized form ('<tag/>')
        self.write_ascii('>')
        self._element_name = None
        return

    def end_element(self, namespace, name):
        """
        Handles an end-tag event.

        Differs from the overridden method in that an end tag is not
        generated for certain elements.
        """
        if namespace is not None:
            xmlprinter.end_element(self, namespace, name)
            return

        element = name.lower()
        if element not in self._forbidden_end_elements:
            self.write_ascii('</')
            self.write_encode(name, 'element name')
            self.write_ascii('>')

        # Restore normal escaping if closing a no-escape element.
        if element in self._no_escape_elements:
            self._disable_ouput_escaping -= 1
        return

    def processing_instruction(self, target, data):
        """
        Handles a processingInstruction event.

        Differs from the overridden method by writing the tag with
        no "?" at the end.
        """
        if self._element_name:
            self.write_ascii('>')
            self._element_name = None

        self.write_ascii('<?')
        self.write_encode(target, 'processing-instruction target')
        if data:
            self.write_ascii(' ')
            self.write_encode(data, 'processing-instruction data')
        self.write_ascii('>')
        return

    # Elements for which end tags must not be emitted
    _forbidden_end_elements = frozenset([
        'area', 'base', 'basefont', 'br', 'col', 'frame', 'hr',
        'img', 'input', 'isindex', 'link', 'meta', 'param',
        ])

    # Elements in which character data is not escaped
    #
    # FIXME: According to HTML 4.01 section B.3.2, "</" and unencodable
    # characters within the content of a SCRIPT or STYLE slement must
    # be escaped according to the conventions of the script or style
    # language in use.
    _no_escape_elements = frozenset(['script', 'style'])

    # Boolean attributes that can be minimized
    _boolean_attributes = {
        'checked'  : ['input'],
        'compact'  : ['dl', 'ol', 'ul', 'dir', 'menu', 'li'],
        'declare'  : ['object'],
        'defer'    : ['script'],
        'disabled' : ['input', 'select', 'optgroup', 'option', 'textarea',
                      'button'],
        'ismap'    : ['img', 'input'],
        'multiple' : ['select'],
        'nohref'   : ['area'],
        'noresize' : ['frame'],
        'noshade'  : ['hr'],
        'nowrap'   : ['th', 'td'],
        'readonly' : ['input', 'textarea'],
        'selected' : ['option'],
        }

    # URI attributes that can have non-ASCII characters escaped
    _uri_attributes = {
        'action'     : ['form'],
        'background' : ['body'],
        'cite'       : ['blockquote', 'del', 'ins', 'q'],
        'classid'    : ['object'],
        'codebase'   : ['applet', 'object'],
        'data'       : ['object'],
        'href'       : ['a', 'area', 'base', 'link'],
        'longdesc'   : ['frame', 'iframe', 'img'],
        'profile'    : ['head'],
        'src'        : ['frame', 'iframe', 'img', 'input', 'script'],
        'usemap'     : ['img', 'input', 'object'],
        }

    _versioned_entities = {
        '3.2' : [],
        '4.0' : [],
        }

    _text_entities = {'<': '&lt;',
                      '>': '&gt;',
                      '&': '&amp;',
                      '\r': '&#13;',
                      }
    _text_entities.update(htmlentities.ENTITIES_HTML_32)
    _versioned_entities['3.2'].append(_xmlstream.entitymap(_text_entities))
    _text_entities.update(htmlentities.ENTITIES_HTML_40)
    # The default entities are those for HTML 4.01
    _text_entities = _xmlstream.entitymap(_text_entities)
    _versioned_entities['4.0'].append(_text_entities)


    # For HTML attribute values:
    #   1. do not escape '<' (see XSLT 1.0 section 16.2)
    #   2. only escape '&' if not followed by '{'
    def _attr_amp_escape(string, offset):
        if string.startswith('&{', offset):
            return '&'
        else:
            return '&amp;'
    _attr_entities_quot = {'&' : _attr_amp_escape,
                           '\t' : '&#9;',
                           '\n' : '&#10;',
                           '\r' : '&#13;',
                           '"' : '&quot;',
                           }
    _attr_entities_quot.update(htmlentities.ENTITIES_HTML_32)
    _versioned_entities['3.2'].append(_xmlstream.entitymap(_attr_entities_quot))
    _attr_entities_quot.update(htmlentities.ENTITIES_HTML_40)
    # The default entities are those for HTML 4.01
    _attr_entities_quot = _xmlstream.entitymap(_attr_entities_quot)
    _versioned_entities['4.0'].append(_attr_entities_quot)

    _attr_entities_apos = {'&' : _attr_amp_escape,
                           '\t' : '&#9;',
                           '\n' : '&#10;',
                           '\r' : '&#13;',
                           "'" : '&#39;',  # no &apos; in HTML
                           }
    _attr_entities_apos.update(htmlentities.ENTITIES_HTML_32)
    _versioned_entities['3.2'].append(_xmlstream.entitymap(_attr_entities_apos))
    _attr_entities_apos.update(htmlentities.ENTITIES_HTML_40)
    # The default entities are those for HTML 4.01
    _attr_entities_apos = _xmlstream.entitymap(_attr_entities_apos)
    _versioned_entities['4.0'].append(_attr_entities_apos)
    del _attr_amp_escape


class htmlprettyprinter(htmlprinter):
    """
    An `htmlprettyprinter` instance provides functions for serializing an
    XML or XML-like document to a stream, based on SAX-like event calls.

    The methods in this subclass of `htmlprinter` attempt to emit a
    document conformant to the HTML 4.01 syntax, with extra whitespace
    added for visual formatting. The indent attribute is the string used
    for each level of indenting. It defaults to 2 spaces.
    """

    # The amount of indent for each level of nesting
    indent = '  '

    def __init__(self, stream, encoding, byte_order_mark=None,
                 canonical_form=None):
        htmlprinter.__init__(self, stream, encoding, byte_order_mark,
                             canonical_form)
        self._level = 0
        # indenting control variables
        self._is_inline = [1]  # prevent newline before first element
        self._in_no_indent = [0]
        self._indent_forbidden = 0
        self._indent_end_tag = False
        return

    def start_element(self, namespace, name, namespaces, attributes):
        if self._element_name:
            self.write_ascii('>')
            self._element_name = None

        # Create the lookup key for the various lookup tables
        if namespace is None:
            key = name.lower()
        else:
            key = '#bogus'

        # Get the inline flag for this element
        inline = key in self._inline_elements

        if (not inline and not self._is_inline[-1]
            and not self._indent_forbidden):
            self.write_ascii('\n' + (self.indent * self._level))

        htmlprinter.start_element(self, namespace, name, namespaces,
                                  attributes)

        # Setup indenting rules for this element
        self._is_inline.append(inline)
        self._in_no_indent.append(key in self._no_indent_elements)
        self._indent_forbidden += self._in_no_indent[-1]
        self._level += 1
        self._indent_end_tag = False
        return

    def end_element(self, namespace, name):
        # Undo changes to indenting rules for this element
        self._level -= 1
        is_inline = self._is_inline[-1]
        del self._is_inline[-1]

        if self._element_name:
            # An empty non-null namespace element (use XML short form)
            self.write_ascii('/>')
            self._element_name = None
        else:
            if (not is_inline and not self._indent_forbidden and
                self._indent_end_tag):
                self.write_ascii('\n' + (self.indent * self._level))

            htmlprinter.end_element(self, namespace, name)

        no_indent = self._in_no_indent[-1]
        del self._in_no_indent[-1]
        self._indent_forbidden -= no_indent
        self._indent_end_tag = not is_inline
        return

    def text(self, data, disable_escaping=False):
        # OK to indent end-tag if just whitespace is written
        self._indent_end_tag = isspace(data)
        htmlprinter.text(self, data, disable_escaping)

    def processing_instruction(self, target, data):
        if self._element_name:
            self.write_ascii('>')
            self._element_name = None

        # OK to indent end-tag
        self._indent_end_tag = True

        # try to indent
        if not self._is_inline[-1] and not self._indent_forbidden:
            self.write_ascii('\n' + (self.indent * self._level))
        htmlprinter.processing_instruction(self, target, data)
        return

    def comment(self, data):
        if self._element_name:
            self.write_ascii('>')
            self._element_name = None

        # OK to indent end-tag
        self._indent_end_tag = True

        # try to indent
        if not self._is_inline[-1] and not self._indent_forbidden:
            self.write_ascii('\n' + (self.indent * self._level))
        htmlprinter.comment(self, data)
        return

    # Elements that should never be emitted on a new line.
    _inline_elements = frozenset([
        'tt', 'i', 'b', 'u', 's', 'strike', 'big', 'small', 'em', 'strong',
        'dfn', 'code', 'samp', 'kbd', 'var', 'cite', 'abbr', 'acronym', 'a',
        'img', 'applet', 'object', 'font', 'basefont', 'br', 'script', 'map',
        'q', 'sub', 'sup', 'span', 'bdo', 'iframe', 'input', 'select',
        'textarea', 'label', 'button',
        ])

    # Elements that should never be emitted with additional
    # whitespace in their content; i.e., once you're inside
    # one, you don't do any more indenting.
    _no_indent_elements = frozenset([
        'script', 'style', 'pre', 'textarea', 'xmp',
        ])
