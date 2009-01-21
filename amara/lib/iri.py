########################################################################
# $Header$
"""
Classes and functions related to IRI/URI processing, validation, resolution, etc.

Copyright 2004-2008 Uche Ogbuji
Detailed license and copyright information: http://4suite.org/COPYRIGHT
Project home, documentation, distributions: http://4suite.org/
"""

__all__ = [
  # IRI tools
  "iri_to_uri",
  "nfc_normalize",
  "convert_ireg_name",

  # RFC 3986 implementation
  'matches_uri_ref_syntax', 'matches_uri_syntax',
  'percent_encode', 'percent_decode',
  'split_uri_ref', 'unsplit_uri_ref',
  'split_authority', 'split_fragment',
  'absolutize', 'relativize', 'remove_dot_segments',
  'normalize_case', 'normalize_percent_encoding',
  'normalize_path_segments', 'normalize_path_segments_in_uri',

  # URI resolution
  'default_resolver',
  'DEFAULT_RESOLVER',
  'DEFAULT_URI_SCHEMES',
  'urlopen',

  # RFC 3151 implementation
  'urn_to_public_id', 'public_id_to_urn',

  # Miscellaneous
  'is_absolute', 'get_scheme', 'strip_fragment',
  'os_path_to_uri', 'uri_to_os_path', 'basejoin', 'join',
  'make_urllib_safe',
  'WINDOWS_SLASH_COMPAT',

  # 4Suite-specific
  'uridict', 'path_resolve',
]

import os, sys
import urllib, urllib2
import re, cStringIO
import mimetools
from string import ascii_letters
from email.Utils import formatdate as _formatdate
from uuid import UUID, uuid1, uuid4

from amara.lib import IriError, importutil

# whether os_path_to_uri should treat "/" same as "\" in a Windows path
WINDOWS_SLASH_COMPAT = True

# URI schemes supported by resolver_base
DEFAULT_URI_SCHEMES = ['http', 'https', 'file', 'ftp', 'data', 'pkgdata']
if not hasattr(urllib2, 'HTTPSHandler'):
    DEFAULT_URI_SCHEMES.remove('https')
DEFAULT_URI_SCHEMES = tuple(DEFAULT_URI_SCHEMES)


def iri_to_uri(iri, convertHost=False):
    r"""
    Converts an IRI or IRI reference to a URI or URI reference,
    implementing sec. 3.1 of draft-duerst-iri-10.

    The convertHost flag indicates whether to perform conversion of
    the ireg-name (host) component of the IRI to an RFC 2396-compatible
    URI reg-name (IDNA encoded), e.g.
    iri_to_uri(u'http://r\xe9sum\xe9.example.org/', convertHost=False)
    => u'http://r%C3%A9sum%C3%A9.example.org/'
    iri_to_uri(u'http://r\xe9sum\xe9.example.org/', convertHost=True)
    => u'http://xn--rsum-bpad.example.org/'

    Ordinarily, the IRI should be given as a unicode string. If the IRI
    is instead given as a byte string, then it will be assumed to be
    UTF-8 encoded, will be decoded accordingly, and as per the
    requirements of the conversion algorithm, will NOT be normalized.
    """
    if not isinstance(iri, str):
        iri = nfc_normalize(iri)

    if convertHost and sys.version_info[0:2] >= (2,3):
        # first we have to get the host
        (scheme, auth, path, query, frag) = split_uri_ref(iri)
        if auth and auth.find('@') > -1:
            userinfo, hostport = auth.split('@')
        else:
            userinfo = None
            hostport = auth
        if hostport and hostport.find(':') > -1:
            host, port = hostport.split(':')
        else:
            host = hostport
            port = None
        if host:
            host = convert_ireg_name(host)
            auth = ''
            if userinfo:
                auth += userinfo + '@'
            auth += host
            if port:
                auth += ':' + port
        iri = unsplit_uri_ref((scheme, auth, path, query, frag))

    res = u''
    pos = 0
    surrogate = None
    for c in iri:
        cp = ord(c)
        if cp > 128:
            if cp < 160:
                # FIXME: i18n
                raise ValueError("Illegal character at position %d (0-based) of IRI %r" % (pos, iri))
            # 'for c in iri' may give us surrogate pairs
            elif cp > 55295:
                if cp < 56320:
                    # d800-dbff
                    surrogate = c
                    continue
                elif cp < 57344:
                    # dc00-dfff
                    if surrogate is None:
                        raise ValueError("Illegal surrogate pair in %r" % iri)
                    c = surrogate + c
                else:
                    raise ValueError("Illegal surrogate pair in %r" % iri)
                surrogate = None
            for octet in c.encode('utf-8'):
                res += u'%%%02X' % ord(octet)
        else:
            res += c
        pos += 1
    return res


def nfc_normalize(iri):
    """
    On Python 2.3 and higher, normalizes the given unicode string
    according to Unicode Normalization Form C (NFC), so that it can
    be used as an IRI or IRI reference.
    """
    try:
        from unicodedata import normalize
        iri = normalize('NFC', iri)
    except ImportError:
        pass
    return iri


def convert_ireg_name(iregname):
    """
    On Python 2.3 and higher, converts the given ireg-name component
    of an IRI to a string suitable for use as a URI reg-name in pre-
    rfc2396bis schemes and resolvers. Returns the ireg-name
    unmodified on Python 2.2.
    """
    try:
        # I have not yet verified that the default IDNA encoding
        # matches the algorithm required by the IRI spec, but it
        # does work on the one simple example in the spec.
        iregname = iregname.encode('idna')
    except:
        pass
    return iregname


#=============================================================================
# Functions that implement aspects of RFC 3986
#
_validation_setup_completed = False
def _init_uri_validation_regex():
    """
    Called internally to compile the regular expressions needed by
    URI validation functions, just once, the first time a function
    that needs them is called.
    """
    global _validation_setup_completed
    if _validation_setup_completed:
        return

    #-------------------------------------------------------------------------
    # Regular expressions for determining the non-URI-ness of strings
    #
    # A given string's designation as a URI or URI reference comes from the
    # context in which it is being used, not from its syntax; a regular
    # expression can at most only determine whether a given string COULD be a
    # URI or URI reference, based on its lexical structure.
    #
    # 1. Altova's regex (in the public domain; courtesy Altova)
    #
    # # based on the BNF grammar in the original RFC 2396
    # ALTOVA_REGEX = r"(([a-zA-Z][0-9a-zA-Z+\-\.]*:)?/{0,2}" + \
    #                r"[0-9a-zA-Z;/?:@&=+$\.\-_!~*'()%]+)?" + \
    #                r"(#[0-9a-zA-Z;/?:@&=+$\.\-_!~*'()%]+)?"
    #
    # This regex matches URI references, and thus URIs as well. It is also
    # lenient; some strings that are not URI references can falsely match.
    #
    # It is also not very useful as-is, because it essentially has the form
    # (group1)?(group2)? -- this matches the empty string, and in fact any
    # string or substring can be said to match this pattern. To be useful,
    # this regex (and any like it) must be changed so that it only matches
    # an entire string. This is accomplished in Python by using the \A and \Z
    # delimiters around the pattern:
    #
    # BETTER_ALTOVA_REGEX = r"\A(?!\n)%s\Z" % ALTOVA_REGEX
    #
    # The (?!\n) takes care of an edge case where a string consisting of a
    # sole linefeed character would falsely match.
    #
    # 2. Python regular expressions for strict validation of URIs and URI
    #    references (in the public domain; courtesy Fourthought, Inc.)
    #
    # Note that we do not use any \d or \w shortcuts, as these are
    # potentially locale or Unicode sensitive.
    #
    # # based on the ABNF in RFC 3986,
    # # "Uniform Resource Identifier (URI): Generic Syntax"
    pchar           = r"(?:[0-9A-Za-z\-_\.!~*'();:@&=+$,]|(?:%[0-9A-Fa-f]{2}))"
    fragment        = r"(?:[0-9A-Za-z\-_\.!~*'();:@&=+$,/?]|(?:%[0-9A-Fa-f]{2}))*"
    query           = fragment
    segment_nz_nc   = r"(?:[0-9A-Za-z\-_\.!~*'();@&=+$,]|(?:%[0-9A-Fa-f]{2}))+"
    segment_nz      = r'%s+' % pchar
    segment         = r'%s*' % pchar
    #path_empty      = r''  # zero characters
    path_rootless   = r'%s(?:/%s)*' % (segment_nz, segment)   # begins with a segment
    path_noscheme   = r'%s(?:/%s)*' % (segment_nz_nc, segment)  # begins with a non-colon segment
    path_absolute   = r'/(?:%s)?' % path_rootless  # begins with "/" but not "//"
    path_abempty    = r'(?:/%s)*' % segment   # begins with "/" or is empty
    #path            = r'(?:(?:%s)|(?:%s)|(?:%s)|(?:%s))?' % (path_abempty, path_absolute, path_noscheme, path_rootless)
    domainlabel     = r'[0-9A-Za-z](?:[0-9A-Za-z\-]{0,61}[0-9A-Za-z])?'
    qualified       = r'(?:\.%s)*\.?' % domainlabel
    reg_name        = r"(?:(?:[0-9A-Za-z\-_\.!~*'();&=+$,]|(?:%[0-9A-Fa-f]{2}))*)"
    dec_octet       = r'(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])'
    IPv4address     = r'(?:%s\.){3}(?:%s)' % (dec_octet, dec_octet)
    h16             = r'[0-9A-Fa-f]{1,4}'
    ls32            = r'(?:(?:%s:%s)|%s)' % (h16, h16, IPv4address)
    IPv6address     = r'(?:' + \
                      r'(?:(?:%s:){6}%s)' % (h16, ls32) + \
                      r'|(?:::(?:%s:){5}%s)' % (h16, ls32) + \
                      r'|(?:%s?::(?:%s:){4}%s)' % (h16, h16, ls32) + \
                      r'|(?:(?:(?:%s:)?%s)?::(?:%s:){3}%s)' % (h16, h16, h16, ls32) + \
                      r'|(?:(?:(?:%s:)?%s){0,2}::(?:%s:){2}%s)' % (h16, h16, h16, ls32) + \
                      r'|(?:(?:(?:%s:)?%s){0,3}::%s:%s)' % (h16, h16, h16, ls32) + \
                      r'|(?:(?:(?:%s:)?%s){0,4}::%s)' % (h16, h16, ls32) + \
                      r'|(?:(?:(?:%s:)?%s){0,5}::%s)' % (h16, h16, h16) + \
                      r'|(?:(?:(?:%s:)?%s){0,6}::)' % (h16, h16) + \
                      r')'
    IPvFuture       = r"(?:v[0-9A-Fa-f]+\.[0-9A-Za-z\-\._~!$&'()*+,;=:]+)"
    IP_literal      = r'\[(?:%s|%s)\]' % (IPv6address, IPvFuture)
    port            = r'[0-9]*'
    host            = r'(?:%s|%s|%s)?' % (IP_literal, IPv4address, reg_name)
    userinfo        = r"(?:[0-9A-Za-z\-_\.!~*'();:@&=+$,]|(?:%[0-9A-Fa-f]{2}))*"
    authority       = r'(?:%s@)?%s(?::%s)?' % (userinfo, host, port)
    scheme          = r'[A-Za-z][0-9A-Za-z+\-\.]*'
    #absolute_URI    = r'%s:%s(?:\?%s)?' % (scheme, hier_part, query)
    relative_part   = r'(?:(?://%s%s)|(?:%s)|(?:%s))?' % (authority, path_abempty,
                                                          path_absolute, path_noscheme)
    relative_ref    = r'%s(?:\?%s)?(?:#%s)?' % (relative_part, query, fragment)
    hier_part       = r'(?:(?://%s%s)|(?:%s)|(?:%s))?' % (authority, path_abempty,
                                                          path_absolute, path_rootless)
    URI             = r'%s:%s(?:\?%s)?(?:#%s)?' % (scheme, hier_part, query, fragment)
    URI_reference   = r'(?:%s|%s)' % (URI, relative_ref)

    STRICT_URI_PYREGEX = r"\A%s\Z" % URI
    STRICT_URIREF_PYREGEX = r"\A(?!\n)%s\Z" % URI_reference

    global URI_PATTERN, URI_REF_PATTERN
    URI_PATTERN = re.compile(STRICT_URI_PYREGEX)        # strict checking for URIs
    URI_REF_PATTERN = re.compile(STRICT_URIREF_PYREGEX) # strict checking for URI refs
    _validation_setup_completed = True
    return


