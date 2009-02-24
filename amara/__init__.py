########################################################################
# amara/__init__.py

from amara.namespaces import XML_NAMESPACE, XMLNS_NAMESPACE

__version__ = "2.0a1"

class Error(Exception):

    message = ''
    _message_table = None

    # defer localization of the messages until needed
    def __new__(cls, code, *args, **kwds):
        if cls._message_table is None:
            cls._message_table = cls._load_messages()
            # change `cls.__new__` to default __new__ as loading is complete
            # and will just waste cycles.
            cls.__new__ = Exception.__new__
        return Exception.__new__(cls)

    def __init__(self, code, **kwds):
        assert self._message_table is not None
        message = self._message_table[code]
        if kwds:
            message %= kwds
        Exception.__init__(self, code, message)
        self.code = code
        self.message = message
        # map keywords into attributes
        for name, value in kwds.iteritems():
            setattr(self, name, value)

    def __str__(self):
        return self.message

    @classmethod
    def _load_messages(cls):
        raise NotImplementedError("subclass %s must override" % cls.__name__)


class ReaderError(Error):
    """
    Exception class for errors specific to XML reading
    (at a level above standard, non-namespace-aware parsing)
    """
    # Fatal errors
    # Note: These are actual Expat error codes redefined here to allow for
    #   translation of the error messages.
    #NO_MEMORY = 1                              # mapped to MemoryError
    SYNTAX_ERROR = 2
    NO_ELEMENTS = 3
    INVALID_TOKEN = 4
    UNCLOSED_TOKEN = 5
    PARTIAL_CHAR = 6
    TAG_MISMATCH = 7
    DUPLICATE_ATTRIBUTE = 8
    JUNK_AFTER_DOCUMENT_ELEMENT = 9
    ILLEGAL_PARAM_ENTITY_REF = 10
    UNDEFINED_ENTITY = 11
    RECURSIVE_ENTITY_REF = 12
    ASYNC_ENTITY = 13
    BAD_CHAR_REF = 14
    BINARY_ENTITY_REF = 15
    ATTRIBUTE_EXTERNAL_ENTITY_REF = 16
    MISPLACED_XML_PI = 17
    UNKNOWN_ENCODING = 18
    INCORRECT_ENCODING = 19
    UNCLOSED_CDATA_SECTION = 20
    EXTERNAL_ENTITY_HANDLING = 21
    NOT_STANDALONE = 22
    #UNEXPECTED_STATE = 23                      # mapped to SystemError
    ENTITY_DECLARED_IN_PE = 24
    #FEATURE_REQUIRES_XML_DTD = 25              # mapped to SystemError
    #CANT_CHANGE_FEATURE_ONCE_PARSING = 26      # mapped to SystemError
    UNBOUND_PREFIX = 27
    UNDECLARED_PREFIX = 28
    INCOMPLETE_PE = 29
    INVALID_XML_DECL = 30
    INVALID_TEXT_DECL = 31
    INVALID_PUBLICID = 32
    #SUSPENDED = 33                             # mapped to SystemError
    #NOT_SUSPENDED = 34                         # mapped to RuntimeError
    #ABORTED = 35                               # mapped to SystemError
    #FINISHED = 36                              # mapped to SystemError
    #SUSPEND_PE = 37                            # mapped to SystemError
    RESERVED_PREFIX_XML = 38
    RESERVED_PREFIX_XMLNS = 39
    RESERVED_NAMESPACE_URI = 40

    # Validity errors
    MISSING_DOCTYPE = 1000
    INVALID_ELEMENT = 1001
    ROOT_ELEMENT_MISMATCH = 1002
    UNDECLARED_ELEMENT = 1003
    INCOMPLETE_ELEMENT = 1004
    INVALID_TEXT = 1005
    UNDECLARED_ATTRIBUTE = 1006
    DUPLICATE_ID = 1007
    UNDECLARED_ENTITY = 1008
    INVALID_ENTITY = 1009
    UNDECLARED_NOTATION = 1010
    MISSING_ATTRIBUTE = 1011
    UNDEFINED_ID = 1012                         # FIXME: implement
    DUPLICATE_ELEMENT_DECL = 1013
    DUPLICATE_ID_DECL = 1014
    ID_ATTRIBUTE_DEFAULT = 1015
    XML_SPACE_DECL = 1016
    XML_SPACE_VALUES = 1017
    INVALID_NAME_VALUE = 1018
    INVALID_NAME_SEQ_VALUE = 1019
    INVALID_NMTOKEN_VALUE = 1020
    INVALID_NMTOKEN_SEQ_VALUE = 1021
    INVALID_ENUM_VALUE = 1022
    ATTRIBUTE_UNDECLARED_NOTATION = 1023
    ENTITY_UNDECLARED_NOTATION = 1024           # FIXME: implement

    # Warnings
    ATTRIBUTES_WITHOUT_ELEMENT = 2000
    ATTRIBUTE_DECLARED = 2001
    ENTITY_DECLARED = 2002

    def __init__(self, code, systemId, lineNumber, columnNumber, **kwords):
        Error.__init__(self, code, **kwords)
        self.systemId = systemId
        self.lineNumber = lineNumber
        self.columnNumber = columnNumber
        return

    def __str__(self):
        from gettext import gettext as _
        systemId = self.systemId
        if isinstance(systemId, unicode):
            systemId = systemId.encode('unicode_escape')
        return _("In %s, line %s, column %s: %s") % (systemId,
                                                     self.lineNumber,
                                                     self.columnNumber,
                                                     self.message)

    @classmethod
    def _load_messages(cls):
        from gettext import gettext as _
        return {
            # Fatal errors
            ReaderError.SYNTAX_ERROR: _(
                "syntax error"),
            ReaderError.NO_ELEMENTS: _(
                "no element found"),
            ReaderError.INVALID_TOKEN: _(
                "not well-formed (invalid token)"),
            ReaderError.UNCLOSED_TOKEN: _(
                "unclosed token"),
            ReaderError.PARTIAL_CHAR: _(
                "partial character"),
            ReaderError.TAG_MISMATCH: _(
                "mismatched tag"),
            ReaderError.DUPLICATE_ATTRIBUTE: _(
                "duplicate attribute"),
            ReaderError.JUNK_AFTER_DOCUMENT_ELEMENT: _(
                "junk after document element"),
            ReaderError.ILLEGAL_PARAM_ENTITY_REF: _(
                "illegal parameter entity reference"),
            ReaderError.UNDEFINED_ENTITY: _(
                "undefined entity"),
            ReaderError.RECURSIVE_ENTITY_REF: _(
                "recursive entity reference"),
            ReaderError.ASYNC_ENTITY: _(
                "asynchronous entity"),
            ReaderError.BAD_CHAR_REF: _(
                "reference to invalid character number"),
            ReaderError.BINARY_ENTITY_REF: _(
                "reference to binary entity"),
            ReaderError.ATTRIBUTE_EXTERNAL_ENTITY_REF: _(
                "reference to external entity in attribute"),
            ReaderError.MISPLACED_XML_PI: _(
                "XML or text declaration not at start of entity"),
            ReaderError.UNKNOWN_ENCODING: _(
                "unknown encoding"),
            ReaderError.INCORRECT_ENCODING: _(
                "encoding specified in XML declaration is incorrect"),
            ReaderError.UNCLOSED_CDATA_SECTION: _(
                "unclosed CDATA section"),
            ReaderError.EXTERNAL_ENTITY_HANDLING: _(
                "error in processing external entity reference"),
            ReaderError.NOT_STANDALONE: _(
                "document is not standalone"),
            ReaderError.ENTITY_DECLARED_IN_PE: _(
                "entity declared in parameter entity"),
            ReaderError.UNBOUND_PREFIX: _(
                "unbound prefix"),
            ReaderError.UNDECLARED_PREFIX: _(
                "must not undeclare prefix"),
            ReaderError.INCOMPLETE_PE: _(
                "incomplete markup in parameter entity"),
            ReaderError.INVALID_XML_DECL: _(
                "XML declaration not well-formed"),
            ReaderError.INVALID_TEXT_DECL: _(
                "text declaration not well-formed"),
            ReaderError.INVALID_PUBLICID: _(
                "illegal character(s) in public id"),
            ReaderError.RESERVED_PREFIX_XML: _(
                "reserved prefix (xml) must not be undeclared or bound to "
                "another namespace name"),
            ReaderError.RESERVED_PREFIX_XMLNS: _(
                "reserved prefix (xmlns) must not be declared or undeclared"),
            ReaderError.RESERVED_NAMESPACE_URI: _(
                "prefix must not be bound to one of the reserved namespace "
                "names"),

            # Validity Errors

            ReaderError.MISSING_DOCTYPE: _(
                "Missing document type declaration"),
            ReaderError.INVALID_ELEMENT: _(
                "Element '%(element)s' not allowed here"),
            ReaderError.ROOT_ELEMENT_MISMATCH: _(
                "Document root element '%(element)s' does not match declared "
                "root element"),
            ReaderError.UNDECLARED_ELEMENT: _(
                "Element '%(element)s' not declared"),
            ReaderError.INCOMPLETE_ELEMENT: _(
                "Element '%(element)s' ended before all required elements "
                "found"),
            ReaderError.INVALID_TEXT: _(
                "Character data not allowed in the content of element "
                "'%(element)s'"),
            ReaderError.UNDECLARED_ATTRIBUTE: _(
                "Attribute '%(attr)s' not declared"),
            ReaderError.DUPLICATE_ID: _(
                "ID '%(id)s' appears more than once"),
            ReaderError.UNDECLARED_ENTITY: _(
                "Entity '%(entity)s' not declared"),
            ReaderError.INVALID_ENTITY: _(
                "Entity '%(entity)s' is not an unparsed entity"),
            ReaderError.UNDECLARED_NOTATION: _(
                "Notation '%(notation)s' not declared"),
            ReaderError.MISSING_ATTRIBUTE: _(
                "Missing required attribute '%(attr)s'"),
            ReaderError.UNDEFINED_ID: _(
                "IDREF referred to non-existent ID '%(id)s'"),
            ReaderError.DUPLICATE_ELEMENT_DECL: _(
                "Element '%(element)s' declared more than once"),
            ReaderError.DUPLICATE_ID_DECL: _(
                "Only one ID attribute allowed on each element type"),
            ReaderError.ID_ATTRIBUTE_DEFAULT: _(
                "ID attributes cannot have a default value"),
            ReaderError.XML_SPACE_DECL: _(
                "xml:space must be declared an enumeration type"),
            ReaderError.XML_SPACE_VALUES: _(
                "xml:space must have exactly one or both of the values "
                "'default' and 'preserve'"),
            ReaderError.INVALID_NAME_VALUE: _(
                "Value of '%(attr)s' attribute is not a valid name"),
            ReaderError.INVALID_NAME_SEQ_VALUE: _(
                "Value of '%(attr)s' attribute is not a valid name sequence"),
            ReaderError.INVALID_NMTOKEN_VALUE: _(
                "Value of '%(attr)s' attribute is not a valid name token"),
            ReaderError.INVALID_NMTOKEN_SEQ_VALUE: _(
                "Value of '%(attr)s' attribute is not a valid name token "
                "sequence"),
            ReaderError.INVALID_ENUM_VALUE: _(
                "'%(value)s in not an allowed value for the '%(attr)s' "
                "attribute"),
            ReaderError.ATTRIBUTE_UNDECLARED_NOTATION: _(
                "Notation attribute '%(attr)s' uses undeclared notation "
                "'%(notation)s'"),
            ReaderError.ENTITY_UNDECLARED_NOTATION: _(""),

            # Warnings

            ReaderError.ATTRIBUTES_WITHOUT_ELEMENT: _(
                "Attribute list for undeclared element '%(element)s'"),
            ReaderError.ATTRIBUTE_DECLARED: _(
                "Attribute '%(attr)s' already declared"),
            ReaderError.ENTITY_DECLARED: _(
                "Entity '%(entity)s' already declared"),

            }


