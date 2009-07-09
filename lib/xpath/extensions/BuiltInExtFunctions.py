########################################################################
# amara/xpath/extensions/xxx.py
"""
4XPath-specific extension functions

Extension functions are implemented by a module, such as this one,
that defines an ExtFunctions global dictionary that maps (namespace,
local-name) string tuples to a corresponding Python function. The
function must take a Context object as the first argument, and any
additional arguments accepted will correspond to the arguments passed
in. See other API docs to see how to make use of modules that contain
ExtFunctions.
"""

import os, re, codecs, time
from xml.dom import Node

import Ft
from Ft.Lib import boolean, number, Uri, Wrap as LineWrap
from Ft.Lib.Random import DEFAULT_RNG
from Ft.Xml import Lib
from Ft.Xml.XPath import Conversions
from Ft.Xml.XPath import XPathTypes as Types
from Ft.Xml.XPath import FT_EXT_NAMESPACE


def BaseUri(context, arg=None):
    """
    Returns the base URI of the first node in the given node-set, or
    of the context node if no argument is given. If the given node-set
    is empty, an empty string is returned.
    """
    if arg is None:
        node = context.node
    elif isinstance(arg, Types.NodesetType):
        if not arg:
            return u''
        node = arg[0]
    else:
        raise TypeError("%r must be a node-set, not a %s" % (
            arg, Types.g_xpathPrimitiveTypes.get(type(arg), type(arg).__name__)))
    return node.xml_base or u''
BaseUri.arguments = (Types.NodesetType,)
BaseUri.result = Types.StringType


def Decode(context, object, encoding):
    """
    f:decode mirrors the Python decode function/method. It takes a
    foreign object that is a Python byte string, and an encoding,
    and returns another foreign object which is a Unicode object.
    """
    encode, decode, reader, writer = codecs.lookup(encoding)
    return decode(object)[0]
Decode.arguments = (Types.ObjectType, Types.StringType)
Decode.result = Types.ObjectType


def Encode(context, object, encoding):
    """
    f:encode mirrors the Python encode function/method. It takes a
    foreign object that is a Unicode object, and an encoding,
    and returns another foreign object which is a Python byte string.
    """
    encode, decode, reader, writer = codecs.lookup(encoding)
    return encode(object)[0]
Encode.arguments = (Types.ObjectType, Types.StringType)
Encode.result = Types.ObjectType


def EndsWith(context, outer, inner):
    """
    Returns true if the string given in the first argument ends with
    the substring given in the second argument.
    """
    outer = Conversions.StringValue(outer)
    inner = Conversions.StringValue(inner)
    return outer.endswith(inner) and boolean.true or boolean.false
EndsWith.arguments = (Types.StringType, Types.StringType)
EndsWith.result = Types.BooleanType


def EscapeXml(context, text):
    """
    Returns the given string with XML markup characters "&", "<" and
    ">" escaped as "&amp;", "&lt;" and "&gt;", respectively.
    """
    from xml.sax.saxutils import escape
    return escape(Conversions.StringValue(text))
EscapeXml.arguments = (Types.StringType,)
EscapeXml.result = Types.StringType


def GenerateUuid(context):
    """
    Returns a random UUID string.
    """
    from Ft.Lib import Uuid
    rt = Uuid.UuidAsString(Uuid.GenerateUuid())
    rt = unicode(rt, 'us-ascii', errors='replace')
    return rt
GenerateUuid.arguments = ()
GenerateUuid.result = Types.StringType


def If(context, cond, v1, v2=None):
    """
    If the first argument, when converted to a boolean, is true,
    returns the second argument. Otherwise, returns the third
    argument, or if the third argument is not given, returns an
    empty node-set.
    """
    # contributed by Lars Marius Garshol;
    # originally using namespace URI 'http://garshol.priv.no/symbolic/'
    if Conversions.BooleanValue(cond):
        return v1
    elif v2 is None:
        return []
    else:
        return v2
If.arguments = (Types.BooleanType, Types.ObjectType, Types.ObjectType)
If.result = Types.ObjectType