def matches_uri_ref_syntax(s):
    """
    This function returns true if the given string could be a URI reference,
    as defined in RFC 3986, just based on the string's syntax.

    A URI reference can be a URI or certain portions of one, including the
    empty string, and it can have a fragment component.
    """
    if not _validation_setup_completed:
        _init_uri_validation_regex()
    return URI_REF_PATTERN.match(s) is not None


def matches_uri_syntax(s):
    """
    This function returns true if the given string could be a URI, as defined
    in RFC 3986, just based on the string's syntax.

    A URI is by definition absolute (begins with a scheme) and does not end
    with a #fragment. It also must adhere to various other syntax rules.
    """
    if not _validation_setup_completed:
        _init_uri_validation_regex()
    return URI_PATTERN.match(s) is not None


_split_uri_ref_setup_completed = False
def _init_split_uri_ref_pattern():
    """
    Called internally to compile the regular expression used by
    split_uri_ref() just once, the first time the function is called.
    """
    global _split_uri_ref_setup_completed
    if _split_uri_ref_setup_completed:
        return

    # Like the others, this regex is also in the public domain.
    # It is based on this one, from RFC 3986 appendix B
    # (unchanged from RFC 2396 appendix B):
    # ^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?
    regex = r"^(?:(?P<scheme>[^:/?#]+):)?(?://(?P<authority>[^/?#]*))?(?P<path>[^?#]*)(?:\?(?P<query>[^#]*))?(?:#(?P<fragment>.*))?$"
    global SPLIT_URI_REF_PATTERN
    SPLIT_URI_REF_PATTERN = re.compile(regex)
    _split_uri_ref_setup_completed = True
    return


def split_uri_ref(uriref):
    """
    Given a valid URI reference as a string, returns a tuple representing the
    generic URI components, as per RFC 3986 appendix B. The tuple's structure
    is (scheme, authority, path, query, fragment).

    All values will be strings (possibly empty) or None if undefined.

    Note that per RFC 3986, there is no distinction between a path and
    an "opaque part", as there was in RFC 2396.
    """
    if not _split_uri_ref_setup_completed:
        _init_split_uri_ref_pattern()
    # the pattern will match every possible string, so it's safe to
    # assume there's a groupdict method to call.
    g = SPLIT_URI_REF_PATTERN.match(uriref).groupdict()
    scheme      = g['scheme']
    authority   = g['authority']
    path        = g['path']
    query       = g['query']
    fragment    = g['fragment']
    return (scheme, authority, path, query, fragment)


def unsplit_uri_ref(uriRefSeq):
    """
    Given a sequence as would be produced by split_uri_ref(), assembles and
    returns a URI reference as a string.
    """
    if not isinstance(uriRefSeq, (tuple, list)):
        raise TypeError("sequence expected, got %s" % type(uriRefSeq))
    (scheme, authority, path, query, fragment) = uriRefSeq
    uri = ''
    if scheme is not None:
        uri += scheme + ':'
    if authority is not None:
        uri += '//' + authority
    uri += path
    if query is not None:
        uri += '?' + query
    if fragment is not None:
        uri += '#' + fragment
    return uri


_split_authority_setup_completed = False
def _init_split_authority_pattern():
    """
    Called internally to compile the regular expression used by
    split_authority() just once, the first time the function is called.
    """
    global _split_authority_setup_completed
    if _split_authority_setup_completed:
        return
    global SPLIT_AUTHORITY_PATTERN
    regex = r'(?:(?P<userinfo>[^@]*)@)?(?P<host>[^:]*)(?::(?P<port>.*))?'
    SPLIT_AUTHORITY_PATTERN = re.compile(regex)
    _split_authority_setup_completed = True
    return


def split_authority(authority):
    """
    Given a string representing the authority component of a URI, returns
    a tuple consisting of the subcomponents (userinfo, host, port). No
    percent-decoding is performed.
    """
    if not _split_authority_setup_completed:
        _init_split_authority_pattern()
    m = SPLIT_AUTHORITY_PATTERN.match(authority)
    if m:
        return m.groups()
    else:
        return (None, authority, None)


def split_fragment(uri):
    """
    Given a URI or URI reference, returns a tuple consisting of
    (base, fragment), where base is the portion before the '#' that
    precedes the fragment component.
    """
    # The only '#' in a legit URI will be the fragment separator,
    # but in the wild, people get sloppy. Assume the last '#' is it.
    pos = uri.rfind('#')
    if pos == -1:
        return (uri, uri[:0])
    else:
        return (uri[:pos], uri[pos+1:])


# "unreserved" characters are allowed in a URI, and do not have special
# meaning as delimiters of URI components or subcomponents. They may
# appear raw or percent-encoded, but percent-encoding is discouraged.
# This set of characters is sufficiently long enough that using a
# compiled regex is faster than using a string with the "in" operator.
#UNRESERVED_PATTERN = re.compile(r"[0-9A-Za-z\-\._~!*'()]") # RFC 2396
UNRESERVED_PATTERN = re.compile(r'[0-9A-Za-z\-\._~]') # RFC 3986

# "reserved" characters are allowed in a URI, but they may or always do
# have special meaning as delimiters of URI components or subcomponents.
# When being used as delimiters, they must be raw, and when not being
# used as delimiters, they must be percent-encoded.
# This set of characters is sufficiently short enough that using a
# string with the "in" operator is faster than using a compiled regex.
# The characters in the string are ordered according to how likely they
# are to be found (approximately), for faster operation with "in".
#RESERVED = "/&=+?;@,:$[]" # RFC 2396 + RFC 2732
RESERVED = "/=&+?#;@,:$!*[]()'" # RFC 3986

# workaround for Py 2.2 bytecode issue; see
# http://mail.python.org/pipermail/python-list/2005-March/269948.html
SURR_DC00 = unichr(0xdc00)

def _chars(s):
    """
    This generator function helps iterate over the characters in a
    string. When the string is unicode and a surrogate pair is
    encountered, the pair is returned together, regardless of whether
    Python was built with 32-bit ('wide') or 16-bit code values for
    its internal representation of unicode. This function will raise a
    ValueError if it detects an illegal surrogate pair.

    For example, given s = u'\ud800\udc00\U00010000',
    with narrow-char unicode, "for c in s" normally iterates 4 times,
    producing u'\ud800', u'\udc00', 'u\ud800', u'\udc00', while
    "for c in _chars(s)" will iterate 2 times: producing
    u'\ud800\udc00' both times; and with wide-char unicode,
    "for c in s" iterates 3 times, producing u'\ud800', u'\udc00',
    and u'\U00010000', while "for c in _chars(s)" will iterate 2 times,
    producing u'\U00010000' both times.

    With this function, the value yielded in each iteration is thus
    guaranteed to represent a single abstract character, allowing for
    ideal encoding by the built-in codecs, as is necessary when
    percent-encoding.
    """
    if isinstance(s, str):
        for i in s:
            yield i
        return
    s = iter(s)
    for i in s:
        if u'\ud7ff' < i < SURR_DC00:
            try:
                j = s.next()
            except StopIteration:
                raise ValueError("Bad pair: string ends after %r" % i)
            if SURR_DC00 <= j < u'\ue000':
                yield i + j
            else:
                raise ValueError("Bad pair: %r (bad second half)" % (i+j))
        elif SURR_DC00 <= i < u'\ue000':
                raise ValueError("Bad pair: %r (no first half)" % i)
        else:
            yield i