class XIncludeError(ReaderError):
    pass

from amara.tree import parse
from amara.lib import xmlstring as string
from amara.writers._treevisitor import xml_print

import sys

def writer(stream=sys.stdout, **kwargs):
    from amara.writers.outputparameters import outputparameters
    oparams = outputparameters(**kwargs)
    if kwargs.get("method", "xml") == "xml":
        from amara.writers.xmlwriter import _xmluserwriter
        writer_class = _xmluserwriter
    else:
        from amara.writers.htmlwriter import _htmluserwriter
        writer_class = _htmluserwriter
    return writer_class(oparams, stream)


def launch(source, **kwargs):
    doc = parse(source)
    from amara import xml_print
    xml_print(doc, indent=kwargs.get('pretty'))
    return


#Ideas borrowed from
# http://www.artima.com/forums/flat.jsp?forum=106&thread=4829

#FIXME: A lot of this is copied boilerplate that neds to be cleaned up

def command_line_prep():
    from optparse import OptionParser
    usage = "Amara 2.x.  Command line support for basic parsing.\n"
    usage += "python -m 'amara' [options] source cmd"
    parser = OptionParser(usage=usage)
    parser.add_option("-p", "--pretty",
                      action="store_true", dest="pretty", default=False,
                      help="Pretty-print the XML output")
    return parser


def main(argv=None):
    #But with better integration of entry points
    if argv is None:
        argv = sys.argv
    # By default, optparse usage errors are terminated by SystemExit
    try:
        optparser = command_line_prep()
        options, args = optparser.parse_args(argv[1:])
        # Process mandatory arguments with IndexError try...except blocks
        try:
            source = args[0]
        except IndexError:
            optparser.error("Missing source for XML")
        #try:
        #    xpattern = args[1]
        #except IndexError:
        #    optparser.error("Missing main xpattern")
    except SystemExit, status:
        return status

    # Perform additional setup work here before dispatching to run()
    # Detectable errors encountered here should be handled and a status
    # code of 1 should be returned. Note, this would be the default code
    # for a SystemExit exception with a string message.

    #try:
    #    xpath = args[2].decode('utf-8')
    #except IndexError:
    #    xpath = None
    #xpattern = xpattern.decode('utf-8')
    #sentinel = options.sentinel and options.sentinel.decode('utf-8')
    pretty = options.pretty
    if source == '-':
        source = sys.stdin
    #if options.test:
    #    test()
    #else:
    launch(source, pretty=pretty)
    return


if __name__ == "__main__":
    sys.exit(main(sys.argv))

