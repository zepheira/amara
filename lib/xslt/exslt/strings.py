########################################################################
# amara/xslt/exslt/common.py
"""
EXSLT 1.1 - Strings (http://www.exslt.org/str/index.html)
"""
import re
import binascii
import operator
import itertools

from amara import tree
from amara.xpath import datatypes

EXSL_STRINGS_NS = "http://exslt.org/strings"

def align_function(context, target, padding, alignment=None):
    """
    The str:align function aligns a string within another string.

    See http://exslt.org/str/functions/align/str.align.html for further
    explanation.
    """
    target = target.evaluate_as_string(context)
    padding = padding.evaluate_as_string(context)
    alignment = alignment and alignment.evaluate_as_string(context)

    # If the target string is longer than the padding string, then it is
    # truncated to be the same length as the padding string and returned.
    if len(target) > len(padding):
        result = target[:len(padding)]
    # If no third argument is given or if it is not one of 'left', 'right'
    # or 'center', then it defaults to left alignment.
    elif alignment == 'right':
        result = padding[:-len(target)] + target
    elif alignment == 'center':
        # With center alignment, the range of characters replaced by the target
        # string is in the middle of the padding string, such that either the
        # number of unreplaced characters on either side of the range is the
        # same or there is one less on the left than there is on the right.
        left = (len(padding) - len(target)) / 2
        right = left + len(target)
        result = padding[:left] + target + padding[right:]
    else:
        result = target + padding[len(target):]
    return datatypes.string(result)


def concat_function(context, nodeset):
    """
    The str:concat function takes a node set and returns the concatenation of
    the string values of the nodes in that node set. If the node set is empty,
    it returns an empty string.
    """
    nodeset = nodeset.evaluate_as_nodeset(context)
    strings = map(datatypes.string, nodeset)
    return datatypes.string(u''.join(strings))


def decode_uri_function(context, uri, encoding=None):
    """
    The str:decode-uri function decodes a percent-encoded string, such as
    one would find in a URI.
    """
    uri = uri.evaluate_as_string(context)
    encoding = encoding.evaluate_as_string(context) if encoding else 'UTF-8'
    try:
        decoder = codecs.getdecoder(encoding)
    except LookupError:
        # Unsupported encoding
        return datatypes.EMPTY_STRING

    def repl(match, decoder=decoder):
        # Note, there may be multiple encoded characters that are required
        # to produce a single Unicode character.
        hexlified = match.group().replace('%', '')
        bytes = binascii.unhexlify(hexlified)
        # Ignore any invalid sequences in this encoding
        string, consumed = decoder(bytes, 'ignore')
        return string

    return datatypes.string(re.sub('(?:%[0-9a-fA-F]{2})+', repl, uri))


_unreserved = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
               'abcdefghijklmnopqrstuvwxyz'
               '0123456789'
               "-_.!~*'()"
               '%') # not really unreserved, but handled specially before these
_reserved = ';/?:@&=+$,[]'

_reserved = re.compile(r"[^" + re.escape(_unreserved + _reserved) + "]")
_unreserved = re.compile(r"[^" + re.escape(_unreserved) + "]")

def encode_uri_function(context, uri, escapeReserved, encoding=None):
    """
    The str:encode-uri function percent-encodes a string for embedding in a URI.
    The second argument is a boolean indicating whether to escape reserved characters;
    if true, the given string can be a URI already, with just some of its characters
    needing to be escaped (not recommended, but users who don't understand the nuances
    of the URI syntax tend to prefer it over assembling a URI piece-by-piece).
    """
    uri = uri.evaluate_as_string(context)
    escape_reserved = escapeReserved.evaluate_as_boolean(context)
    encoding = encoding.evaluate_as_string(context) if encoding else 'UTF-8'

    try:
        encoder = codecs.getencoder(encoding)
    except LookupError:
        return datatypes.EMPTY_STRING

    # The "%" is escaped only if it is not followed by two hexadecimal digits.
    uri = re.sub('%(?![0-9A-Fa-f]{2})', u'%25', uri)

    def repl(match, encoder=encoder):
        ch = match.group()
        ordinal = ord(ch)
        if ordinal > 127:
            try:
                encoded, consumed = encoder(ch, 'strict')
            except UnicodeError:
                # Not valid in this encoding
                result = '%3F'
            else:
                # The Unicode character could map to multiple bytes
                result = u''.join([ '%%%02X' % ord(ch) for ch in encoded ])
        else:
            result = '%%%02X' % ordinal
        return result

    if escape_reserved:
        result = _reserved.sub(repl, uri)
    else:
        result = _unreserved.sub(repl, uri)
    return datatypes.string(result)


def padding_function(context, length, chars=None):
    """
    The str:padding function creates a padding string of a certain length.

    The second argument gives a string to be used to create the padding.
    This string is repeated as many times as is necessary to create a string
    of the length specified by the first argument; if the string is more than
    a character long, it may have to be truncated to produce the required
    length. If no second argument is specified, it defaults to a space (' ').
    """
    length = int(length.evaluate_as_number(context))
    chars = chars.evaluate_as_string(context) if chars else u' '
    return datatypes.string((chars*length)[:length])