def percent_encode(s, encoding='utf-8', encodeReserved=True, spaceToPlus=False,
                     nlChars=None, reservedChars=RESERVED):
    """
    [*** Experimental API ***] This function applies percent-encoding, as
    described in RFC 3986 sec. 2.1, to the given string, in order to prepare
    the string for use in a URI. It replaces characters that are not allowed
    in a URI. By default, it also replaces characters in the reserved set,
    which normally includes the generic URI component delimiters ":" "/"
    "?" \"#\" "[" "]" "@" and the subcomponent delimiters "!" "$" "&" "\'" "("
    ")" "*" "+" "," ";" "=".

    Ideally, this function should be used on individual components or
    subcomponents of a URI prior to assembly of the complete URI, not
    afterward, because this function has no way of knowing which characters
    in the reserved set are being used for their reserved purpose and which
    are part of the data. By default it assumes that they are all being used
    as data, thus they all become percent-encoded.

    The characters in the reserved set can be overridden from the default by
    setting the reservedChars argument. The percent-encoding of characters
    in the reserved set can be disabled by unsetting the encodeReserved flag.
    Do this if the string is an already-assembled URI or a URI component,
    such as a complete path.

    If the given string is Unicode, the name of the encoding given in the
    encoding argument will be used to determine the percent-encoded octets
    for characters that are not in the U+0000 to U+007F range. The codec
    identified by the encoding argument must return a byte string.

    If the given string is not Unicode, the encoding argument is ignored and
    the string is interpreted to represent literal octets, rather than
    characters. Octets above \\x7F will be percent-encoded as-is, e.g., \\xa0
    becomes %A0, not, say, %C2%A0.

    The spaceToPlus flag controls whether space characters are changed to
    "+" characters in the result, rather than being percent-encoded.
    Generally, this is not required, and given the status of "+" as a
    reserved character, is often undesirable. But it is required in certain
    situations, such as when generating application/x-www-form-urlencoded
    content or RFC 3151 public identifier URNs, so it is supported here.

    The nlChars argument, if given, is a sequence type in which each member
    is a substring that indicates a "new line". Occurrences of this substring
    will be replaced by '%0D%0A' in the result, as is required when generating
    application/x-www-form-urlencoded content.

    This function is similar to urllib.quote(), but is more conformant and
    Unicode-friendly. Suggestions for improvements welcome.
    """
    res = ''
    is_unicode = isinstance(s, unicode)
    if nlChars is not None:
        for c in nlChars:
            s.replace(c, '\r\n')
    for c in _chars(s):
        # surrogates? -> percent-encode according to given encoding
        if is_unicode and len(c) - 1:
            for octet in c.encode(encoding):
                res += '%%%02X' % ord(octet)
        # not unreserved?
        elif UNRESERVED_PATTERN.match(c) is None:
            cp = ord(c)
            # ASCII range?
            if cp < 128:
                # space? -> plus if desired
                if spaceToPlus and c == ' ':
                    res += '+'
                # reserved? -> percent-encode if desired
                elif c in reservedChars:
                    if encodeReserved:
                        res += '%%%02X' % cp
                    else:
                        res += c
                # not unreserved or reserved, so percent-encode
                # FIXME: should percent-encode according to given encoding;
                # ASCII range is not special!
                else:
                    res += '%%%02X' % cp
            # non-ASCII-range unicode?
            elif is_unicode:
                # percent-encode according to given encoding
                for octet in c.encode(encoding):
                    res += '%%%02X' % ord(octet)
            # non-ASCII str; percent-encode the bytes
            else:
                for octet in c:
                    res += '%%%02X' % ord(octet)

        # unreserved -> safe to use as-is
        else:
            res += c
    return res


def percent_decode(s, encoding='utf-8', decodable=None):
    """
    [*** Experimental API ***] Reverses the percent-encoding of the given
    string.

    This function is similar to urllib.unquote(), but can also process a
    Unicode string, not just a regular byte string.

    By default, all percent-encoded sequences are decoded, but if a byte
    string is given via the 'decodable' argument, only the sequences
    corresponding to those octets will be decoded.

    If the string is Unicode, the percent-encoded sequences are converted to
    bytes, then converted back to Unicode according to the encoding given in
    the encoding argument. For example, by default, u'abc%E2%80%A2' will be
    converted to u'abc\u2022', because byte sequence E2 80 A2 represents
    character U+2022 in UTF-8.

    If the string is not Unicode, the percent-encoded octets are just
    converted to bytes, and the encoding argument is ignored. For example,
    'abc%E2%80%A2' will be converted to 'abc\xe2\x80\xa2'.

    This function is intended for use on the portions of a URI that are
    delimited by reserved characters (see percent_encode), or on a value from
    data of media type application/x-www-form-urlencoded.
    """
    # Most of this comes from urllib.unquote().
    # urllib.unquote(), if given a unicode argument, does not decode
    # percent-encoded octets above %7F.
    is_unicode = isinstance(s, unicode)
    if is_unicode:
        mychr = unichr
    else:
        mychr = chr
    list_ = s.split('%')
    res = [list_[0]]
    myappend = res.append
    del list_[0]
    for item in list_:
        if item[1:2]:
            try:
                c = mychr(int(item[:2], 16))
                if decodable is None:
                    myappend(c + item[2:])
                elif c in decodable:
                    myappend(c + item[2:])
                else:
                    myappend('%' + item)
            except ValueError:
                myappend('%' + item)
        else:
            myappend('%' + item)
    s = ''.join(res)
    # If the original input was unicode, then we assume it represented
    # characters; e.g., u'%E2%80%A2' -> '\xe2\x80\xa2' -> u'\u2022'
    # (assuming UTF-8 was the basis for percent-encoding). However,
    # at this point in the implementation, variable s would actually be
    # u'\u00e2\u0080\u00a2', so we first convert it to bytes (via an
    # iso-8859-1 encode) in order to get '\xe2\x80\xa2'. Then we decode back
    # to unicode according to the desired encoding (UTF-8 by default) in
    # order to produce u'\u2022'.
    if is_unicode:
        s = s.encode('iso-8859-1').decode(encoding)
    return s


def absolutize(uriRef, baseUri):
    """
    Resolves a URI reference to absolute form, effecting the result of RFC
    3986 section 5. The URI reference is considered to be relative to the
    given base URI.

    It is the caller's responsibility to ensure that the base URI matches
    the absolute-URI syntax rule of RFC 3986, and that its path component
    does not contain '.' or '..' segments if the scheme is hierarchical.
    Unexpected results may occur otherwise.

    This function only conducts a minimal sanity check in order to determine
    if relative resolution is possible: it raises a IriError if the base
    URI does not have a scheme component. While it is true that the base URI
    is irrelevant if the URI reference has a scheme, an exception is raised
    in order to signal that the given string does not even come close to
    meeting the criteria to be usable as a base URI.

    It is the caller's responsibility to make a determination of whether the
    URI reference constitutes a "same-document reference", as defined in RFC
    2396 or RFC 3986. As per the spec, dereferencing a same-document
    reference "should not" involve retrieval of a new representation of the
    referenced resource. Note that the two specs have different definitions
    of same-document reference: RFC 2396 says it is *only* the cases where the
    reference is the empty string, or \"#\" followed by a fragment; RFC 3986
    requires making a comparison of the base URI to the absolute form of the
    reference (as is returned by the spec), minus its fragment component,
    if any.

    This function is similar to urlparse.urljoin() and urllib.basejoin().
    Those functions, however, are (as of Python 2.3) outdated, buggy, and/or
    designed to produce results acceptable for use with other core Python
    libraries, rather than being earnest implementations of the relevant
    specs. Their problems are most noticeable in their handling of
    same-document references and 'file:' URIs, both being situations that
    come up far too often to consider the functions reliable enough for
    general use.
    """
    # Reasons to avoid using urllib.basejoin() and urlparse.urljoin():
    # - Both are partial implementations of long-obsolete specs.
    # - Both accept relative URLs as the base, which no spec allows.
    # - urllib.basejoin() mishandles the '' and '..' references.
    # - If the base URL uses a non-hierarchical or relative path,
    #    or if the URL scheme is unrecognized, the result is not
    #    always as expected (partly due to issues in RFC 1808).
    # - If the authority component of a 'file' URI is empty,
    #    the authority component is removed altogether. If it was
    #    not present, an empty authority component is in the result.
    # - '.' and '..' segments are not always collapsed as well as they
    #    should be (partly due to issues in RFC 1808).
    # - Effective Python 2.4, urllib.basejoin() *is* urlparse.urljoin(),
    #    but urlparse.urljoin() is still based on RFC 1808.

    # This procedure is based on the pseudocode in RFC 3986 sec. 5.2.
    #
    # ensure base URI is absolute
    if not baseUri or not is_absolute(baseUri):
        raise IriError(IriError.RELATIVE_BASE_URI,
                           base=baseUri, ref=uriRef)
    # shortcut for the simplest same-document reference cases
    if uriRef == '' or uriRef[0] == '#':
        return baseUri.split('#')[0] + uriRef
    # ensure a clean slate
    tScheme = tAuth = tPath = tQuery = None
    # parse the reference into its components
    (rScheme, rAuth, rPath, rQuery, rFrag) = split_uri_ref(uriRef)
    # if the reference is absolute, eliminate '.' and '..' path segments
    # and skip to the end
    if rScheme is not None:
        tScheme = rScheme
        tAuth = rAuth
        tPath = remove_dot_segments(rPath)
        tQuery = rQuery
    else:
        # the base URI's scheme, and possibly more, will be inherited
        (bScheme, bAuth, bPath, bQuery, bFrag) = split_uri_ref(baseUri)
        # if the reference is a net-path, just eliminate '.' and '..' path
        # segments; no other changes needed.
        if rAuth is not None:
            tAuth = rAuth
            tPath = remove_dot_segments(rPath)
            tQuery = rQuery
        # if it's not a net-path, we need to inherit pieces of the base URI
        else:
            # use base URI's path if the reference's path is empty
            if not rPath:
                tPath = bPath
                # use the reference's query, if any, or else the base URI's,
                tQuery = rQuery is not None and rQuery or bQuery
            # the reference's path is not empty
            else:
                # just use the reference's path if it's absolute
                if rPath[0] == '/':
                    tPath = remove_dot_segments(rPath)
                # merge the reference's relative path with the base URI's path
                else:
                    if bAuth is not None and not bPath:
                        tPath = '/' + rPath
                    else:
                        tPath = bPath[:bPath.rfind('/')+1] + rPath
                    tPath = remove_dot_segments(tPath)
                # use the reference's query
                tQuery = rQuery
            # since the reference isn't a net-path,
            # use the authority from the base URI
            tAuth = bAuth
        # inherit the scheme from the base URI
        tScheme = bScheme
    # always use the reference's fragment (but no need to define another var)
    #tFrag = rFrag

    # now compose the target URI (RFC 3986 sec. 5.3)
    return unsplit_uri_ref((tScheme, tAuth, tPath, tQuery, rFrag))