# why does this exist?
def ImportString(context, object):
    """
    f:import-string takes a Unicode FO and returns an XPath string.  It is
    an error if the FO contains illegal XML chars.  (although eventually
    this function might be extended to recover from this error)
    """
    #FIXME: Add validation of object as valid XPath string,
    #and possibly mapping ops to PUA for illegal characters.
    #We probably need an Export string if we add PUA shifting
    return object
ImportString.arguments = (Types.ObjectType,)
ImportString.result = Types.StringType


def Indent(context, text, levels, indentstring=None):
    """
    f:indent() returns a string with each line of the text indented the
    given number of levels. For each level, the indent string, normally
    2 spaces by default, is prepended to each line.
    """
    text = Conversions.StringValue(text)
    levels = int(Conversions.NumberValue(levels))
    if indentstring is None:
        indentstring = u'  '
    else:
        indentstring = Conversions.StringValue(indentstring)
    if indentstring and levels > 0:
        indent = indentstring * levels
        return indent + ('\n' + indent).join(text.split('\n'))
    else:
        return text
Indent.arguments = (Types.StringType, Types.NumberType, Types.StringType)
Indent.result = Types.StringType


def NormalizeEol(context, text):
    """
    Normalizes end-of-line characters in input string, returning the
    normalized string. Normalization involves replacing "\n\r", "\r\n"
    or "\r" with "\n"
    """
    text = text.replace("\n\r", "\n")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    return text
NormalizeEol.arguments = (Types.StringType,)
NormalizeEol.result = Types.StringType


def OsPath2Uri(context, path):
    """
    Returns the given OS path as a URI.
    The result varies depending on the underlying operating system.
    """
    return Uri.OsPathToUri(Conversions.StringValue(path))
OsPath2Uri.arguments = (Types.StringType,)
OsPath2Uri.result = Types.StringType


def ParseXml(context, src, parameters=None):
    """
    f:parse-xml() parses the string-value of the given object as XML
    and returns a node-set whose sole item is the resulting parsed
    document's root node. The XML must be a well-formed document.

    src - the string or object to be parsed as XML.

    parameters - the name of a parameter set for the operation.

    The parameters argument is ignored for now. In the future, it
    will provide a way to specify a base URI for the resolution of
    relative URIs in entity declarations and XIncludes.

    Also for now, if the XML contains an encoding declaration, the
    declaration must specify UTF-8.

    An example:

    <?xml version="1.0" encoding="utf-8"?>
    <xsl:stylesheet
      xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
      xmlns:f="http://xmlns.4suite.org/ext"
      version="1.0"
    >
      <xsl:output method="text"/>
      <xsl:variable name="doc"
        select="'&lt;spam>eggs&lt;monty>python&lt;/monty>&lt;/spam>'"/>

      <xsl:template match="/">
        <xsl:value-of select="f:parse-xml($doc)/spam/monty"/>
      </xsl:template>
    </xsl:stylesheet>

    ...run against any XML source should yield:

    python

    See also: XSLT (not XPath) extension function f:serialize-xml()
    """
    from Ft.Xml import Domlette
    src = Conversions.StringValue(src).encode("utf-8")

    # prepare a base URI for the XML
    instruction = getattr(context, 'currentInstruction', None)
    if instruction:
        uri = instruction.baseUri
    else:
        uri = context.node.baseUri
    if not uri:
        uri = OsPathToUri('__parse-xml-extension-function__',
                          attemptAbsolute=1)
    # append "XML-string-(something_unique)" as a fragment
    uri += '%sXML-string-%s' % ((uri.find('#') + 1 and ';' or '#'),
                                 str(time.time()))

    doc = Domlette.NonvalidatingReader.parseString(src, uri)
    return [doc]
ParseXml.arguments = (Types.StringType, Types.ObjectType)
ParseXml.result = Types.NodesetType


def Range(context, lo, hi):
    """
    Returns a node-set consisting of text nodes encapsulating integers
    in the numeric range bounded by the given low and high values.
    """
    # contributed by Lars Marius Garshol;
    # originally using namespace URI 'http://garshol.priv.no/symbolic/'
    doc = context.node.rootNode

    # sanity check
    for n in (lo, hi):
        if number.isinf(n) or number.isnan(n):
            raise ValueError("Arguments to ft:range must be neither infinite nor NaN.")

    #xrange wants int, not float
    lo = int(round(Conversions.NumberValue(lo)))
    hi = int(round(Conversions.NumberValue(hi)))

    nodeset = []
    for num in xrange(lo, hi):
        nodeset.append(doc.createTextNode(str(num)))

    return nodeset
