########################################################################
# amara/lib/treecompare.py
"""
Comparison functions for XML and HTML documents
(mainly used in the test suites)
"""
import re
import difflib
import itertools
import HTMLParser
from xml.parsers import expat

from amara.lib.xmlstring import isspace

_S = "[\x20\x09\x0D\x0A]"
_VersionNum = "[a-zA-Z0-9_.:-]+"
_Eq = "%s?=%s?" % (_S, _S)
_VersionInfo = _S + "version" + _Eq + \
               "(?:(?:'" + _VersionNum + "')|" + '(?:"' + _VersionNum + '"))'
_EncName = "[A-Za-z][A-Za-z0-9._-]*"
_EncodingDecl = _S + "encoding" + _Eq + \
                "(?:(?:'" + _EncName + "')|" + '(?:"' + _EncName + '"))'
_SDDecl = _S + "standalone" + _Eq + \
          "(?:(?:'(?:yes|no)')|" + '(?:"(?:yes|no)"))'
_xmldecl_find = re.compile(r"<\?xml" +
                           r"(?P<VersionInfo>%s)" % _VersionInfo +
                           r"(?P<EncodingDecl>%s)?" % _EncodingDecl +
                           r"(?P<SDDecl>%s)?" % _SDDecl +
                           r"%s?\?>" % _S)
_doctype_find = re.compile("<!DOCTYPE" + _S)
_starttag_find = re.compile("<[^!?]")
_html_find = re.compile("(<!DOCTYPE html)|(<html)", re.IGNORECASE)


def document_compare(expected, compared, whitespace=True):
    # See if we need to use XML or HTML
    if not _xmldecl_find.match(expected) and _html_find.search(expected):
        compare = html_compare
    else:
        compare = xml_compare
    return compare(expected, compared, whitespace)


def html_compare(expected, compared, whitespace=True):
    """
    Compare two HTML strings. Returns `True` if the two strings are
    equivalent, otherwise it returns `False`.
    """
    for line in html_diff(expected, compared, whitespace):
        # differences found
        return False
    # No differences
    return True


def html_diff(expected, compared, whitespace=True):
    """
    Compare two HTML strings; generate the delta as a unified diff.

    `ignorews` controls whether whitespace differences in text
    events are ignored.
    """
    expected = _html_sequence(expected, whitespace)
    compared = _html_sequence(compared, whitespace)
    return difflib.unified_diff(expected, compared, 'expected', 'compared')


def xml_compare(expected, compared, whitespace=True, lexical=True):
    """
    Compare two XML strings. Returns `True` if the two strings are
    equivalent, otherwise it returns `False`.
    """
    for line in xml_diff(expected, compared, whitespace):
        # differences found
        return False
    # No differences
    return True


def xml_diff(expected, compared, whitespace=True):
    # External Parsed Entities cannot have a standalone declaration or
    # DOCTYPE declaration.
    # See XML 1.0 2nd, 4.3.2, Well-Formed Parsed Entities
    match = _xmldecl_find.match(expected)
    if match and match.groupdict().get('SDDecl'):
        sequencer = _xml_sequence
    else:
        # Limit the search for DOCTYPE to the content before the first element.
        # If no elements exist, it *MUST* be a parsed entity.
        match = _starttag_find.search(expected)
        if match and _doctype_find.search(expected, 0, match.start()):
            sequencer = _xml_sequence
        else:
            sequencer = _entity_sequence
    expected = sequencer(expected, whitespace)
    compared = sequencer(compared, whitespace)
    return difflib.unified_diff(expected, compared, 'expected', 'compared')


def entity_compare(expected, compared, ignorews=False):
    return


class _markup_sequence(list):
    __slots__ = ('_whitespace', '_lexical', '_data')
    def __init__(self, data, whitespace=True, lexical=True):
        list.__init__(self)
        self._whitespace = whitespace
        self._lexical = lexical
        self._data = u''
        self.feed(data)
        self.close()
        self._flush()

    def _flush(self):
        data = self._data
        if data and self._whitespace or not isspace(data):
            self.append(('#text', data))
        self._data = u''