def relativize(targetUri, againstUri, subPathOnly=False):
    """
    This method returns a relative URI that is consistent with `targetURI`
    when resolved against `againstUri`.  If no such relative URI exists, for
    whatever reason, this method returns `None`.

    To be precise, if a string called `rel` exists such that
    ``absolutize(rel, againstUri) == targetUri``, then `rel` is returned by
    this function.  In these cases, `relativize` is in a sense the inverse
    of `absolutize`.  In all other cases, `relativize` returns `None`.

    The following idiom may be useful for obtaining compliant relative
    reference strings (e.g. for `path`) for use in other methods of this
    package::

      path = relativize(os_path_to_uri(path), os_path_to_uri('.'))

    If `subPathOnly` is `True`, then this method will only return a relative
    reference if such a reference exists relative to the last hierarchical
    segment of `againstUri`.  In particular, this relative reference will
    not start with '/' or '../'.
    """

    # We might want to change the semantics slightly to allow a relative
    # target URI to be a valid "relative path" (and just return it).  For
    # now, though, absolute URIs only.
    #
    # TODO: We also need to decide if/when we want to use exceptions instead
    # of returning `None`.
    if not is_absolute(targetUri) or not is_absolute(againstUri):
        return None

    targetUri = normalize_path_segments_in_uri(targetUri)
    againstUri = normalize_path_segments_in_uri(againstUri)

    splitTarget = list(split_uri_ref(absolutize(targetUri, targetUri)))
    splitAgainst = list(split_uri_ref(absolutize(againstUri, againstUri)))

    if not splitTarget[:2] == splitAgainst[:2]:
        return None

    subPathSplit = [None, None] + splitTarget[2:]

    targetPath = splitTarget[2]
    againstPath = splitAgainst[2]

    leadingSlash = False
    if targetPath[:1] == '/' or againstPath[:1] == '/':
        if targetPath[:1] == againstPath[:1]:
            targetPath = targetPath[1:]
            againstPath = againstPath[1:]
            leadingSlash = True
        else:
            return None

    targetPathSegments = targetPath.split('/')
    againstPathSegments = againstPath.split('/')

    # Count the number of path segments in common.
    i = 0
    while True:
        # Stop if we get to the end of either segment list.
        if not(len(targetPathSegments) > i and
               len(againstPathSegments) > i):
            break

        # Increment the count when the lists agree, unless we are at the
        # last segment of either list and that segment is an empty segment.
        # We bail on this case because an empty ending segment in one path
        # must not match a mid-path empty segment in the other.
        if (targetPathSegments[i] == againstPathSegments[i]
            and not (i + 1 == len(againstPathSegments) and
                     '' == againstPathSegments[i])
            and not (i + 1 == len(targetPathSegments) and
                     '' == targetPathSegments[i])):
            i = i + 1
        # Otherwise stop.
        else:
            break

    # The target path has `i` segments in common with the basis path, and
    # the last segment (after the final '/') doesn't matter; we'll need to
    # traverse the rest.
    traverse = len(againstPathSegments) - i - 1

    relativePath = None
    # If the two paths do not agree on any segments, we have two special
    # cases.
    if i == 0 and leadingSlash:
        # First, if the ruling path only had one segment, then our result
        # can be a relative path.
        if len(againstPathSegments) == 1:
            relativePath = targetPath
        # Otherwise, the ruling path had a number of segments, so our result
        # must be an absolute path (unless we only want a subpath result, in
        # which case none exists).
        elif subPathOnly:
            return None
        else:
            relativePath = '/' + targetPath
    elif traverse > 0:
        if subPathOnly:
            return None
        relativePath = (("../" * traverse) +
                        '/'.join(targetPathSegments[i:]))
    # If the ith segment of the target path is empty and that is not the
    # final segment, then we need to precede the path with "./" to make it a
    # relative path.
    elif (len(targetPathSegments) > i + 1 and
          '' == targetPathSegments[i]):
        relativePath = "./" + '/'.join(targetPathSegments[i:])
    else:
        relativePath = '/'.join(targetPathSegments[i:])

    return unsplit_uri_ref([None, None, relativePath] + splitTarget[3:])


def remove_dot_segments(path):
    """
    Supports absolutize() by implementing the remove_dot_segments function
    described in RFC 3986 sec. 5.2.  It collapses most of the '.' and '..'
    segments out of a path without eliminating empty segments. It is intended
    to be used during the path merging process and may not give expected
    results when used independently. Use normalize_path_segments() or
    normalize_path_segments_in_uri() if more general normalization is desired.
    """
    # return empty string if entire path is just "." or ".."
    if path == '.' or path == '..':
        return path[0:0] # preserves string type
    # remove all "./" or "../" segments at the beginning
    while path:
        if path[:2] == './':
            path = path[2:]
        elif path[:3] == '../':
            path = path[3:]
        else:
            break
    # We need to keep track of whether there was a leading slash,
    # because we're going to drop it in order to prevent our list of
    # segments from having an ambiguous empty first item when we call
    # split().
    leading_slash = False
    if path[:1] == '/':
        path = path[1:]
        leading_slash = True
    # replace a trailing "/." with just "/"
    if path[-2:] == '/.':
        path = path[:-1]
    # convert the segments into a list and process each segment in
    # order from left to right.
    segments = path.split('/')
    keepers = []
    segments.reverse()
    while segments:
        seg = segments.pop()
        # '..' means drop the previous kept segment, if any.
        # If none, and if the path is relative, then keep the '..'.
        # If the '..' was the last segment, ensure
        # that the result ends with '/'.
        if seg == '..':
            if keepers:
                keepers.pop()
            elif not leading_slash:
                keepers.append(seg)
            if not segments:
                keepers.append('')
        # ignore '.' segments and keep all others, even empty ones
        elif seg != '.':
            keepers.append(seg)
    # reassemble the kept segments
    return leading_slash * '/' + '/'.join(keepers)


def normalize_case(uriRef, doHost=False):
    """
    Returns the given URI reference with the case of the scheme,
    percent-encoded octets, and, optionally, the host, all normalized,
    implementing section 6.2.2.1 of RFC 3986. The normal form of
    scheme and host is lowercase, and the normal form of
    percent-encoded octets is uppercase.

    The URI reference can be given as either a string or as a sequence as
    would be provided by the split_uri_ref function. The return value will
    be a string or tuple.
    """
    if not isinstance(uriRef, (tuple, list)):
        uriRef = split_uri_ref(uriRef)
        tup = None
    else:
        tup = True
    # normalize percent-encoded octets
    newRef = []
    for component in uriRef:
        if component:
            newRef.append(re.sub('%([0-9a-f][0-9a-f])',
                          lambda m: m.group(0).upper(), component))
        else:
            newRef.append(component)
    # normalize scheme
    scheme = newRef[0]
    if scheme:
        scheme = scheme.lower()
    # normalize host
    authority = newRef[1]
    if doHost:
        if authority:
            userinfo, host, port = split_authority(authority)
            authority = ''
            if userinfo is not None:
                authority += '%s@' % userinfo
            authority += host.lower()
            if port is not None:
                authority += ':%s' % port

    res = (scheme, authority, newRef[2], newRef[3], newRef[4])
    if tup:
        return res
    else:
        return unsplit_uri_ref(res)


def normalize_percent_encoding(s):
    """
    Given a string representing a URI reference or a component thereof,
    returns the string with all percent-encoded octets that correspond to
    unreserved characters decoded, implementing section 6.2.2.2 of RFC
    3986.
    """
    return percent_decode(s, decodable='0123456789%s-._~' % ascii_letters)


def normalize_path_segments(path):
    """
    Given a string representing the path component of a URI reference having a
    hierarchical scheme, returns the string with dot segments ('.' and '..')
    removed, implementing section 6.2.2.3 of RFC 3986. If the path is
    relative, it is returned with no changes.
    """
    if not path or path[:1] != '/':
        return path
    else:
        return remove_dot_segments(path)


def normalize_path_segments_in_uri(uri):
    """
    Given a string representing a URI or URI reference having a hierarchical
    scheme, returns the string with dot segments ('.' and '..') removed from
    the path component, implementing section 6.2.2.3 of RFC 3986. If the
    path is relative, the URI or URI reference is returned with no changes.
    """
    components = list(split_uri_ref(uri))
    components[2] = normalize_path_segments(components[2])
    return unsplit_uri_ref(components)