Range.arguments = (Types.NumberType, Types.NumberType)
Range.result = Types.NodesetType


def ResolvePath(context, base, rel):
    """
    Resolves a Posix-style path, such as the path portion of a URL,
    against a base. Similar to f:resolve-url, but allows the base to be
    just a path, not necessarily a full URL.
    """
    base = Conversions.StringValue(base)
    rel = Conversions.StringValue(rel)
    return Uri.BaseJoin(base, rel)
ResolvePath.arguments = (Types.StringType, Types.StringType)
ResolvePath.result = Types.StringType


def ResolveUrl(context, base, rel):
    """
    Returns the relative URL ref given in the second argument
    resolved against the base given in the first argument.
    In case of URI processing error an empty string is returned
    """
    base = Conversions.StringValue(base)
    rel = Conversions.StringValue(rel)
    try:
        return Uri.Absolutize(rel, base)
    except Uri.UriException:
        return u''
ResolveUrl.arguments = (Types.StringType, Types.StringType)
ResolveUrl.result = Types.StringType


def ShaHash(context, text):
    """
    Returns a SHA message digest of the given string, as a string of
    several groups of hex digits separated by '-'. See
    http://www.itl.nist.gov/fipspubs/fip180-1.htm for info on SHA.
    """
    text = Conversions.StringValue(text)
    import sha
    rv = sha.sha(text).hexdigest()
    rv = unicode(rv, 'us-ascii', errors='replace')
    return rv
ShaHash.arguments = (Types.StringType,)
ShaHash.result = Types.StringType


def SharePath(context):
    """
    Returns the system-dependent path to modifiable data
    """
    return unicode(Ft.GetConfigVar('LOCALSTATEDIR'), 'us-ascii',
                   errors='replace')
SharePath.arguments = ()
SharePath.result = Types.StringType

def BinPath(context):
    """
    Returns the system-dependent path of Fourthought binaries
    """
    return unicode(Ft.GetConfigVar('BINDIR'), 'us-ascii', errors='replace')
BinPath.arguments = ()
BinPath.result = Types.StringType


def Uri2OsPath(context, uri):
    """
    Returns the given URI as an OS path.
    The result varies depending on the underlying operating system.
    """
    return Uri.UriToOsPath(Conversions.StringValue(uri))
Uri2OsPath.arguments = (Types.StringType,)
Uri2OsPath.result = Types.StringType


def Version(context):
    """
    Returns the 4Suite version number as a string.
    """
    return unicode(Ft.VERSION, 'us-ascii', errors='replace')
Version.arguments = ()
Version.result = Types.StringType


def Wrap(context, text, width):
    """
    f:wrap() returns a string with the text reflowed so that each line
    fits within the given width. Existing linefeeds are preserved, but
    spaces are considered inter-word separators that can be collapsed.
    To reflow without preserving existing linefeeds, strip them first,
    e.g. with translate(text, '&#10;', '').
    http://lists.fourthought.com/pipermail/4suite-dev/2002-December/000878.html
    """
    s = Conversions.StringValue(text)
    width = Conversions.NumberValue(width)
    return LineWrap(s, width)
Wrap.arguments = (Types.StringType, Types.NumberType)
Wrap.result = Types.StringType


def PytimeToExslt(context, t=None):
    """
    Takes a Python time value as a number and returns a date/time as if
    from EXSLT date-time()
    t - a time stamp number, as from Python's time.time()
        if omitted, use the current time
    """
    from Ft.Lib import Time as FtTime
    if t is not None:
        t = Conversions.NumberValue(t)
        return unicode(str(FtTime.FromPythonTime(t)), errors='replace')
    else:
        return unicode(str(FtTime.FromPythonTime()), errors='replace')
PytimeToExslt.arguments = (Types.NumberType,)
PytimeToExslt.result = Types.StringType