class _xml_sequence(_markup_sequence):
    __slots__ = ('_parser',)
    def __init__(self, data, whitespace=True, lexical=True):
        self._parser = parser = self._create_parser()
        parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
        parser.StartElementHandler = self.start_element
        parser.EndElementHandler = self.end_element
        parser.CharacterDataHandler = self.characters
        parser.ProcessingInstructionHandler = self.processing_instruction
        parser.StartNamespaceDeclHandler = self.namespace_decl
        parser.SkippedEntityHandler = self.skipped_entity
        if self._lexical:
            parser.CommentHandler = self.comment
            parser.StartCdataSectionHandler = self.start_cdata
            parser.EndCdataSectionHandler = self.end_cdata
            parser.StartDoctypeDeclHandler = self.doctype_decl
        _markup_sequence.__init__(self, whitespace, lexical)

    def _create_parser(self):
        return expat.ParserCreate(namespace_separator='#')

    def feed(self, data):
        self._parser.Parse(data, 0)

    def close(self):
        self._parser.Parse('', 1)
        # break cycle created by expat handlers pointing to our methods
        self._parser = None

    def namespace_decl(self, prefix, uri):
        if self._data: self._flush()
        self.append(('namespace', prefix, uri))

    def start_element(self, name, attrs):
        if self._data: self._flush()
        self.append(('start-tag', name, tuple(sorted(attrs.items()))))
        return

    def end_element(self, name):
        if self._data: self._flush()
        self.append(('end-tag', nsname))

    def characters(self, data):
        if data:
            self._data += data

    def processing_instruction(self, target, data):
        if self._data: self._flush()
        self.append(('processing-instruction', target, data))

    def skipped_entity(self, name):
        if self._data: self._flush()
        self.append(('entityref', name))

    def comment(self, data):
        if self._data: self._flush()
        self.append(('#comment', data))

    def start_cdata(self):
        if self._data: self._flush()
        self.append(('start-cdata',))

    def end_cdata(self):
        if self._data: self._flush()
        self.append(('end-cdata',))

    def doctype_decl(self, name, sysid, pubid, has_internal_subset):
        if self._data: self._flush()
        self.append(('doctype-decl', name, sysid, pubid, has_internal_subset))


class _entity_sequence(_xml_sequence):
    def _create_parser(self):
        parser = _xml_sequence._create_parser(self)
        context = 'xml=http://www.w3.org/XML/1998/namespace'
        return parser.ExternalEntityParserCreate(context)


class _html_sequence(HTMLParser.HTMLParser, _markup_sequence):

    _forbidden_end_elements = frozenset([
        'area', 'base', 'basefont', 'br', 'col', 'frame', 'hr',
        'img', 'input', 'isindex', 'link', 'meta', 'param',
        ])

    def __init__(self, data, whitespace=True, lexical=True):
        HTMLParser.HTMLParser.__init__(self)
        _markup_sequence.__init__(self, data, whitespace, lexical)

    def handle_starttag(self, tagname, attrs):
        if self._data: self._flush()
        self.append(('start-tag', tagname, tuple(sorted(attrs))))
        if tagname.lower() in self._forbidden_end_elements:
            self.append(('end-tag', tagname))
        return

    def handle_endtag(self, tag):
        if self._data: self._flush()
        # prevent duplicate end-tags if the HTML is malformed
        if tagname.lower() not in self._forbidden_end_elements:
            self.append(('end-tag', tag))

    def handle_charref(self, ref):
        if self._data: self._flush()
        self.append(('charref', ref))

    def handle_entityref(self, ref):
        if self._data: self._flush()
        self.append(('entityref', ref))

    def handle_data(self, data):
        if data:
            self._data += data

    def handle_comment(self, data):
        if self._lexical:
            if self._data: self._flush()
            self.append(('#comment', data))