#=============================================================================
# Resolvers provide normalization and resolution functions for URI references
#
class default_resolver:
    """
    This is class provides a set of functions related to the resolution of
    URIs, including the resolution to absolute form of URI references, and
    the retrieval of a representation of a resource that is identified by a
    URI.

    The object attribute supportedSchemes is a list of URI schemes supported
    for dereferencing (representation retrieval). Schemes supported by
    default are: %s.
    """ % ', '.join(DEFAULT_URI_SCHEMES)
    def __init__(self, lenient=True):
        self.lenient = lenient
        self.supportedSchemes = list(DEFAULT_URI_SCHEMES)
        self.sep = '/' #Bad value for data URIs

    def normalize(self, uriRef, baseUri):
        """
        Resolves a URI reference to absolute form, effecting the result of RFC
        3986 section 5. The URI reference is considered to be relative to
        the given base URI.

        Also verifies that the resulting URI reference has a scheme that
        resolve() supports, raising a IriError if it doesn't.

        The default implementation does not perform any validation on the base
        URI beyond that performed by absolutize().

        If leniency has been turned on (self.lenient=True), accepts a base URI
        beginning with '/', in which case the argument is assumed to be an absolute
        path component of 'file' URI with no authority component.
        """
        # since we know how absolutize works, we can anticipate the scheme of
        # its return value and verify that it's supported first
        if self.lenient:
            # assume file: if leading "/"
            if baseUri.startswith('/'):
                baseUri = 'file://' + baseUri
        scheme = get_scheme(uriRef) or get_scheme(baseUri)
        if scheme in self.supportedSchemes:
            return absolutize(uriRef, baseUri)
        else:
            if scheme is None:
                raise ValueError('When the URI to resolve is a relative '
                    'reference, it must be accompanied by a base URI.')
            else:
                raise IriError(IriError.UNSUPPORTED_SCHEME,
                                   scheme=scheme,
                                   resolver=self.__class__.__name__)

    def resolve(self, uri, baseUri=None):
        """
        This function takes a URI or a URI reference plus a base URI, produces
        a normalized URI using the normalize function if a base URI was given,
        then attempts to obtain access to an entity representing the resource
        identified by the resulting URI, returning the entity as a stream (a
        Python file-like object).

        Raises a IriError if the URI scheme is unsupported or if a stream
        could not be obtained for any reason.
        """
        if baseUri is not None:
            uri = self.normalize(uri, baseUri)
            scheme = get_scheme(uri)
        else:
            scheme = get_scheme(uri)
            # since we didn't use normalize(), we need to verify here
            if scheme not in self.supportedSchemes:
                if scheme is None:
                    raise ValueError('When the URI to resolve is a relative '
                        'reference, it must be accompanied by a base URI.')
                else:
                    raise IriError(IriError.UNSUPPORTED_SCHEME,
                                       scheme=scheme,
                                       resolver=self.__class__.__name__)

        # Bypass urllib for opening local files.
        if scheme == 'file':
            path = uri_to_os_path(uri, attemptAbsolute=False)
            try:
                stream = open(path, 'rb')
            except IOError, e:
                raise IriError(IriError.RESOURCE_ERROR,
                                   loc='%s (%s)' % (uri, path),
                                   uri=uri, msg=str(e))
            # Add the extra metadata that urllib normally provides (sans
            # the poorly guessed Content-Type header).
            stats = os.stat(path)
            size = stats.st_size
            mtime = _formatdate(stats.st_mtime)
            headers = mimetools.Message(cStringIO.StringIO(
                'Content-Length: %s\nLast-Modified: %s\n' % (size, mtime)))
            stream = urllib.addinfourl(stream, headers, uri)
        else:
            # urllib2.urlopen, wrapped by us, will suffice for http, ftp,
            # data and gopher
            try:
                stream = urlopen(uri)
            except IOError, e:
                raise IriError(IriError.RESOURCE_ERROR,
                                   uri=uri, loc=uri, msg=str(e))
        return stream

    def generate(self, hint=None):
        """
        This function generates and returns a URI.
        The hint is an object that helps decide what to generate.
        The default action is to generate a random UUID URN.
        """
        return uuid4().urn

    def join(self, *uriparts):
        """
        Merges a series of URI reference parts, returning a new URI reference.
    
        Much like iri.basejoin, but takes multiple arguments
    
        self.sep is a separator to place between path segments
        """
        if len(uriparts) == 0:
            raise TypeError("FIXME...")
        elif len(uriparts) == 1:
            return uriparts[0]
        else:
            base = uriparts[0]
            for part in uriparts[1:]:
                base = basejoin(base.rstrip(self.sep)+self.sep, part)
            return base


#Reusable resolver instance
DEFAULT_RESOLVER = default_resolver()

_urlopener = None
class _data_handler(urllib2.BaseHandler):
    """
    A class to handle 'data' URLs.

    The actual handling is done by urllib.URLopener.open_data() method.
    """
    def data_open(self, request):
        global _urlopener
        if _urlopener is None:
            _urlopener = urllib.URLopener()
        return _urlopener.open_data(self, request.get_full_url())

def resource_to_uri(package, resource):
    """Return a PEP 302 pseudo-URL for the specified resource.

    'package' is a Python module name (dot-separated module names) and
    'resource' is a '/'-separated pathname.
    """
    provider, resource_name = importutil.normalize_resource(package, resource)
    if provider.loader:
        # Use a 'pkgdata' (PEP 302) pseudo-URL
        segments = resource_name.split('/')
        if not resource.startswith('/'):
            dirname = provider.module_path[len(provider.zip_pre):]
            segments[0:0] = dirname.split(os.sep)
        path = '/'.join(map(percent_encode, segments))
        uri = 'pkgdata://%s/%s' % (package, path)
    else:
        # Use a 'file' URL
        filename = importutil.get_resource_filename(package, resource)
        uri = os_path_to_uri(filename)
    return uri

class _pep302_handler(urllib2.FileHandler):
    """
    A class to handler opening of PEP 302 pseudo-URLs.

    The syntax for this pseudo-URL is:
        url    := "pkgdata://" module "/" path
        module := <Python module name>
        path   := <'/'-separated pathname>

    The "path" portion of the URL will be passed to the get_data() method
    of the loader identified by "module" with '/'s converted to the OS
    native path separator.
    """
    def pep302_open(self, request):
        import mimetypes

        # get the package and resource components
        package = request.get_host()
        resource = request.get_selector()
        resource = percent_decode(re.sub('%2[fF]', '\\/', resource))

        # get the stream associated with the resource
        try:
            stream = importutil.get_resource_stream(package, resource)
        except EnvironmentError, error:
            raise urllib2.URLError(str(error))

        # compute some simple header fields
        try:
            stream.seek(0, 2) # go to the end of the stream
        except IOError:
            data = stream.read()
            stream = cStringIO.StringIO(data)
            length = len(data)
        else:
            length = stream.tell()
            stream.seek(0, 0) # go to the start of the stream
        mtime = importutil.get_resource_last_modified(package, resource)
        mtime = _formatdate(mtime)
        mtype = mimetypes.guess_type(resource) or 'text/plain'
        headers = ("Content-Type: %s\n"
                   "Content-Length: %d\n"
                   "Last-Modified: %s\n" % (mtype, length, mtime))
        headers = mimetools.Message(cStringIO.StringIO(headers))
        return urllib.addinfourl(stream, headers, request.get_full_url())

_opener = None
def urlopen(url, *args, **kwargs):
    """
    A replacement/wrapper for urllib2.urlopen().

    Simply calls make_urllib_safe() on the given URL and passes the result
    and all other args to urllib2.urlopen().
    """
    global _opener
    if _opener is None:
        _opener = urllib2.build_opener(_data_handler, _pep302_handler)

    # work around urllib's intolerance for proper URIs, Unicode, IDNs
    stream = _opener.open(make_urllib_safe(url), *args, **kwargs)
    stream.name = url
    return stream


#=============================================================================
# RFC 3151 implementation
#

def urn_to_public_id(urn):
    """
    Converts a URN that conforms to RFC 3151 to a public identifier.

    For example, the URN
    "urn:publicid:%2B:IDN+example.org:DTD+XML+Bookmarks+1.0:EN:XML"
    will be converted to the public identifier
    "+//IDN example.org//DTD XML Bookmarks 1.0//EN//XML"

    Raises a IriError if the given URN cannot be converted.
    Query and fragment components, if present, are ignored.
    """
    if urn is not None and urn:
        (scheme, auth, path, query, frag) = split_uri_ref(urn)
        if scheme is not None and scheme.lower() == 'urn':
            pp = path.split(':', 1)
            if len(pp) > 1:
                urn_scheme = percent_decode(pp[0])
                if urn_scheme == 'publicid':
                    publicid = pp[1].replace('+', ' ')
                    publicid = publicid.replace(':', '//')
                    publicid = publicid.replace(';', '::')
                    publicid = percent_decode(publicid)
                    return publicid

    raise IriError(IriError.INVALID_PUBLIC_ID_URN, urn=urn)


def public_id_to_urn(publicid):
    """
    Converts a public identifier to a URN that conforms to RFC 3151.
    """
    # 1. condense whitespace, XSLT-style
    publicid = re.sub('[ \t\r\n]+', ' ', publicid.strip())
    # 2. // -> :
    #    :: -> ;
    #    space -> +
    #    + ; ' ? # % / : -> percent-encode
    #    (actually, the intent of the RFC is to not conflict with RFC 2396,
    #     so any character not in the unreserved set must be percent-encoded)
    r = ':'.join([';'.join([percent_encode(dcpart, spaceToPlus=True)
                            for dcpart in dspart.split('::')])
                  for dspart in publicid.split('//')])
    return 'urn:publicid:%s' % r


