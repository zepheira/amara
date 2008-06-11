########################################################################
# amara/writers/_htmlprinters.py
"""
This module supports document serialization in HTML syntax.
"""

import re

from amara import XHTML_NAMESPACE
from amara.writers import _xmlstream
from amara.writers._xmlprinter import xmlprinter

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

    def __init__(self, stream, encoding, xhtml=False):
        """
        Creates an HtmlPrinter instance.

        stream must be a file-like object open for writing binary
        data. encoding specifies the encoding which is to be used for
        writing to the stream.
        """
        xmlprinter.__init__(self, stream, encoding)
        self.xhtml = xhtml
        return

    def start_document(self, version='4.0', standalone=None):
        """
        Handles a startDocument event.

        Differs from the overridden method in that no XML declaration
        is written.
        """
        # If the version isn't one we know how to handle, fallback to 4.0.
        if version not in self._versionedEntities or self.xhtml:
            version = '4.0'

        # Set the entity maps to the particular version of HTML being output.
        self.textEntities, self.attrEntitiesQuot, self.attrEntitiesApos = \
            self._versionedEntities[version]

        if self.xhtml:
            XmlPrinter.startDocument(self, version='1.0', standalone=None)
        return

    def doctype(self, name, publicId, systemId):
        """
        Handles a doctype event.

        Extends the overridden method by adding support for the case
        when there is a publicId and no systemId, which is allowed in
        HTML but not in XML.
        """
        if publicId and not systemId:
            self.writeAscii('<!DOCTYPE ')
            self.writeEncode(name, 'document type name')
            self.writeAscii(' PUBLIC "')
            self.writeEncode(publicId, 'document type public-id')
            self.writeAscii('">\n')
        else:
            XmlPrinter.doctype(self, name, publicId, systemId)
        return

    def startElement(self, namespaceUri, tagName, namespaces, attributes):
        """
        Handles a startElement event.

        Extends the overridden method by disabling output escaping for
        the content of certain elements (SCRIPT and STYLE).
        """
        if namespaceUri is not None:
            XmlPrinter.startElement(self, namespaceUri, tagName, namespaces,
                                    attributes)
            if self.xhtml and namespaceUri == XHTML_NAMESPACE and tagName not in self.forbiddenEndElements:
                # Check for XHTML tags which should not be in minimized form ('<tag/>')
                self.writeAscii('>')
                self._inElement = False
            return

        if tagName.lower() in self.noEscapeElements:
            self.disableOutputEscaping += 1

        XmlPrinter.startElement(self, namespaceUri, tagName, namespaces,
                                attributes)

        # HTML tags are never in minimized form ('<tag/>')
        self.writeAscii('>')
        self._inElement = False
        return

    def endElement(self, namespaceUri, tagName):
        """
        Handles an endElement event.

        Differs from the overridden method in that an end tag is not
        generated for certain elements.
        """
        if self.xhtml and namespaceUri == XHTML_NAMESPACE:
            if tagName not in self.forbiddenEndElements:
                self.writeAscii('</')
                self.writeEncode(tagName, 'element name')
                self.writeAscii('>')
            else:
                XmlPrinter.endElement(self, namespaceUri, tagName)
            return

        if namespaceUri is not None:
            XmlPrinter.endElement(self, namespaceUri, tagName)
            return

        element = tagName.lower()
        if element not in self.forbiddenEndElements:
            self.writeAscii('</')
            self.writeEncode(tagName, 'element name')
            self.writeAscii('>')

        # Restore normal escaping if closing a no-escape element.
        if element in self.noEscapeElements:
            self.disableOutputEscaping -= 1
        return

    def attribute(self, elementUri, elementName, name, value):
        """
        Handles an attribute event.

        Extends the overridden method by writing boolean attributes in
        minimized form.
        """
        if elementUri is not None:
            XmlPrinter.attribute(self, elementUri, elementName, name, value)
            return

        element = elementName.lower()
        attribute = name.lower()
        if element in self.booleanAttributes.get(attribute, []) \
           and attribute == value.lower():
            # A boolean attribute, just write out the name
            self.writeAscii(' ')
            self.writeEncode(name, 'attribute name')
        elif element in self.uriAttributes.get(attribute, []):
            # From HTML 4.0 Section B.2.1
            # We recommend that user agents adopt the following convention for
            # handling non-ASCII characters:
            # 1. Represent each character in UTF-8 (see [RFC2279]) as one or
            #    more bytes.
            # 2. Escape these bytes with the URI escaping mechanism (i.e., by
            #    converting each byte to %HH, where HH is the hexadecimal
            #    notation of the byte value).
            # (Although this recommendation is for HTML user agents
            # that encounter HTML with improperly escaped URI refs,
            # we implement it in order to comply with XSLT's html
            # output method, and because there's no compelling reason
            # not to do it for non-XSLT serializations as well)
            #
            # FIXME:
            # "&" should not be escaped in an attribute value when it
            # it is followed by "{" (see Section B.7.1 of HTML 4.0).
            value = unicode(re.sub('[\x80-\xff]',
                                   lambda match: '%%%02X' % ord(match.group()),
                                   value.encode('UTF-8')))
            XmlPrinter.attribute(self, elementUri, elementName, name, value)
        else:
            XmlPrinter.attribute(self, elementUri, elementName, name, value)
        return

    def text(self, data, disableEscaping=0):
        """
        Handles a text event.

        Extends the overridden method by disabling output escaping if
        in the content of certain elements like SCRIPT or STYLE.
        """
        if self._inElement:
            self.writeAscii('>')
            self._inElement = False

        disableEscaping = disableEscaping or self.disableOutputEscaping
        XmlPrinter.text(self, data, disableEscaping)
        return

    def processingInstruction(self, target, data):
        """
        Handles a processingInstruction event.

        Differs from the overridden method by writing the tag with
        no "?" at the end.
        """
        if self._inElement:
            self.writeAscii('>')
            self._inElement = False

        self.writeAscii('<?')
        self.writeEncode(target, 'processing-instruction target')
        if data:
            self.writeAscii(' ')
            self.writeEncode(data, 'processing-instruction data')
        self.writeAscii('>')
        return

    # Elements for which end tags must not be emitted
    forbiddenEndElements = {}
    for name in ['area', 'base', 'basefont', 'br', 'col', 'frame', 'hr',
                 'img', 'input', 'isindex', 'link', 'meta', 'param']:
        forbiddenEndElements[name] = True
    del name

    # Elements in which character data is not escaped
    #
    # FIXME: According to HTML 4.01 section B.3.2, "</" and unencodable
    # characters within the content of a SCRIPT or STYLE slement must
    # be escaped according to the conventions of the script or style
    # language in use.
    noEscapeElements = {'script' : True,
                        'style' : True,
                        }

    # Boolean attributes that can be minimized
    booleanAttributes = {
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
    uriAttributes = {
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

    # HTML 3.2 defined character entities
    entities_3_2 = {
        # Sect 24.2 -- ISO 8859-1
        u'\u00A0' : '&nbsp;',
        u'\u00A1' : '&iexcl;',
        u'\u00A2' : '&cent;',
        u'\u00A3' : '&pound;',
        u'\u00A4' : '&curren;',
        u'\u00A5' : '&yen;',
        u'\u00A6' : '&brvbar;',
        u'\u00A7' : '&sect;',
        u'\u00A8' : '&uml;',
        u'\u00A9' : '&copy;',
        u'\u00AA' : '&ordf;',
        u'\u00AB' : '&laquo;',
        u'\u00AC' : '&not;',
        u'\u00AD' : '&shy;',
        u'\u00AE' : '&reg;',
        u'\u00AF' : '&macr;',
        u'\u00B0' : '&deg;',
        u'\u00B1' : '&plusmn;',
        u'\u00B2' : '&sup2;',
        u'\u00B3' : '&sup3;',
        u'\u00B4' : '&acute;',
        u'\u00B5' : '&micro;',
        u'\u00B6' : '&para;',
        u'\u00B7' : '&middot;',
        u'\u00B8' : '&cedil;',
        u'\u00B9' : '&sup1;',
        u'\u00BA' : '&ordm;',
        u'\u00BB' : '&raquo;',
        u'\u00BC' : '&frac14;',
        u'\u00BD' : '&frac12;',
        u'\u00BE' : '&frac34;',
        u'\u00BF' : '&iquest;',
        u'\u00C0' : '&Agrave;',
        u'\u00C1' : '&Aacute;',
        u'\u00C2' : '&Acirc;',
        u'\u00C3' : '&Atilde;',
        u'\u00C4' : '&Auml;',
        u'\u00C5' : '&Aring;',
        u'\u00C6' : '&AElig;',
        u'\u00C7' : '&Ccedil;',
        u'\u00C8' : '&Egrave;',
        u'\u00C9' : '&Eacute;',
        u'\u00CA' : '&Ecirc;',
        u'\u00CB' : '&Euml;',
        u'\u00CC' : '&Igrave;',
        u'\u00CD' : '&Iacute;',
        u'\u00CE' : '&Icirc;',
        u'\u00CF' : '&Iuml;',
        u'\u00D0' : '&ETH;',
        u'\u00D1' : '&Ntilde;',
        u'\u00D2' : '&Ograve;',
        u'\u00D3' : '&Oacute;',
        u'\u00D4' : '&Ocirc;',
        u'\u00D5' : '&Otilde;',
        u'\u00D6' : '&Ouml;',
        u'\u00D7' : '&times;',
        u'\u00D8' : '&Oslash;',
        u'\u00D9' : '&Ugrave;',
        u'\u00DA' : '&Uacute;',
        u'\u00DB' : '&Ucirc;',
        u'\u00DC' : '&Uuml;',
        u'\u00DD' : '&Yacute;',
        u'\u00DE' : '&THORN;',
        u'\u00DF' : '&szlig;',
        u'\u00E0' : '&agrave;',
        u'\u00E1' : '&aacute;',
        u'\u00E2' : '&acirc;',
        u'\u00E3' : '&atilde;',
        u'\u00E4' : '&auml;',
        u'\u00E5' : '&aring;',
        u'\u00E6' : '&aelig;',
        u'\u00E7' : '&ccedil;',
        u'\u00E8' : '&egrave;',
        u'\u00E9' : '&eacute;',
        u'\u00EA' : '&ecirc;',
        u'\u00EB' : '&euml;',
        u'\u00EC' : '&igrave;',
        u'\u00ED' : '&iacute;',
        u'\u00EE' : '&icirc;',
        u'\u00EF' : '&iuml;',
        u'\u00F0' : '&eth;',
        u'\u00F1' : '&ntilde;',
        u'\u00F2' : '&ograve;',
        u'\u00F3' : '&oacute;',
        u'\u00F4' : '&ocirc;',
        u'\u00F5' : '&otilde;',
        u'\u00F6' : '&ouml;',
        u'\u00F7' : '&divide;',
        u'\u00F8' : '&oslash;',
        u'\u00F9' : '&ugrave;',
        u'\u00FA' : '&uacute;',
        u'\u00FB' : '&ucirc;',
        u'\u00FC' : '&uuml;',
        u'\u00FD' : '&yacute;',
        u'\u00FE' : '&thorn;',
        u'\u00FF' : '&yuml;',
        }

    # HTML 4.01 defined character entities
    entities_4_0 = {
        # Sect 24.3 -- Symbols, Mathematical Symbols, and Greek Letters
        # Latin Extended-B
        u'\u0192' : '&fnof;',
        # Greek
        u'\u0391' : '&Alpha;',
        u'\u0392' : '&Beta;',
        u'\u0393' : '&Gamma;',
        u'\u0394' : '&Delta;',
        u'\u0395' : '&Epsilon;',
        u'\u0396' : '&Zeta;',
        u'\u0397' : '&Eta;',
        u'\u0398' : '&Theta;',
        u'\u0399' : '&Iota;',
        u'\u039A' : '&Kappa;',
        u'\u039B' : '&Lambda;',
        u'\u039C' : '&Mu;',
        u'\u039D' : '&Nu;',
        u'\u039E' : '&Xi;',
        u'\u039F' : '&Omicron;',
        u'\u03A0' : '&Pi;',
        u'\u03A1' : '&Rho;',
        u'\u03A3' : '&Sigma;',
        u'\u03A4' : '&Tau;',
        u'\u03A5' : '&Upsilon;',
        u'\u03A6' : '&Phi;',
        u'\u03A7' : '&Chi;',
        u'\u03A8' : '&Psi;',
        u'\u03A9' : '&Omega;',
        u'\u03B1' : '&alpha;',
        u'\u03B2' : '&beta;',
        u'\u03B3' : '&gamma;',
        u'\u03B4' : '&delta;',
        u'\u03B5' : '&epsilon;',
        u'\u03B6' : '&zeta;',
        u'\u03B7' : '&eta;',
        u'\u03B8' : '&theta;',
        u'\u03B9' : '&iota;',
        u'\u03BA' : '&kappa;',
        u'\u03BB' : '&lambda;',
        u'\u03BC' : '&mu;',
        u'\u03BD' : '&nu;',
        u'\u03BE' : '&xi;',
        u'\u03BF' : '&omicron;',
        u'\u03C0' : '&pi;',
        u'\u03C1' : '&rho;',
        u'\u03C2' : '&sigmaf;',
        u'\u03C3' : '&sigma;',
        u'\u03C4' : '&tau;',
        u'\u03C5' : '&upsilon;',
        u'\u03C6' : '&phi;',
        u'\u03C7' : '&chi;',
        u'\u03C8' : '&psi;',
        u'\u03C9' : '&omega;',
        u'\u03D1' : '&thetasym;',
        u'\u03D2' : '&upsih;',
        u'\u03D6' : '&piv;',
        # General Punctuation
        u'\u2022' : '&bull;',      # bullet
        u'\u2026' : '&hellip;',    # horizontal ellipsis
        u'\u2032' : '&prime;',     # prime (minutes/feet)
        u'\u2033' : '&Prime;',     # double prime (seconds/inches)
        u'\u203E' : '&oline;',     # overline (spacing overscore)
        u'\u203A' : '&frasl;',     # fractional slash
        # Letterlike Symbols
        u'\u2118' : '&weierp;',    # script capital P (power set/Weierstrass p)
        u'\u2111' : '&image;',     # blackletter capital I (imaginary part)
        u'\u211C' : '&real;',      # blackletter capital R (real part)
        u'\u2122' : '&trade;',     # trademark
        u'\u2135' : '&alefsym;',   # alef symbol (first transfinite cardinal)
        # Arrows
        u'\u2190' : '&larr;',      # leftwards arrow
        u'\u2191' : '&uarr;',      # upwards arrow
        u'\u2192' : '&rarr;',      # rightwards arrow
        u'\u2193' : '&darr;',      # downwards arrow
        u'\u2194' : '&harr;',      # left right arrow
        u'\u21B5' : '&crarr;',     # downwards arrow with corner leftwards
        u'\u21D0' : '&lArr;',      # leftwards double arrow
        u'\u21D1' : '&uArr;',      # upwards double arrow
        u'\u21D2' : '&rArr;',      # rightwards double arrow
        u'\u21D3' : '&dArr;',      # downwards double arrow
        u'\u21D4' : '&hArr;',      # left right double arrow
        # Mathematical Operators
        u'\u2200' : '&forall;',    # for all
        u'\u2202' : '&part;',      # partial differential
        u'\u2203' : '&exist;',     # there exists
        u'\u2205' : '&empty;',     # empty set, null set, diameter
        u'\u2207' : '&nabla;',     # nabla, backward difference
        u'\u2208' : '&isin;',      # element of
        u'\u2209' : '&notin;',     # not an element of
        u'\u220B' : '&ni;',        # contains as member
        u'\u220F' : '&prod;',      # n-ary product, product sign
        u'\u2211' : '&sum;',       # n-ary sumation
        u'\u2212' : '&minus;',     # minus sign
        u'\u2217' : '&lowast;',    # asterisk operator
        u'\u221A' : '&radic;',     # square root, radical sign
        u'\u221D' : '&prop;',      # proportional to
        u'\u221E' : '&infin;',     # infinity
        u'\u2220' : '&ang;',       # angle
        u'\u2227' : '&and;',       # logical and, wedge
        u'\u2228' : '&or;',        # logical or, vee
        u'\u2229' : '&cap;',       # intersection, cap
        u'\u222A' : '&cup;',       # union, cup
        u'\u222B' : '&int;',       # integral
        u'\u2234' : '&there4;',    # therefore
        u'\u223C' : '&sim;',       # tilde operator, varies with, similar to
        u'\u2245' : '&cong;',      # approximately equal to
        u'\u2248' : '&asymp;',     # almost equal to, asymptotic to
        u'\u2260' : '&ne;',        # not equal to
        u'\u2261' : '&equiv;',     # identical to
        u'\u2264' : '&le;',        # less-than or equal to
        u'\u2265' : '&ge;',        # greater-than or equal to
        u'\u2282' : '&sub;',       # subset of
        u'\u2283' : '&sup;',       # superset of
        u'\u2284' : '&nsub;',      # not subset of
        u'\u2286' : '&sube;',      # subset of or equal to
        u'\u2287' : '&supe;',      # superset of or equal to
        u'\u2295' : '&oplus;',     # circled plus, direct sum
        u'\u2297' : '&otimes;',    # circled times, vector product
        u'\u22A5' : '&perp;',      # up tack, orthogonal to, perpendicular
        u'\u22C5' : '&sdot;',      # dot operator
        u'\u2308' : '&lceil;',     # left ceiling, apl upstile
        u'\u2309' : '&rceil;',     # right ceiling
        u'\u230A' : '&lfloor;',    # left floor, apl downstile
        u'\u230B' : '&rfloor;',    # right floor
        u'\u2329' : '&lang;',      # left-pointing angle bracket, bra
        u'\u232A' : '&rang;',      # right-pointing angle bracket, ket
        u'\u25CA' : '&loz;',       # lozenge
        # Miscellaneous Symbols
        u'\u2660' : '&spades;',
        u'\u2663' : '&clubs;',
        u'\u2665' : '&hearts;',
        u'\u2666' : '&diams;',

        # Sect 24.4 -- Markup Significant and Internationalization
        # Latin Extended-A
        u'\u0152' : '&OElig;',      # capital ligature OE
        u'\u0153' : '&oelig;',      # small ligature oe
        u'\u0160' : '&Scaron;',     # capital S with caron
        u'\u0161' : '&scaron;',     # small s with caron
        u'\u0178' : '&Yuml;',       # capital Y with diaeresis
        # Spacing Modifier Letters
        u'\u02C6' : '&circ;',       # circumflexx accent
        u'\u02DC' : '&tidle;',      # small tilde
        # General Punctuation
        u'\u2002' : '&ensp;',      # en space
        u'\u2003' : '&emsp;',      # em space
        u'\u2009' : '&thinsp;',    # thin space
        u'\u200C' : '&zwnj;',      # zero-width non-joiner
        u'\u200D' : '&zwj;',       # zero-width joiner
        u'\u200E' : '&lrm;',       # left-to-right mark
        u'\u200F' : '&rlm;',       # right-to-left mark
        u'\u2013' : '&ndash;',     # en dash
        u'\u2014' : '&mdash;',     # em dash
        u'\u2018' : '&lsquo;',     # left single quotation mark
        u'\u2019' : '&rsquo;',     # right single quotation mark
        u'\u201A' : '&sbquo;',     # single low-9 quotation mark
        u'\u201C' : '&ldquo;',     # left double quotation mark
        u'\u201D' : '&rdquo;',     # right double quotation mark
        u'\u201E' : '&bdquo;',     # double low-9 quotation mark
        u'\u2020' : '&dagger;',    # dagger
        u'\u2021' : '&Dagger;',    # double dagger
        u'\u2030' : '&permil;',    # per mille sign
        u'\u2039' : '&lsaquo;',    # single left-pointing angle quotation mark
        u'\u203A' : '&rsaquo;',    # single right-pointing angle quotation mark
        u'\u20AC' : '&euro;',      # euro sign
    }

    _versionedEntities = {
        '3.2' : [],
        '4.0' : [],
        }

    textEntities = {'<' : '&lt;',
                    '>' : '&gt;',
                    '&' : '&amp;',
                    '\r' : '&#13;',
                    }
    textEntities.update(entities_3_2)
    _versionedEntities['3.2'].append(cStreamWriter.EntityMap(textEntities))
    textEntities.update(entities_4_0)
    textEntities = cStreamWriter.EntityMap(textEntities)
    _versionedEntities['4.0'].append(textEntities)


    # For HTML attribute values:
    #   1. do not escape '<' (see XSLT 1.0 section 16.2)
    #   2. only escape '&' if not followed by '{'
    def attr_amp_escape(string, offset):
        if string.startswith('&{', offset):
            return '&'
        else:
            return '&amp;'

    attrEntitiesQuot = {'&' : attr_amp_escape,
                        '\t' : '&#9;',
                        '\n' : '&#10;',
                        '\r' : '&#13;',
                        '"' : '&quot;',
                        }
    attrEntitiesQuot.update(entities_3_2)
    _versionedEntities['3.2'].append(cStreamWriter.EntityMap(attrEntitiesQuot))
    attrEntitiesQuot.update(entities_4_0)
    attrEntitiesQuot = cStreamWriter.EntityMap(attrEntitiesQuot)
    _versionedEntities['4.0'].append(attrEntitiesQuot)

    attrEntitiesApos = {'&' : attr_amp_escape,
                        '\t' : '&#9;',
                        '\n' : '&#10;',
                        '\r' : '&#13;',
                        "'" : '&#39;',  # no &apos; in HTML
                        }
    attrEntitiesApos.update(entities_3_2)
    _versionedEntities['3.2'].append(cStreamWriter.EntityMap(attrEntitiesApos))
    attrEntitiesApos.update(entities_4_0)
    attrEntitiesApos = cStreamWriter.EntityMap(attrEntitiesApos)
    _versionedEntities['4.0'].append(attrEntitiesApos)

    del entities_3_2
    del entities_4_0
    del attr_amp_escape


class HtmlPrettyPrinter(HtmlPrinter):
    """
    An HtmlPrettyPrinter instance provides functions for serializing an
    XML or XML-like document to a stream, based on SAX-like event calls
    initiated by an Ft.Xml.Lib.Print.PrintVisitor instance.

    The methods in this subclass of HtmlPrinter attempt to emit a
    document conformant to the HTML 4.01 syntax, with extra whitespace
    added for visual formatting. The indent attribute is the string used
    for each level of indenting. It defaults to 2 spaces.
    """

    # The amount of indent for each level of nesting
    indent = '  '

    def __init__(self, stream, encoding, xhtml=False):
        HtmlPrinter.__init__(self, stream, encoding, xhtml)
        self._level = 0

        # indenting control variables
        self._isInline = [1]  # prevent newline before first element
        self._inNoIndent = [0]
        self._indentForbidden = 0
        self._indentEndTag = False
        self.xhtml = xhtml
        if xhtml:
            for name in inlineLocalNames:
                inlineElements[(XHTML_NAMESPACE, name)] = True
        return

    def startElement(self, namespaceUri, tagName, namespaces, attributes):
        if self._inElement:
            self.writeAscii('>')
            self._inElement = False

        # Create the lookup key for the various lookup tables
        key = (namespaceUri, tagName.lower())

        # Get the inline flag for this element
        inline = key in self.inlineElements

        if not inline and not self._isInline[-1] and not self._indentForbidden:
            self.writeAscii('\n' + (self.indent * self._level))

        HtmlPrinter.startElement(self, namespaceUri, tagName, namespaces,
                                 attributes)

        # Setup indenting rules for this element
        self._isInline.append(inline)
        self._inNoIndent.append(key in self.noIndentElements)
        self._indentForbidden += self._inNoIndent[-1]
        self._level += 1
        self._indentEndTag = False
        return

    def endElement(self, namespaceUri, tagName):
        # Undo changes to indenting rules for this element
        self._level -= 1
        inline = self._isInline.pop()

        #if self.xhtml and namespaceUri == XHTML_NAMESPACE:
        #    HtmlPrinter.endElement(self, namespaceUri, tagName)

        if self._inElement:
            # An empty non-null namespace element (use XML short form)
            self.writeAscii('/>')
            self._inElement = False
        else:
            if not inline and not self._indentForbidden and self._indentEndTag:
                self.writeAscii('\n' + (self.indent * self._level))

            HtmlPrinter.endElement(self, namespaceUri, tagName)

        self._indentForbidden -= self._inNoIndent.pop()
        self._indentEndTag = not inline
        return

    def processingInstruction(self, target, data):
        if self._inElement:
            self.writeAscii('>')
            self._inElement = False

        # OK to indent end-tag
        self._indentEndTag = True

        # try to indent
        if not self._isInline[-1] and not self._indentForbidden:
            self.writeAscii('\n' + (self.indent * self._level))
        HtmlPrinter.processingInstruction(self, target, data)
        return

    def comment(self, data):
        if self._inElement:
            self.writeAscii('>')
            self._inElement = False

        # OK to indent end-tag
        self._indentEndTag = True

        # try to indent
        if not self._isInline[-1] and not self._indentForbidden:
            self.writeAscii('\n' + (self.indent * self._level))
        HtmlPrinter.comment(self, data)
        return

    # Elements that should never be emitted on a new line.
    inlineLocalNames = ['tt', 'i', 'b', 'u', 's', 'strike', 'big', 'small', 'em',
                 'strong', 'dfn', 'code', 'samp', 'kbd', 'var', 'cite',
                 'abbr', 'acronym', 'a', 'img', 'applet', 'object', 'font',
                 'basefont', 'script', 'map', 'q', 'sub', 'sup', 'span',
                 'bdo', 'iframe', 'input', 'select', 'textarea', 'label',
                 'button']
    inlineElements = {}
    for name in inlineLocalNames:
        inlineElements[(None, name)] = True
        inlineElements[(XHTML_NAMESPACE, name)] = True

    # Elements that should never be emitted with additional
    # whitespace in their content; i.e., once you're inside
    # one, you don't do any more indenting.
    noIndentElements = {}
    for name in ['script', 'style', 'pre', 'textarea', 'xmp']:
        noIndentElements[(None, name)] = True

    del name