def _replace(context, string, replacement=None, *replacements):
    """
    Supports str:replace(). s is a string. replmap is a list of tuples,
    where each tuple is a search string and a replacement node or None.
    This recursive function will cause the original string to have
    occurrences of the search strings replaced with the corresponding
    node or deleted. When a replacement is made, that portion of the
    original string is no longer available for further replacements.
    All replacements are made for each search string before moving on
    to the next. Empty search strings match in between every character
    of the original string.
    """
    if replacement:
        search, replace, key = replacement
        if search:
            segments = string.split(search)
        else:
            segments = list(string)
        last_i = len(segments) - 1
        for i, segment in enumerate(segments):
            if segment:
                _replace(context, segment, *replacements)
            if replace and i < last_i:
                context.copy_node(replace)
    else:
        context.text(string)
    return

def replace_function(context, string, search, replace):
    """
    The str:replace function converts a string to a node-set, with
    each instance of a substring from a given list (obtained from the
    string-values of nodes in the second argument) replaced by the
    node at the corresponding position of the node-set given as the
    third argument. Unreplaced substrings become text nodes.

    The second and third arguments can be any type of object; if
    either is not a node-set, it is treated as if it were a node-set
    of just one text node, formed from the object's string-value.

    Attribute and namespace nodes in the replacement set are
    erroneous but are treated as empty text nodes.

    All occurrences of the longest substrings are replaced first,
    and once a replacement is made, that span of the original string
    is no longer eligible for future replacements.

    An empty search string matches between every character of the
    original string.

    See http://exslt.org/str/functions/replace/str.replace.html for details.
    """
    #FIXME: http://www.exslt.org/str/functions/replace/ doesn't say we have
    #to convert the first arg to a string, but should we, anyway?
    #If not, we should at least check and flag non-strings with a clear error?
    # prepare a list of strings to search for (based on searchNodeSet)
    string = string.evaluate_as_string(context)
    search = search.evaluate(context)
    replace = replace.evaluate(context)
    if isinstance(search, datatypes.nodeset):
        search = map(datatypes.string, search)
    else:
        search = [datatypes.string(search)]
    if isinstance(replace, datatypes.nodeset):
        # use `replace` but replace attr, ns nodes with empty text nodes
        for index, node in enumerate(replace):
            if isinstance(node, (tree.attribute, tree.namespace)):
                replace[index] = tree.text(u'')
    else:
        replace = [tree.text(datatypes.string(replace))]
    # Unpaired search patterns are to be deleted (replacement is None)
    replace = itertools.chain(replace, itertools.repeat(None))
    # Sort the tuples in ascending order by length of string.
    # So that the longest search strings will be replaced first,
    replacements = zip(search, replace, itertools.imap(len, search))
    replacements.sort(key=operator.itemgetter(2), reverse=True)

    # generate a result tree fragment
    context.push_tree_writer(context.instruction.baseUri)
    _replace(context, string, *replacements)
    writer = context.pop_writer()
    rtf = writer.get_result()
    return datatypes.nodeset(rtf.xml_children)


def split_function(context, string, pattern=None):
    """
    The str:split function splits up a string and returns a node set of
    token elements, each containing one token from the string.

    The first argument is the string to be split. The second argument is a
    pattern string (default=' '). The string given by the first argument is
    split at any occurrence of this pattern. An empty string pattern will
    result in a split on every character in the string.
    """
    string = string.evaluate_as_string(context)
    pattern = pattern.evaluate_as_string(context) if pattern else u' '
    context.push_tree_writer(context.instruction.baseUri)
    if pattern:
        tokens = string.split(pattern)
    else:
        tokens = string
    for token in tokens:
        context.start_element(u'token')
        context.text(token)
        context.end_element(u'token')
    writer = context.pop_writer()
    rtf = writer.get_result()
    return datatypes.nodeset(rtf.xml_children)


def tokenize_function(context, string, delimiters=None):
    """
    The str:tokenize function splits up a string and returns a node set of
    'token' elements, each containing one token from the string.

    The first argument is the string to be tokenized. The second argument
    is a string consisting of a number of characters. Each character in
    this string is taken as a delimiting character. The string given by the
    first argument is split at any occurrence of any of these characters.
    """
    string = string.evaluate_as_string(context)
    if delimiters:
        delimiters = delimiters.evaluate_as_string(context)
    else:
        delimiters = '\t\n\r '
    if delimiters:
        tokens = re.split('[%s]' % re.escape(delimiters), string)
    else:
        tokens = string
    context.push_tree_writer(context.instruction.baseUri)
    for token in tokens:
        context.start_element(u'token')
        context.text(token)
        context.end_element(u'token')
    writer = context.pop_writer()
    rtf = writer.get_result()
    return datatypes.nodeset(rtf.xml_children)


## XSLT Extension Module Interface ####################################

extension_namespaces = {
    EXSL_STRINGS_NS : 'str',
    }

extension_functions = {
    (EXSL_STRINGS_NS, 'align'): align_function,
    (EXSL_STRINGS_NS, 'concat'): concat_function,
    (EXSL_STRINGS_NS, 'decode-uri'): decode_uri_function,
    (EXSL_STRINGS_NS, 'encode-uri'): encode_uri_function,
    (EXSL_STRINGS_NS, 'padding'): padding_function,
    (EXSL_STRINGS_NS, 'replace'): replace_function,
    (EXSL_STRINGS_NS, 'split'): split_function,
    (EXSL_STRINGS_NS, 'tokenize'): tokenize_function,
    }

extension_elements = {
    }