#=============================================================================
# Miscellaneous public functions
#

SCHEME_PATTERN = re.compile(r'([a-zA-Z][a-zA-Z0-9+\-.]*):')
def get_scheme(uriRef):
    """
    Obtains, with optimum efficiency, just the scheme from a URI reference.
    Returns a string, or if no scheme could be found, returns None.
    """
    # Using a regex seems to be the best option. Called 50,000 times on
    # different URIs, on a 1.0-GHz PIII with FreeBSD 4.7 and Python
    # 2.2.1, this method completed in 0.95s, and 0.05s if there was no
    # scheme to find. By comparison,
    #   urllib.splittype()[0] took 1.5s always;
    #   Ft.Lib.Uri.split_uri_ref()[0] took 2.5s always;
    #   urlparse.urlparse()[0] took 3.5s always.
    m = SCHEME_PATTERN.match(uriRef)
    if m is None:
        return None
    else:
        return m.group(1)


def strip_fragment(uriRef):
    """
    Returns the given URI or URI reference with the fragment component, if
    any, removed.
    """
    return split_fragment(uriRef)[0]


def is_absolute(identifier):
    """
    Given a string believed to be a URI or URI reference, tests that it is
    absolute (as per RFC 3986), not relative -- i.e., that it has a scheme.
    """
    # We do it this way to avoid compiling another massive regex.
    return get_scheme(identifier) is not None


_ntPathToUriSetupCompleted = False
def _initNtPathPattern():
    """
    Called internally to compile the regular expression used by
    os_path_to_uri() on Windows just once, the first time the function is
    called.
    """
    global _ntPathToUriSetupCompleted
    if _ntPathToUriSetupCompleted:
        return
    # path variations we try to handle:
    #
    # a\b\c (a relative path)
    #    file:a/b/c is the best we can do.
    #    Dot segments should not be collapsed in the final URL.
    #
    # \a\b\c
    #    file:///a/b/c is correct
    #
    # C:\a\b\c
    #    urllib.urlopen() requires file:///C|/a/b/c or ///C|/a/b/c
    #     because it currently relies on urllib.url2pathname().
    #    Windows resolver will accept the first or file:///C:/a/b/c
    #
    # \\host\share\x\y\z
    #    Windows resolver accepts file://host/share/x/y/z
    #    Netscape (4.x?) accepts file:////host/share/x/y/z
    #
    # If an entire drive is shared, the share name might be
    #  $drive$, like this: \\host\$c$\a\b\c
    #  We could recognize it as a drive letter, but it's probably
    #  best not to treat it specially, since it will never occur
    #  without a host. It's just another share name.
    #
    # There's also a weird C:\\host\share\x\y\z convention
    #  that is hard to find any information on. Presumably the C:
    #  is ignored, but the question is do we put it in the URI?
    #
    # So the format, in ABNF, is roughly:
    # [ drive ":" ] ( [ "\\" host "\" share ] abs-path ) / rel-path
    drive         = r'(?P<drive>[A-Za-z])'
    host          = r'(?P<host>[^\\]*)'
    share         = r'(?P<share>[^\\]+)'
    abs_path      = r'(?P<abspath>\\(?:[^\\]+\\?)*)'
    rel_path      = r'(?P<relpath>(?:[^\\]+\\?)*)'
    NT_PATH_REGEX = r"^(?:%s:)?(?:(?:(?:\\\\%s\\%s)?%s)|%s)$" % (
                        drive,
                        host,
                        share,
                        abs_path,
                        rel_path)
    global NT_PATH_PATTERN
    NT_PATH_PATTERN = re.compile(NT_PATH_REGEX)
    # We can now use NT_PATH_PATTERN.match(path) to parse the path and use
    #  the returned object's .groupdict() method to get a dictionary of
    #  path subcomponents. For example,
    #  NT_PATH_PATTERN.match(r"\\h\$c$\x\y\z").groupdict()
    #  yields
    #  {'abspath': r'\x\y\z',
    #   'share': '$c$',
    #   'drive': None,
    #   'host': 'h',
    #   'relpath': None
    #  }
    # Note that invalid paths such as r'\\foo\bar'
    #  (a UNC path with no trailing '\') will not match at all.
    _ntPathToUriSetupCompleted = True
    return


def _splitNtPath(path):
    """
    Called internally to get a tuple representing components of the given
    Windows path.
    """
    if not _ntPathToUriSetupCompleted:
        _initNtPathPattern()
    m = NT_PATH_PATTERN.match(path)
    if not m:
        raise ValueError("Path %s is not a valid Windows path.")
    components = m.groupdict()
    (drive, host, share, abspath, relpath) = (
        components['drive'],
        components['host'],
        components['share'],
        components['abspath'],
        components['relpath'],
        )
    return (drive, host, share, abspath, relpath)


def _get_drive_letter(s):
    """
    Called internally to get a drive letter from a string, if the string
    is a drivespec.
    """
    if len(s) == 2 and s[1] in ':|' and s[0] in ascii_letters:
        return s[0]
    return


def os_path_to_uri(path, attemptAbsolute=True, osname=None):
    r"""This function converts an OS-specific file system path to a URI of
    the form 'file:///path/to/the/file'.

    In addition, if the path is absolute, any dot segments ('.' or '..') will
    be collapsed, so that the resulting URI can be safely used as a base URI
    by functions such as absolutize().

    The given path will be interpreted as being one that is appropriate for
    use on the local operating system, unless a different osname argument is
    given.

    If the given path is relative, an attempt may be made to first convert
    the path to absolute form by interpreting the path as being relative
    to the current working directory.  This is the case if the attemptAbsolute
    flag is True (the default).  If attemptAbsolute is False, a relative
    path will result in a URI of the form file:relative/path/to/a/file .

    attemptAbsolute has no effect if the given path is not for the
    local operating system.

    On Windows, the drivespec will become the first step in the path component
    of the URI. If the given path contains a UNC hostname, this name will be
    used for the authority component of the URI.

    Warning: Some libraries, such as urllib.urlopen(), may not behave as
    expected when given a URI generated by this function. On Windows you may
    want to call re.sub('(/[A-Za-z]):', r'\1|', uri) on the URI to prepare it
    for use by functions such as urllib.url2pathname() or urllib.urlopen().

    This function is similar to urllib.pathname2url(), but is more featureful
    and produces better URIs.
    """
    # Problems with urllib.pathname2url() on all platforms include:
    # - the generated URL has no scheme component;
    # - percent-encoding is incorrect, due to urllib.quote() issues.
    #
    # Problems with urllib.pathname2url() on Windows include:
    # - trailing backslashes are ignored;
    # - all leading backslashes are considered part of the absolute
    #    path, so UNC paths aren't properly converted (assuming that
    #    a proper conversion would be to use the UNC hostname in the
    #    hostname component of the resulting URL);
    # - non-leading, consecutive backslashes are collapsed, which may
    #    be desirable but is correcting what is, arguably, user error;
    # - the presence of a letter followed by ":" is believed to
    #    indicate a drivespec, no matter where it occurs in the path,
    #    which may have been considered a safe assumption since the
    #    drivespec is the only place where ":" can legally, but there's
    #    no need to search the whole string for it;
    # - the ":" in a drivespec is converted to "|", a convention that
    #    is becoming increasingly less common. For compatibility, most
    #    web browser resolvers will accept either "|" or ":" in a URL,
    #    but urllib.urlopen(), relying on url2pathname(), expects "|"
    #    only. In our opinion, the callers of those functions should
    #    ensure that the arguments are what are expected. Our goal
    #    here is to produce a quality URL, not a URL designed to play
    #    nice with urllib's bugs & limitations.
    # - it treats "/" the same as "\", which results in being able to
    #    call the function with a posix-style path, a convenience
    #    which allows the caller to get sloppy about whether they are
    #    really passing a path that is apprropriate for the desired OS.
    #    We do this a lot in 4Suite.
    #
    # There is some disagreement over whether a drivespec should be placed in
    # the authority or in the path. Placing it in the authority means that
    # ":", which has a reserved purpose in the authority, cannot be used --
    # this, along with the fact that prior to RFC 3986, percent-encoded
    # octets were disallowed in the authority, is presumably a reason why "|"
    # is a popular substitute for ":". Using the authority also allows for
    # the drive letter to be retained whe resolving references like this:
    #   reference '/a/b/c' + base 'file://C|/x/y/z' = 'file://C|/a/b/c'
    # The question is, is that really the ideal result? Should the drive info
    # be inherited from the base URI, if it is unspecified in a reference
    # that is otherwise representing an absolute path? Using the authority
    # for this purpose means that it would be overloaded if we also used it
    # to represent the host part of a UNC path. The alternative is to put the
    # UNC host in the path (e.g. 'file:////host/share/path'), but when such a
    # URI is used as a base URI, relative reference resolution often returns
    # unexpected results.
    #
    osname = osname or os.name

    if osname == 'nt':
        if WINDOWS_SLASH_COMPAT:
            path = path.replace('/','\\')
        (drive, host, share, abspath, relpath) = _splitNtPath(path)
        if attemptAbsolute and relpath is not None and osname == os.name:
            path = os.path.join(os.getcwd(), relpath)
            (drive, host, share, abspath, relpath) = _splitNtPath(path)
        path = abspath or relpath
        path = '/'.join([percent_encode(seg) for seg in path.split('\\')])
        uri = 'file:'
        if host:
            uri += '//%s' % percent_encode(host)
        elif abspath:
            uri += '//'
        if drive:
            uri += '/%s:' % drive.upper()
        if share:
            uri += '/%s' % percent_encode(share)
        if abspath:
            path = remove_dot_segments(path)
        uri += path

    elif osname == 'posix':
        try:
            from posixpath import isabs
        except ImportError:
            isabs = lambda p: p[:1] == '/'
        pathisabs = isabs(path)
        if pathisabs:
            path = remove_dot_segments(path)
        elif attemptAbsolute and osname == os.name:
            path = os.path.join(os.getcwd(), path)
            pathisabs = isabs(path)
        path = '/'.join([percent_encode(seg) for seg in path.split('/')])
        if pathisabs:
            uri = 'file://%s' % path
        else:
            uri = 'file:%s' % path

    else:
        # 4Suite only supports posix and nt, so we're not going to worry about
        # improving upon urllib.pathname2url() for other OSes.
        if osname == os.name:
            from urllib import pathname2url
            if attemptAbsolute and not os.path.isabs(path):
                path = os.path.join(os.getcwd(), path)
        else:
            try:
                module = '%surl2path' % osname
                exec 'from %s import pathname2url' % module
            except ImportError:
                raise IriError(IriError.UNSUPPORTED_PLATFORM,
                                   osname, os_path_to_uri)
        uri = 'file:' + pathname2url(path)

    return uri


