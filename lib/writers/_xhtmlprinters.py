########################################################################
# amara/writers/_xhtmlprinters.py
"""
This module supports document serialization in XHTML syntax.
"""

import re

from amara import XHTML_NAMESPACE
from amara.writers import _xmlstream, htmlentities
from amara.writers._xmlprinter import xmlprinter

__all__ = ('xhtmlprinter', 'xhtmlprettyprinter')

class xhtmlprinter(xmlprinter):
    """
    An `xhtmlprinter` instance provides functions for serializing an XML
    or XML-like document to a stream, based on SAX-like event calls.

    The methods in this subclass of `xmlprinter` attempt to emit a
    document conformant to the XHTML 1.0 syntax, with no extra
    whitespace added for visual formatting. The degree of correctness
    of the output depends on the data supplied in the event calls; no
    checks are done for conditions that would result in syntax errors,
    such as two attributes with the same name, "--" in a comment, etc.
    """

    def _translate_attributes(self, element, attributes):
        uri_attrs = self._uri_attributes
        for name, value in attributes:
            if name in uri_attrs and element in uri_attrs[name]:
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
        """
        xhtml = (namespace == XHTML_NAMESPACE)
        if xhtml:
            attributes = self._translate_attributes(name, attributes)

        xmlprinter.start_element(self, namespace, name, namespaces,
                                 attributes)

        if xhtml and name not in self._empty_elements:
            # Check for XHTML tags which should not be in minimized form
            # ('<tag/>')
            self.write_ascii('>')
            self._element_name = None
        return

    def end_element(self, namespace, name):
        """
        Handles an end-tag event.

        Differs from the overridden method in that an end tag is not
        generated for certain elements.
        """
        if (self._element_name and
            name in self._empty_elements and
            namespace == XHTML_NAMESPACE):
            # EMPTY element content, use minimized form (with space before /)
            self.write_ascii(' />')
        else:
            xmlprinter.end_element(self, namespace, name)
        return

    # Elements for which end tags must not be emitted
    _empty_elements = frozenset([
        'area', 'base', 'basefont', 'br', 'col', 'frame', 'hr',
        'img', 'input', 'isindex', 'link', 'meta', 'param',
        ])

    # URI attributes that can have non-ASCII characters escaped
    _uri_attributes = {
        'action'    : ['form'],
        'archive'   : ['object'],
        'background': ['body'],
        'cite'      : ['blockquote', 'del', 'ins', 'q'],
        'classid'   : ['object'],
        'codebase'  : ['applet', 'object'],
        'data'      : ['object'],
        'datasrc'   : ['button', 'div', 'input', 'object', 'select', 'span',
                       'table', 'textarea'],
        'for'       : ['script'],
        'href'      : ['a', 'area', 'base', 'link'],
        'longdesc'  : ['frame', 'iframe', 'img'],
        'name'      : ['a'],
        'profile'   : ['head'],
        'src'       : ['frame', 'iframe', 'img', 'input', 'script'],
        'usemap'    : ['img', 'input', 'object'],
        }

    _text_entities = {'<': '&lt;',
                      '>': '&gt;',
                      '&': '&amp;',
                      '\r': '&#13;',
                      }
    _text_entities.update(htmlentities.ENTITIES_XHTML_10)
    _text_entities = _xmlstream.entitymap(_text_entities)

    _attr_entities_quot = {'&' : '&amp;',
                           '\t' : '&#9;',
                           '\n' : '&#10;',
                           '\r' : '&#13;',
                           '"' : '&quot;',
                           }
    _attr_entities_quot.update(htmlentities.ENTITIES_XHTML_10)
    _attr_entities_quot = _xmlstream.entitymap(_attr_entities_quot)

    _attr_entities_apos = {'&' : '&amp;',
                           '\t' : '&#9;',
                           '\n' : '&#10;',
                           '\r' : '&#13;',
                           "'" : '&#39;',  # no &apos; in HTML
                           }
    _attr_entities_apos.update(htmlentities.ENTITIES_XHTML_10)
    _attr_entities_apos = _xmlstream.entitymap(_attr_entities_apos)


class xhtmlprettyprinter(xhtmlprinter):
    """
    An `xhtmlprettyprinter` instance provides functions for serializing an
    XML or XML-like document to a stream, based on SAX-like event calls.

    The methods in this subclass of `xhtmlprinter` attempt to emit a
    document conformant to the XHTML 1.0 syntax, with extra whitespace
    added for visual formatting. The indent attribute is the string used
    for each level of indenting. It defaults to 2 spaces.
    """

    # The amount of indent for each level of nesting
    indent = '  '

    def __init__(self, stream, encoding, byte_order_mark=None,
                 canonical_form=None):
        xhtmlprinter.__init__(self, stream, encoding, byte_order_mark,
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
        if namespace == XHTML_NAMESPACE:
            key = name
        else:
            key = None

        # Get the inline flag for this element
        inline = key in self._inline_elements

        if (not inline and not self._is_inline[-1]
            and not self._indent_forbidden):
            self.write_ascii('\n' + (self.indent * self._level))

        xhtmlprinter.start_element(self, namespace, name, namespaces,
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

            xhtmlprinter.end_element(self, namespace, name)

        no_indent = self._in_no_indent[-1]
        del self._in_no_indent[-1]
        self._indent_forbidden -= no_indent
        self._indent_end_tag = not is_inline
        return

    def processing_instruction(self, target, data):
        if self._element_name:
            self.write_ascii('>')
            self._element_name = None

        # OK to indent end-tag
        self._indent_end_tag = True

        # try to indent
        if not self._is_inline[-1] and not self._indent_forbidden:
            self.write_ascii('\n' + (self.indent * self._level))
        xhtmlprinter.processing_instruction(self, target, data)
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
        xhtmlprinter.comment(self, data)
        return

    # Elements that should never be emitted on a new line.
    _inline_elements = frozenset([
        'tt', 'i', 'b', 'u', 's', 'strike', 'big', 'small', 'em', 'strong',
        'dfn', 'code', 'samp', 'kbd', 'var', 'cite', 'abbr', 'acronym', 'a',
        'img', 'applet', 'object', 'font', 'basefont', 'script', 'map', 'q',
        'sub', 'sup', 'span', 'bdo', 'iframe', 'input', 'select', 'textarea',
        'label', 'button',
        ])

    # Elements that should never be emitted with additional
    # whitespace in their content; i.e., once you're inside
    # one, you don't do any more indenting.
    _no_indent_elements = frozenset([
        'script', 'style', 'pre', 'textarea', 'xmp',
        ])