#---EXSLT-like functions------------------------------------------------
#   (perhaps soon to be deprecated)

def Join(context, nodeset, delim=' '):
    """
    Concatenates the string-values of the nodes in the given node-set,
    inserting the delimiter given in the optional second argument in
    between each string-value. The delimiter defaults to a space.
    See also: EXSLT's str:concat()
    """
    delim = Conversions.StringValue(delim)
    comps = map(Conversions.StringValue, nodeset)
    if delim:
        return delim.join(comps)
    else:
        return u''.join(comps)
Join.arguments = (Types.NodesetType, Types.StringType)
Join.result = Types.StringType


def Match(context, pattern, arg=None):
    """
    Returns true if the string given in the optional second argument
    (or the string-value of the context node if no second argument is
    given) matches the regular expression given in the first argument.
    See also: EXSLT's regexp:test()
    This function does differ from XSLT 2.0 match() function
    """
    if not arg:
        arg = context.node
    arg = Conversions.StringValue(arg)
    return re.match(pattern, arg) and boolean.true or boolean.false
Match.arguments = (Types.StringType, Types.StringType)
Match.result = Types.StringType


def ParseDate(context, date, format=None):
    """
    This function is similar to EXSLT's date:parse-date()
    except that it uses Python rather than Java conventions
    for the date formatting.
    """
    import time
    date = Conversions.StringValue(date)
    format = Conversions.StringValue(format)
    time_tuple = time.strptime(format)
    #perhaps add some variants for missing time tuple values?
    str_time = time.strftime("%Y-%m-%dT%H:%M:%S", time_tuple)
    return unicode(str_time, 'us-ascii', errors='replace')
ParseDate.arguments = (Types.StringType, Types.StringType)
ParseDate.result = Types.StringType


def Random(context, max=None, forceInt=0):
    """
    Returns a random number between 0 (inclusive) and max (exclusive).
    max defaults to 1. The first optional argument is a different
    value for max, and the second argument is a flag that, if set,
    causes the random number to be rounded to an integer.
    See also: EXSLT's math:random()
    """
    if max:
        max = Conversions.NumberValue(max)
    else:
        max = 1.0
    rt = DEFAULT_RNG.randrange(0, max)
    if forceInt:
        rt = round(rt)
    return rt
Random.arguments = (Types.NumberType, Types.BooleanType)
Random.result = Types.NumberType


def Replace(context, old, new, arg=None):
    """
    Returns the third argument string, which defaults to the
    string-value of the context node, with occurrences of the substring
    given in the first argument replaced by the string given in the
    second argument.
    See also: EXSLT's str:replace()
    """
    if not arg:
        arg = context.node
    arg = Conversions.StringValue(arg)
    old = Conversions.StringValue(old)
    new = Conversions.StringValue(new)
    return arg.replace(old, new)
Replace.arguments = (Types.StringType, Types.StringType, Types.StringType)
Replace.result = Types.StringType


def StrFTime(context, format, date=None):
    """
    Returns the given ISO 8601 UTC date-time formatted according to
    the given format string as would be used by Python's
    time.strftime(). If no date-time string is given, the current
    time is used.
    """
    format = Conversions.StringValue(format)
    if date is not None:
        date = Conversions.StringValue(date)
        time_str = time.strftime(format, time.strptime(date, '%Y-%m-%dT%H:%M:%SZ'))
    else:
        time_str = time.strftime(format)
    return unicode(time_str, 'us-ascii', errors='replace')
StrFTime.arguments = (Types.StringType, Types.StringType)
StrFTime.result = Types.StringType


#---OS System-aware functions------------------------------------------------
#   (Not loaded by default for security reasons)

def EnvVar(context, var):
    """
    Looks up a variable in the OS environment. Returns a string, either
    the environment variable value or an empty string if there is no
    such variable. The system default encoding is assumed.

    CAUTION: Using this function could be a security hazard.

    You can also use system-property() for the same purpose
    f:env-var('foo')
    is equivalent to
    system-property('fs:foo')
    given a mapping from fs to http://xmlns.4suite.org/xslt/env-system-property
    """
    var = Conversions.StringValue(var)
    result = os.environ.get(var, '')
    result = unicode(result, errors='replace')
    return result