def uri_to_os_path(uri, attemptAbsolute=True, encoding='utf-8', osname=None):
    r"""
    This function converts a URI reference to an OS-specific file system path.

    If the URI reference is given as a Unicode string, then the encoding
    argument determines how percent-encoded components are interpreted, and
    the result will be a Unicode string. If the URI reference is a regular
    byte string, the encoding argument is ignored and the result will be a
    byte string in which percent-encoded octets have been converted to the
    bytes they represent. For example, the trailing path segment of
    u'file:///a/b/%E2%80%A2' will by default be converted to u'\u2022',
    because sequence E2 80 A2 represents character U+2022 in UTF-8. If the
    string were not Unicode, the trailing segment would become the 3-byte
    string '\xe2\x80\xa2'.

    The osname argument determines for what operating system the resulting
    path is appropriate. It defaults to os.name and is typically the value
    'posix' on Unix systems (including Mac OS X and Cygwin), and 'nt' on
    Windows NT/2000/XP.

    This function is similar to urllib.url2pathname(), but is more featureful
    and produces better paths.

    If the given URI reference is not relative, its scheme component must be
    'file', and an exception will be raised if it isn't.

    In accordance with RFC 3986, RFC 1738 and RFC 1630, an authority
    component that is the string 'localhost' will be treated the same as an
    empty authority.

    Dot segments ('.' or '..') in the path component are NOT collapsed.

    If the path component of the URI reference is relative and the
    attemptAbsolute flag is True (the default), then the resulting path
    will be made absolute by considering the path to be relative to the
    current working directory. There is no guarantee that such a result
    will be an accurate interpretation of the URI reference.

    attemptAbsolute has no effect if the
    result is not being produced for the local operating system.

    Fragment and query components of the URI reference are ignored.

    If osname is 'posix', the authority component must be empty or just
    'localhost'. An exception will be raised otherwise, because there is no
    standard way of interpreting other authorities. Also, if '%2F' is in a
    path segment, it will be converted to r'\/' (a backslash-escaped forward
    slash). The caller may need to take additional steps to prevent this from
    being interpreted as if it were a path segment separator.

    If osname is 'nt', a drivespec is recognized as the first occurrence of a
    single letter (A-Z, case-insensitive) followed by '|' or ':', occurring as
    either the first segment of the path component, or (incorrectly) as the
    entire authority component. A UNC hostname is recognized as a non-empty,
    non-'localhost' authority component that has not been recognized as a
    drivespec, or as the second path segment if the first path segment is
    empty. If a UNC hostname is detected, the result will begin with
    '\\<hostname>\'. If a drivespec was detected also, the first path segment
    will be '$<driveletter>$'. If a drivespec was detected but a UNC hostname
    was not, then the result will begin with '<driveletter>:'.

    Windows examples:
    'file:x/y/z' => r'x\y\z';
    'file:/x/y/z' (not recommended) => r'\x\y\z';
    'file:///x/y/z' => r'\x\y\z';
    'file:///c:/x/y/z' => r'C:\x\y\z';
    'file:///c|/x/y/z' => r'C:\x\y\z';
    'file:///c:/x:/y/z' => r'C:\x:\y\z' (bad path, valid interpretation);
    'file://c:/x/y/z' (not recommended) => r'C:\x\y\z';
    'file://host/share/x/y/z' => r'\\host\share\x\y\z';
    'file:////host/share/x/y/z' => r'\\host\share\x\y\z'
    'file://host/x:/y/z' => r'\\host\x:\y\z' (bad path, valid interp.);
    'file://localhost/x/y/z' => r'\x\y\z';
    'file://localhost/c:/x/y/z' => r'C:\x\y\z';
    'file:///C:%5Cx%5Cy%5Cz' (not recommended) => r'C:\x\y\z'
    """
    (scheme, authority, path) = split_uri_ref(uri)[0:3]
    if scheme and scheme != 'file':
        raise IriError(IriError.NON_FILE_URI, uri=uri)
    # enforce 'localhost' URI equivalence mandated by RFCs 1630, 1738, 3986
    if authority == 'localhost':
        authority = None
    osname = osname or os.name

    if osname == 'nt':
        # Get the drive letter and UNC hostname, if any. Fragile!
        unchost = None
        driveletter = None
        if authority:
            authority = percent_decode(authority, encoding=encoding)
            if _get_drive_letter(authority):
                driveletter = authority[0]
            else:
                unchost = authority
        if not (driveletter or unchost):
            # Note that we have to treat %5C (backslash) as a path separator
            # in order to catch cases like file:///C:%5Cx%5Cy%5Cz => C:\x\y\z
            # We will also treat %2F (slash) as a path separator for
            # compatibility.
            if WINDOWS_SLASH_COMPAT:
                regex = '%2[fF]|%5[cC]'
            else:
                regex = '%5[cC]'
            path = re.sub(regex, '/', path)
            segs = path.split('/')
            if not segs[0]:
                # //host/... => [ '', '', 'host', '...' ]
                if len(segs) > 2 and not segs[1]:
                    unchost = percent_decode(segs[2], encoding=encoding)
                    path = len(segs) > 3 and '/' + '/'.join(segs[3:]) or ''
                # /C:/...    => [ '', 'C:', '...' ]
                elif len(segs) > 1:
                    driveletter = _get_drive_letter(percent_decode(segs[1],
                                                   encoding=encoding))
                    if driveletter:
                        path = len(segs) > 2 and '/' + '/'.join(segs[2:]) or ''
            else:
                # C:/...     => [ 'C:', '...' ]
                driveletter = _get_drive_letter(percent_decode(segs[0],
                                                encoding=encoding))
                if driveletter:
                    path = len(segs) > 1 and path[2:] or ''



        # Do the conversion of the path part
        sep = '\\' # we could try to import from ntpath,
                   # but at this point it would just waste cycles.
        path = percent_decode(path.replace('/', sep), encoding=encoding)

        # Assemble and return the path
        if unchost:
            # It's a UNC path of the form \\host\share\path.
            # driveletter is ignored.
            path = r'%s%s%s' % (sep * 2, unchost, path)
        elif driveletter:
            # It's an ordinary Windows path of the form C:\x\y\z
            path = r'%s:%s' % (driveletter.upper(), path)
        # It's an ordinary Windows path of the form \x\y\z or x\y\z.
        # We need to make sure it doesn't end up looking like a UNC
        # path, so we discard extra leading backslashes
        elif path[:1] == '\\':
            path = re.sub(r'^\\+', '\\\\', path)
        # It's a relative path. If the caller wants it absolute, attempt to comply
        elif attemptAbsolute and osname == os.name:
            path = os.path.join(os.getcwd(), path)

        return path

    elif osname == 'posix':
        # a non-empty, non-'localhost' authority component is ambiguous on Unix
        if authority:
            raise IriError(IriError.UNIX_REMOTE_HOST_FILE_URI, uri=uri)
        # %2F in a path segment would indicate a literal '/' in a
        # filename, which is possible on posix, but there is no
        # way to consistently represent it. We'll backslash-escape
        # the literal slash and leave it to the caller to ensure it
        # gets handled the way they want.
        path = percent_decode(re.sub('%2[fF]', '\\/', path), encoding=encoding)
        # If it's relative and the caller wants it absolute, attempt to comply
        if attemptAbsolute and osname == os.name and not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        return path

    else:
        # 4Suite only supports posix and nt, so we're not going to worry about
        # improving upon urllib.pathname2url() for other OSes.
        if osname == os.name:
            from urllib import url2pathname
        else:
            try:
                module = '%surl2path' % osname
                exec 'from %s import url2pathname' % module
            except ImportError:
                raise IriError(IriError.UNSUPPORTED_PLATFORM,
                               platform=osname, function=uri_to_os_path)
        # drop the scheme before passing to url2pathname
        if scheme:
            uri = uri[len(scheme)+1:]
        return url2pathname(uri)

REG_NAME_HOST_PATTERN = re.compile(r"^(?:(?:[0-9A-Za-z\-_\.!~*'();&=+$,]|(?:%[0-9A-Fa-f]{2}))*)$")

