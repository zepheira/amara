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
_xmldecl_match = re.compile(r"<\?xml" +
                           r"(?P<VersionInfo>%s)" % _VersionInfo +
                           r"(?P<EncodingDecl>%s)?" % _EncodingDecl +
                           r"(?P<SDDecl>%s)?" % _SDDecl +
                           r"%s?\?>" % _S).match
_textdecl_match = re.compile(r"<\?xml" +
                             r"(?P<VersionInfo>%s)?" % _VersionInfo +
                             r"(?P<EncodingDecl>%s)" % _EncodingDecl +
                             r"%s?\?>" % _S).match
_doctype_find = re.compile("<!DOCTYPE" + _S).search
_starttag_find = re.compile("<[^!?]").search
_html_find = re.compile("(<!DOCTYPE html)|(<html)", re.IGNORECASE).search


def document_compare(expected, compared, whitespace=True):
    for line in document_diff(expected, compared, whitespace):
        # There is a difference
        return False
    return True


def document_diff(expected, compared, whitespace=True):
    # See if we need to use XML or HTML
    if not _xmldecl_match(expected) and _html_find(expected):
        diff = html_diff
    else:
        diff = xml_diff
    return diff(expected, compared, whitespace)


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
    return difflib.unified_diff(expected, compared, 'expected', 'compared',
                                n=2, lineterm='')


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
    sequencer = _xml_sequence
    if _textdecl_match(expected):
        # Limit the search for DOCTYPE to the content before the first element.
        # If no elements exist, it *MUST* be a parsed entity.
        match = _starttag_find(expected)
        if not match or not _doctype_find(expected, 0, match.start()):
            sequencer = _entity_sequence
    expected = sequencer(expected, whitespace)
    compared = sequencer(compared, whitespace)
    return difflib.unified_diff(expected, compared, 'expected', 'compared',
                                n=2, lineterm='')


def entity_compare(expected, compared, ignorews=False):
    return


class _markup_sequence(list):
    __slots__ = ('_data', '_nsdecls')
    def __init__(self, data, whitespace=True):
        list.__init__(self)
        if not whitespace:
            self._flush = self._flush_whitespace
        self._data = u''
        self._nsdecls = []
        self.feed(data)
        self.close()
        self._flush()

    def _flush(self):
        data = self._data
        if data:
            self.append('#text: ' + repr(data))
            self._data = u''

    def _flush_whitespace(self):
        data = self._data
        if data:
            if not isspace(data):
                self.append('#text: ' + repr(data))
            self._data = u''

    def namespace_decl(self, prefix, uri):
        self._nsdecls.append((prefix, uri))

    _prepare_attrs = sorted

    def start_element(self, name, attrs):
        if self._data: self._flush()
        self.append('start-tag: ' + name)
        if self._nsdecls:
            nsdecls = sorted(self._nsdecls)
            nsdecls = [ '%s=%r' % pair for pair in nsdecls ]
            self.append('  namespaces: ' + ', '.join(nsdecls))
            del self._nsdecls[:]
        if attrs:
            attrs = self._prepare_attrs(attrs)
            attrs = [ '%s=%r' % pair for pair in attrs ]
            self.append('  attributes: ' + ', '.join(attrs))
        return

    def end_element(self, name):
        if self._data: self._flush()
        self.append('end-tag: ' + name)

    def characters(self, data):
        if data:
            self._data += data

    def processing_instruction(self, target, data):
        if self._data: self._flush()
        event = 'processing-instruction: target=%s, data=%r' % (target, data)
        self.append(event)

    def entity_ref(self, name):
        if self._data: self._flush()
        self.append('entity-ref: name=' + name)

    def comment(self, data):
        if self._data: self._flush()
        self.append('#comment: ' + repr(data))

    def start_cdata(self):
        if self._data: self._flush()
        self.append('start-cdata')

    def end_cdata(self):
        if self._data: self._flush()
        self.append('end-cdata')

    def doctype_decl(self, name, sysid, pubid, has_internal_subset):
        if self._data: self._flush()
        event = 'doctype-decl: name=%s, sysid=%r, pubid=%r, subset=%s' % (
            name, sysid, pubid, ('yes' if has_internal_subset else 'no'))
        self.append(event)


class _xml_sequence(_markup_sequence):
    __slots__ = ('_parser',)
    def __init__(self, data, whitespace=True, lexical=True):
        self._parser = parser = self._create_parser()
        parser.ordered_attributes = True
        parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
        parser.StartElementHandler = self.start_element
        parser.EndElementHandler = self.end_element
        parser.CharacterDataHandler = self.characters
        parser.ProcessingInstructionHandler = self.processing_instruction
        parser.StartNamespaceDeclHandler = self.namespace_decl
        parser.SkippedEntityHandler = self.entity_ref
        if lexical:
            parser.CommentHandler = self.comment
            parser.StartCdataSectionHandler = self.start_cdata
            parser.EndCdataSectionHandler = self.end_cdata
            parser.StartDoctypeDeclHandler = self.doctype_decl
        _markup_sequence.__init__(self, data, whitespace)

    def _create_parser(self):
        return expat.ParserCreate(namespace_separator='#')

    def _prepare_attrs(self, attrs):
        it = iter(attrs)
        return sorted(itertools.izip(it, it))

    def feed(self, data):
        self._parser.Parse(data, 0)

    def close(self):
        self._parser.Parse('', 1)
        # break cycle created by expat handlers pointing to our methods
        self._parser = None


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
        if lexical:
            self.handle_comment = self.comment
        _markup_sequence.__init__(self, data, whitespace)

    handle_starttag = _markup_sequence.start_element
    handle_endtag = _markup_sequence.end_element
    handle_charref = _markup_sequence.entity_ref
    handle_entityref = _markup_sequence.entity_ref
    handle_data = _markup_sequence.characters