EnvVar.arguments = (Types.StringType,)
EnvVar.result = Types.StringType


def Spawnv(context, command, *args):
    """
    Executes a command in the operating system's shell, passing in the
    command line arguments separately. Returns the result of the command
    (a numeric exit code, typically).

    CAUTION: Using this function could be a security hazard.

    See also: f:system()
    """
    command = Conversions.StringValue(command)
    result = os.spawnv(os.P_WAIT, command, args)
    return result
Spawnv.arguments = (Types.StringType,)
Spawnv.result = Types.NumberType


def System(context, command):
    """
    Executes a command in the operating system's shell and returns the
    command's result (a numeric exit code, typically).

    CAUTION: Using this function could be a security hazard.

    See also: f:spawnv()
    """
    command = Conversions.StringValue(command)
    result = os.system(command)
    return result
System.arguments = (Types.StringType,)
System.result = Types.NumberType


ExtNamespaces = {
    FT_EXT_NAMESPACE : 'f',
    }

ExtFunctions = {
    (FT_EXT_NAMESPACE, 'base-uri'): BaseUri,
    (FT_EXT_NAMESPACE, 'decode') : Decode,
    (FT_EXT_NAMESPACE, 'encode') : Encode,
    (FT_EXT_NAMESPACE, 'ends-with'): EndsWith,
    (FT_EXT_NAMESPACE, 'escape-xml'): EscapeXml,
    (FT_EXT_NAMESPACE, 'generate-uuid'): GenerateUuid,
    (FT_EXT_NAMESPACE, 'if'): If,
    (FT_EXT_NAMESPACE, 'import-string') : ImportString,
    (FT_EXT_NAMESPACE, 'indent') : Indent,
    (FT_EXT_NAMESPACE, 'join'): Join,
    (FT_EXT_NAMESPACE, 'match'): Match,
    (FT_EXT_NAMESPACE, 'normalize-eol') : NormalizeEol,
    (FT_EXT_NAMESPACE, 'ospath2uri'): OsPath2Uri,
    (FT_EXT_NAMESPACE, 'parse-date'): ParseDate,
    (FT_EXT_NAMESPACE, 'pytime-to-exslt'): PytimeToExslt,
    (FT_EXT_NAMESPACE, 'parse-xml') : ParseXml,
    (FT_EXT_NAMESPACE, 'random'): Random,
    (FT_EXT_NAMESPACE, 'range'): Range,
    (FT_EXT_NAMESPACE, 'replace'): Replace,
    (FT_EXT_NAMESPACE, 'resolve-url'): ResolveUrl,
    (FT_EXT_NAMESPACE, 'resolve-path'): ResolvePath,
    (FT_EXT_NAMESPACE, 'sha-hash') : ShaHash,
    (FT_EXT_NAMESPACE, 'share-path'): SharePath,
    (FT_EXT_NAMESPACE, 'bin-path'): BinPath,
    (FT_EXT_NAMESPACE, 'uri2ospath'): Uri2OsPath,
    (FT_EXT_NAMESPACE, 'version'): Version,
    (FT_EXT_NAMESPACE, 'wrap') : Wrap,
    (FT_EXT_NAMESPACE, 'strftime') : StrFTime,
    }


InsecureExtFunctions = {
    (FT_EXT_NAMESPACE, 'spawnv'): Spawnv,
    (FT_EXT_NAMESPACE, 'system'): System,
    (FT_EXT_NAMESPACE, 'env-var'): EnvVar,
}

import MathFunctions
ExtFunctions.update(MathFunctions.ExtFunctions)

# Deprecated functions removed for 4Suite 1.0a4:
#
#    (FT_EXT_NAMESPACE, 'escape-url'): EscapeUrl,
#    (FT_EXT_NAMESPACE, 'evaluate'): Evaluate,
#    (FT_EXT_NAMESPACE, 'iso-time'): IsoTime,
#    (FT_EXT_NAMESPACE, 'distinct'): Distinct,
#    (FT_EXT_NAMESPACE, 'find'): Find,
#    (FT_EXT_NAMESPACE, 'node-set'): NodeSet,