def make_urllib_safe(uriRef):
    """
    Makes the given RFC 3986-conformant URI reference safe for passing
    to legacy urllib functions. The result may not be a valid URI.

    As of Python 2.3.3, urllib.urlopen() does not fully support
    internationalized domain names, it does not strip fragment components,
    and on Windows, it expects file URIs to use '|' instead of ':' in the
    path component corresponding to the drivespec. It also relies on
    urllib.unquote(), which mishandles unicode arguments. This function
    produces a URI reference that will work around these issues, although
    the IDN workaround is limited to Python 2.3 only. May raise a
    UnicodeEncodeError if the URI reference is Unicode and erroneously
    contains non-ASCII characters.
    """
    # IDN support requires decoding any percent-encoded octets in the
    # host part (if it's a reg-name) of the authority component, and when
    # doing DNS lookups, applying IDNA encoding to that string first.
    # As of Python 2.3, there is an IDNA codec, and the socket and httplib
    # modules accept Unicode strings and apply IDNA encoding automatically
    # where necessary. However, urllib.urlopen() has not yet been updated
    # to do the same; it raises an exception if you give it a Unicode
    # string, and does no conversion on non-Unicode strings, meaning you
    # have to give it an IDNA string yourself. We will only support it on
    # Python 2.3 and up.
    #
    # see if host is a reg-name, as opposed to IPv4 or IPv6 addr.
    (scheme, auth, path, query, frag) = split_uri_ref(uriRef)
    if auth and auth.find('@') > -1:
        userinfo, hostport = auth.split('@')
    else:
        userinfo = None
        hostport = auth
    if hostport and hostport.find(':') > -1:
        host, port = hostport.split(':')
    else:
        host = hostport
        port = None
    if host and REG_NAME_HOST_PATTERN.match(host):
        # percent-encoded hostnames will always fail DNS lookups
        host = percent_decode(host)
        # IDNA-encode if possible.
        # We shouldn't do this for schemes that don't need DNS lookup,
        # but are there any (that you'd be calling urlopen for)?
        if sys.version_info[0:2] >= (2,3):
            if isinstance(host, str):
                host = host.decode('utf-8')
            host = host.encode('idna')
        # reassemble the authority with the new hostname
        # (percent-decoded, and possibly IDNA-encoded)
        auth = ''
        if userinfo:
            auth += userinfo + '@'
        auth += host
        if port:
            auth += ':' + port

    # On Windows, ensure that '|', not ':', is used in a drivespec.
    if os.name == 'nt' and scheme == 'file':
        path = path.replace(':','|',1)

    # Note that we drop fragment, if any. See RFC 3986 sec. 3.5.
    uri = unsplit_uri_ref((scheme, auth, path, query, None))

    # parts of urllib are not unicode safe
    if isinstance(uri, unicode):
        try:
            # should work if IDNA encoding was applied (Py 2.3+)
            uri = uri.encode('us-ascii')
        except UnicodeError:
            raise IriError(IriError.IDNA_UNSUPPORTED, uri=uriRef)
    return uri


def path_resolve(paths):
    """
    This function takes a list of file URIs.  The first can be
    absolute or relative to the URI equivalent of the current working
    directory. The rest must be relative to the first.
    The function converts them all to OS paths appropriate for the local
    system, and then creates a single final path by resolving each path
    in the list against the following one. This final path is returned
    as a URI.
    """
    if not paths: return paths
    paths = [uri_to_os_path(p, attemptAbsolute=False) for p in paths]
    if not os.path.isabs(paths[0]):
        paths[0] = os.path.join(os.getcwd(), paths[0])
    resolved = reduce(lambda a, b: \
                       basejoin(os.path.isdir(a)
                                 and os_path_to_uri(
                                      os.path.join(a, ''),
                                      attemptAbsolute=False,
                                     ) or os_path_to_uri(a, attemptAbsolute=False),
                                os_path_to_uri(b, attemptAbsolute=False)[5:]),
                       paths)
    return resolved


def basejoin(base, uriRef):
    """
    Merges a base URI reference with another URI reference, returning a
    new URI reference.

    It behaves exactly the same as absolutize(), except the arguments
    are reversed, and it accepts any URI reference (even a relative URI)
    as the base URI. If the base has no scheme component, it is
    evaluated as if it did, and then the scheme component of the result
    is removed from the result, unless the uriRef had a scheme. Thus, if
    neither argument has a scheme component, the result won't have one.

    This function is named basejoin because it is very much like
    urllib.basejoin(), but it follows the current RFC 3986 algorithms
    for path merging, dot segment elimination, and inheritance of query
    and fragment components.

    WARNING: This function exists for 2 reasons: (1) because of a need
    within the 4Suite repository to perform URI reference absolutization
    using base URIs that are stored (inappropriately) as absolute paths
    in the subjects of statements in the RDF model, and (2) because of
    a similar need to interpret relative repo paths in a 4Suite product
    setup.xml file as being relative to a path that can be set outside
    the document. When these needs go away, this function probably will,
    too, so it is not advisable to use it.
    """
    if is_absolute(base):
        return absolutize(uriRef, base)
    else:
        dummyscheme = 'basejoin'
        res = absolutize(uriRef, '%s:%s' % (dummyscheme, base))
        if is_absolute(uriRef):
            # scheme will be inherited from uriRef
            return res
        else:
            # no scheme in, no scheme out
            return res[len(dummyscheme)+1:]


class uridict(dict):
    """
    A dictionary that uses URIs as keys. It attempts to observe some degree of
    URI equivalence as defined in RFC 3986 section 6. For example, if URIs
    A and B are equivalent, a dictionary operation involving key B will return
    the same result as one involving key A, and vice-versa.

    This is useful in situations where retrieval of a new representation of a
    resource is undesirable for equivalent URIs, such as "file:///x" and
    "file://localhost/x" (see RFC 1738), or "http://spam/~x/",
    "http://spam/%7Ex/" and "http://spam/%7ex" (see RFC 3986).

    Normalization performed includes case normalization on the scheme and
    percent-encoded octets, percent-encoding normalization (decoding of
    octets corresponding to unreserved characters), and the reduction of
    'file://localhost/' to 'file:///', in accordance with both RFC 1738 and
    RFC 3986 (although RFC 3986 encourages using 'localhost' and doing
    this for all schemes, not just file).

    An instance of this class is used by Ft.Xml.Xslt.XsltContext for caching
    documents, so that the XSLT function document() will return identical
    nodes, without refetching/reparsing, for equivalent URIs.
    """
    # RFC 3986 requires localhost to be the default host no matter
    # what the scheme, but, being descriptive of existing practices,
    # leaves it up to the implementation to decide whether to use this
    # and other tests of URI equivalence in the determination of
    # same-document references. So our implementation results in what
    # is arguably desirable, but not strictly required, behavior.
    #
    #FIXME: make localhost the default for all schemes, not just file
    def _normalizekey(self, key):
        key = normalize_case(normalize_percent_encoding(key))
        if key[:17] == 'file://localhost/':
            return 'file://' + key[16:]
        else:
            return key

    def __getitem__(self, key):
        return super(uridict, self).__getitem__(self._normalizekey(key))

    def __setitem__(self, key, value):
        return super(uridict, self).__setitem__(self._normalizekey(key), value)

    def __delitem__(self, key):
        return super(uridict, self).__delitem__(self._normalizekey(key))

    def has_key(self, key):
        return super(uridict, self).has_key(self._normalizekey(key))

    def __contains__(self, key):
        return super(uridict, self).__contains__(self._normalizekey(key))

    def __iter__(self):
        return iter(self.keys())

    iterkeys = __iter__
    def iteritems(self):
        for key in self.iterkeys():
            yield key, self.__getitem__(key)


#=======================================================================
#
# Further reading re: percent-encoding
#
# http://lists.w3.org/Archives/Public/ietf-http-wg/2004JulSep/0009.html
#
#=======================================================================
#
# 'file:' URI notes
#
# 'file:' URI resolution is difficult to get right, because the 'file'
# URL scheme is underspecified, and is handled by resolvers in very
# lenient and inconsistent ways.
#
# RFC 3986 provides definitive clarification on how all URIs,
# including the quirky 'file:' ones, are to be interpreted for purposes
# of resolution to absolute form, so that is what we implement to the
# best of our ability.
#
#-----------------------------------------------------------------------
#
# Notes from our previous research on 'file:' URI resolution:
#
# According to RFC 2396 (original), these are valid absolute URIs:
#  file:/autoexec.bat     (scheme ":" abs_path)
#  file:///autoexec.bat   (scheme ":" net_path)
#
# This one is valid but is not what you'd expect it to be:
#
#  file://autoexec.bat    (authority = autoexec.bat, no abs_path)
#
# If you have any more than 3 slashes, it's OK because each path segment
# can be an empty string.
#
# This one is valid too, although everything after 'file:' is
# considered an opaque_part (note that RFC 3986 changes this):
#
#   file:etc/passwd
#
# Unescaped backslashes are NOT allowed in URIs, ever.
# It is not possible to use them as path segment separators.
# Yet... Windows Explorer will accept these:
#   file:C:\WINNT\setuplog.txt
#   file:/C:\WINNT\setuplog.txt
#   file:///C:\WINNT\setuplog.txt
# However, it will also accept "|" in place of the colon after the drive:
#   file:C|/WINNT/setuplog.txt
#   file:/C|/WINNT/setuplog.txt
#   file:///C|/WINNT/setuplog.txt
#
# RFC 1738 says file://localhost/ and file:/// are equivalent;
# localhost in this case is always the local machine, no matter what
# your DNS says.
#
# Basically, any file: URI is valid. Good luck resolving them, though.
#
# Jeremy's idea is to not use open() or urllib.urlopen() on Windows;
# instead, use a C function that wraps Windows' generic open function,
# which resolves any path or URI exactly as Explorer would (he thinks).
#
#-----------------------------------------------------------------------
#
# References for further research on 'file:' URI resolution:
#  http://mail.python.org/pipermail/xml-sig/2001-February/004572.html
#  http://mail.python.org/pipermail/xml-sig/2001-March/004791.html
#  http://mail.python.org/pipermail/xml-sig/2002-August/008236.html
#  http://www.perldoc.com/perl5.8.0/lib/URI/file.html
#  http://lists.w3.org/Archives/Public/uri/2004Jul/0013.html
#
#=======================================================================
