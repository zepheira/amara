########################################################################
# amara/xslt/__init__.py
"""
Please see: http://wiki.xml3k.org/Amara2/Whatsnew#head-6121c5b40e473f1e3d720a66212f3025856bdc90
"""

import sys, getopt
from amara import Error

__all__ = ['XsltError', 'transform']

class XsltError(Error):

    INTERNAL_ERROR = 1
    # xsl:stylesheet
    NO_STYLESHEET = 20
    #STYLESHEET_MISSING_VERSION = 21
    LITERAL_RESULT_MISSING_VERSION = 22
    STYLESHEET_PARSE_ERROR = 23
    SOURCE_PARSE_ERROR = 24
    #XSL_STYLESHEET_NOT_DOCELEM = 25
    #TOP_LEVEL_ELEM_WITH_NULL_NS = 26
    XSLT_ILLEGAL_ELEMENT = 27
    #STYLESHEET_ILLEGAL_ROOT = 28
    CIRCULAR_VARIABLE = 29
    DUPLICATE_TOP_LEVEL_VAR = 30
    DUPLICATE_NAMESPACE_ALIAS = 31

    # misc element validation
    MISSING_REQUIRED_ELEMENT = 50
    ILLEGAL_ELEMENT_CHILD = 51
    ILLEGAL_TEXT_CHILD = 52
    UNDEFINED_PREFIX = 53

    # misc attribute validation
    MISSING_REQUIRED_ATTRIBUTE = 70
    ILLEGAL_NULL_NAMESPACE_ATTR = 71
    ILLEGAL_XSL_NAMESPACE_ATTR = 72
    INVALID_ATTR_CHOICE = 73
    INVALID_CHAR_ATTR = 74
    INVALID_NUMBER_ATTR = 75
    INVALID_NS_URIREF_ATTR = 76
    INVALID_ID_ATTR = 77
    INVALID_QNAME_ATTR = 78
    INVALID_NCNAME_ATTR = 79
    INVALID_PREFIX_ATTR = 80
    INVALID_NMTOKEN_ATTR = 81
    QNAME_BUT_NOT_NCNAME = 82
    AVT_SYNTAX = 83
    PATTERN_SYNTAX = 84
    INVALID_AVT = 85
    INVALID_PATTERN = 86
    INVALID_EXPRESSION = 87

    # xsl:apply-imports
    APPLYIMPORTS_WITH_NULL_CURRENT_TEMPLATE = 100

    # xsl:import and xsl:include
    #ILLEGAL_IMPORT = 110
    #IMPORT_NOT_FOUND = 111
    INCLUDE_NOT_FOUND = 112
    CIRCULAR_INCLUDE = 113

    # xsl:choose, xsl:when and xsl:otherwise
    ILLEGAL_CHOOSE_CHILD = 120
    #CHOOSE_REQUIRES_WHEN = 121
    #CHOOSE_WHEN_AFTER_OTHERWISE = 122
    #CHOOSE_MULTIPLE_OTHERWISE = 123
    #WHEN_MISSING_TEST = 124

    # xsl:call-template
    #ILLEGAL_CALLTEMPLATE_CHILD = 130
    NAMED_TEMPLATE_NOT_FOUND = 131

    # xsl:template
    #ILLEGAL_TEMPLATE_PRIORITY = 140
    MULTIPLE_MATCH_TEMPLATES = 141
    DUPLICATE_NAMED_TEMPLATE = 142

    # xsl:attribute
    ATTRIBUTE_ADDED_TOO_LATE = 150
    #ATTRIBUTE_MISSING_NAME = 151
    ATTRIBUTE_ADDED_TO_NON_ELEMENT = 152
    NONTEXT_IN_ATTRIBUTE = 153
    BAD_ATTRIBUTE_NAME = 154

    # xsl:element
    UNDEFINED_ATTRIBUTE_SET = 160

    # xsl:for-each
    INVALID_FOREACH_SELECT = 170

    # xsl:value-of
    #VALUEOF_MISSING_SELECT = 180

    # xsl:copy-of
    #COPYOF_MISSING_SELECT = 190

    # xsl:apply-template
    #ILLEGAL_APPLYTEMPLATE_CHILD = 210
    #ILLEGAL_APPLYTEMPLATE_MODE = 211
    INVALID_APPLY_TEMPLATES_SELECT = 'XTTE0520'

    # xsl:attribute-set
    #ILLEGAL_ATTRIBUTESET_CHILD = 220
    #ATTRIBUTESET_REQUIRES_NAME = 221
    CIRCULAR_ATTRIBUTE_SET = 222

    # xsl:param and xsl:variable
    #ILLEGAL_PARAM = 230
    #ILLEGAL_PARAM_PARENT = 231
    ILLEGAL_SHADOWING = 232
    VAR_WITH_CONTENT_AND_SELECT = 233

    # xsl:message
    #ILLEGAL_MESSAGE_PARENT = 240
    STYLESHEET_REQUESTED_TERMINATION = 241

    # xsl:processing-instruction
    ILLEGAL_XML_PI = 250
    NONTEXT_IN_PI = 251

    # xsl:output
    UNKNOWN_OUTPUT_METHOD = 260

    # xsl:decimal-format
    DUPLICATE_DECIMAL_FORMAT = 270
    UNDEFINED_DECIMAL_FORMAT = 271

    # xsl:sort
    #ILLEGAL_SORT_DATA_TYPE_VALUE = 280
    #ILLEGAL_SORT_CASE_ORDER_VALUE = 281
    #ILLEGAL_SORT_ORDER_VALUE = 282

    # xsl:number
    #ILLEGAL_NUMBER_GROUPING_SIZE_VALUE = 290
    #ILLEGAL_NUMBER_LEVEL_VALUE = 291
    #ILLEGAL_NUMBER_LETTER_VALUE = 292
    ILLEGAL_NUMBER_FORMAT_VALUE = 293
    UNSUPPORTED_NUMBER_LANG_VALUE = 294
    UNSUPPORTED_NUMBER_LETTER_FOR_LANG = 295

    # xsl:namespace-alias
    #INVALID_NAMESPACE_ALIAS = 300

    # xsl:comment
    NONTEXT_IN_COMMENT = 310

    # xsl:fallback and forwards-compatible processing
    FWD_COMPAT_WITHOUT_FALLBACK = 320
    UNKNOWN_EXTENSION_ELEMENT = 321

    # built-in functions and XSLT-specific extension functions
    DOC_FUNC_EMPTY_NODESET = 1000
    UNKNOWN_NODE_BASE_URI = 1001
    #KEY_WITH_RTF_CONTEXT = 1002
    #WRONG_NUMBER_OF_ARGUMENTS = 2000
    WRONG_ARGUMENT_TYPE = 2001
    INVALID_QNAME_ARGUMENT = 2002

    # EXSLT messages use 3000-3999
    UNSUPPORTED_DOCUMENT_URI_SCHEME = 3000
    ABORTED_EXSLDOCUMENT_OVERWRITE = 3010
    NO_EXSLTDOCUMENT_BASE_URI = 3020

    ILLEGAL_DURATION_FORMAT = 3100

    RESULT_NOT_IN_FUNCTION = 3200
    ILLEGAL_RESULT_SIBLINGS = 3201

    # built-in output methods
    RESTRICTED_OUTPUT_VIOLATION = 7000

    #FEATURE_NOT_SUPPORTED = 9999

    @classmethod
    def _load_messages(cls):
        from gettext import gettext as _
        return {
            XsltError.INTERNAL_ERROR: _(
                'There is an internal bug in 4Suite. Please make a post to '
                'the 4Suite mailing list to report this error message to the '
                'developers. Include platform details and info about how to '
                'reproduce the error. Info about the mailing list is at '
                'http://lists.fourthought.com/mailman/listinfo/4suite. '),
            # xsl:stylesheet
            XsltError.NO_STYLESHEET: _(
                'No stylesheets to process.'),
            #XsltError.STYLESHEET_MISSING_VERSION: _(
            #    'Stylesheet %(uri)s, document root element must have a'
            #    ' version attribute.  (see XSLT 1.0 sec. 2.2)'),
            XsltError.LITERAL_RESULT_MISSING_VERSION: _(
                "Document root element must have a 'xsl:version' attribute "
                "(see XSLT 1.0 sec. 2.3)"),
            XsltError.STYLESHEET_PARSE_ERROR: _(
                'Error parsing stylesheet %(uri)s: %(text)s'),
            XsltError.SOURCE_PARSE_ERROR: _(
                'Error parsing source document %(uri)s: %(text)s'),
            #XsltError.XSL_STYLESHEET_NOT_DOCELEM: _(
            #    'An xsl:stylesheet or xsl:transform element must be '
            #    'the document element.'),
            #XsltError.TOP_LEVEL_ELEM_WITH_NULL_NS: _(''),
            XsltError.XSLT_ILLEGAL_ELEMENT: _(
                "Illegal element '%(element)s' in XSLT Namespace "
                "(see XSLT 1.0 sec. 2.1)."),
            #XsltError.STYLESHEET_ILLEGAL_ROOT: _(
            #    'Illegal Document Root Element "%s" (see XSLT 1.0 sec. 2.2).'),
            XsltError.CIRCULAR_VARIABLE: _(
                'Circular variable reference error (see XSLT 1.0 sec. 11.4) for variable or parameter: %(name)s'),
            XsltError.DUPLICATE_TOP_LEVEL_VAR: _(
                'Top level variable %(variable)s has duplicate definitions '
                'with the same import precedence.  (see XSLT 1.0 sec. 11)'),
            XsltError.DUPLICATE_NAMESPACE_ALIAS: _(
                'The namespace for "%s" has duplicate namespace aliases defined with the same import precedence.  (see XSLT 1.0 sec. 2.6.2)'),

            # misc element validation
            XsltError.MISSING_REQUIRED_ELEMENT: _(
                "Element '%(element)s' missing required element '%(child)s'"),
            XsltError.ILLEGAL_ELEMENT_CHILD: _(
                "Element '%(element)s' not allowed here"),
            XsltError.ILLEGAL_TEXT_CHILD: _(
                "Illegal literal text %(data)r within element '%(element)s'"),
            XsltError.UNDEFINED_PREFIX: _(
                "Undefined namespace prefix '%(prefix)s' for element '%(elem)s'"),

            # misc attribute validation
            XsltError.MISSING_REQUIRED_ATTRIBUTE: _(
                "Element '%(element)s' missing required attribute "
                "'%(attribute)s'"),
            XsltError.ILLEGAL_NULL_NAMESPACE_ATTR: _(
                "Illegal null-namespace attribute '%(attribute)s' on "
                "element '%(element)s'"),
            XsltError.ILLEGAL_XSL_NAMESPACE_ATTR: _(
                "Illegal xsl-namespace attribute '%(attribute)s' on "
                "element '%(element)s'"),
            XsltError.INVALID_ATTR_CHOICE: _(
                "Illegal attribute value '%s', must be one of '%s'"),
            XsltError.INVALID_CHAR_ATTR: _(
                "Invalid char attribute value '%s'"),
            XsltError.INVALID_NUMBER_ATTR: _(
                "Invalid number attribute value '%s'"),
            XsltError.INVALID_NS_URIREF_ATTR: _(
                "'%s' is not a valid namespace name (see Namespaces in XML erratum NE05)"),
            XsltError.INVALID_ID_ATTR: _(
                "Invalid ID attribute value '%s'"),
            XsltError.INVALID_QNAME_ATTR: _(
                "Invalid QName attribute value '%(value)s'"),
            XsltError.INVALID_NCNAME_ATTR: _(
                "Invalid NCName attribute value '%s'"),
            XsltError.INVALID_PREFIX_ATTR: _(
                "Invalid prefix attribute value '%s'"),
            XsltError.INVALID_NMTOKEN_ATTR: _(
                "Invalid NMTOKEN attribute value '%s'"),
            XsltError.QNAME_BUT_NOT_NCNAME: _(
                "QName allowed but not NCName, '%s' found"),
            XsltError.AVT_SYNTAX: _(
                'Unbalanced curly braces ({}) in attribute value template. (see XSLT 1.0 sec. 7.6.2)'),
            XsltError.INVALID_AVT: _(
                "Malformed attribute value template file=%(baseuri)s, line=%(line)s, column=%(col)s ('%(value)s' '%(msg)s')"),
            XsltError.INVALID_PATTERN: _(
                'XPattern expression syntax error at line %(line)d, '
                'column %(column)d: %(text)s'),
            XsltError.INVALID_EXPRESSION: _(
                "Malformed XPath expression '%(text)s'"),

            # xsl:apply-imports
            XsltError.APPLYIMPORTS_WITH_NULL_CURRENT_TEMPLATE: _(
                'xsl:apply-imports used where there is no current template. '
                ' (see XSLT Spec)'),

            # xsl:import and xsl:include
            #XsltError.ILLEGAL_IMPORT: _(
            #    'xsl:import is not allowed here (xsl:import must be at top '
            #    'level and precede all other XSLT top-level instructions). '
            #    '(see XSLT 1.0 sec. 2.6.2)'),
            #XsltError.IMPORT_NOT_FOUND: _(''),
            XsltError.INCLUDE_NOT_FOUND: _(
                "Unable to retrieve the stylesheet '%(uri)s', "
                "using base URI '%(base)s'"),
            XsltError.CIRCULAR_INCLUDE: _(
                "Stylesheet '%(uri)s' may not be included or imported more "
                "than once (see XSLT 1.0 sec. 2.6)"),

            # xsl:choose, xsl:when and xsl:otherwise
            XsltError.ILLEGAL_CHOOSE_CHILD: _('FIXME'),
            #XsltError.CHOOSE_REQUIRES_WHEN: _(
            #    'xsl:choose must have at least one xsl:when child '
            #    '(see XSLT 1.0 sec. 9.2)'),
            #XsltError.CHOOSE_WHEN_AFTER_OTHERWISE: _(
            #    "'xsl:choose' cannot have 'xsl:when' child after "
            #    "'xsl:otherwise' child (see XSLT 1.0 sec. 9.2)"),
            #XsltError.CHOOSE_MULTIPLE_OTHERWISE: _(
            #    "'xsl:choose only allowed one 'xsl:otherwise' child "
            #    "(see XSLT 1.0 sec. 9.2)'"),
            #XsltError.WHEN_MISSING_TEST: _(
            #    "'xsl:when' requires 'test' attribute "
            #    "(see XSLT 1.0 sec. 9.2)'"),

            # xsl:call-template
            #XsltError.ILLEGAL_CALLTEMPLATE_CHILD: _(
            #    "'xsl:call-template' child must be 'xsl:with-param' "
            #    "(see XSLT 1.0 sec. 6)'"),
            XsltError.NAMED_TEMPLATE_NOT_FOUND: _(
                "Named template '%s' invoked but not defined."),

            # xsl:template
            #XsltError.ILLEGAL_TEMPLATE_PRIORITY: _(
            #    'Invalid priority value for template '
            #    '(see XSLT 1.0 sec. 5.5)'),
            XsltError.MULTIPLE_MATCH_TEMPLATES: _(
                "Multiple templates matching node '%r' "
                "(see XSLT 1.0 sec. 5.5).\n"
                "Conflicting template locations:\n%s"),
            XsltError.DUPLICATE_NAMED_TEMPLATE: _(
                "Named template '%(template)s' already defined with same "
                "import precedence"),

            # xsl:attribute
            XsltError.ATTRIBUTE_ADDED_TOO_LATE: _(
                "Children were added to element before 'xsl:attribute' "
                "instantiation (see XSLT 1.0 sec. 7.1.3)"),
            #XsltError.ATTRIBUTE_MISSING_NAME: _(
            #    "'xsl:attribute' missing required 'name' attribute "
            #    "(see XSLT 1.0 sec. 7.1.3)"),
            XsltError.ATTRIBUTE_ADDED_TO_NON_ELEMENT: _(
                "'xsl:attribute' attempted to add attribute to non-element "
                "(see XSLT 1.0 sec. 7.1.3)"),
            XsltError.NONTEXT_IN_ATTRIBUTE: _(
                "Nodes other than text nodes created during 'xsl:attribute' "
                "instantiation (see XSLT 1.0 sec. 7.1.3)"),
            XsltError.BAD_ATTRIBUTE_NAME: _(
                "An attribute cannot be created with name '%s' "
                "(see XSLT 1.0 sec. 7.1.3)"),

            # xsl:element
            XsltError.UNDEFINED_ATTRIBUTE_SET: _(
                "Undefined attribute set '%(name)s'"),

            # xsl:for-each
            XsltError.INVALID_FOREACH_SELECT: _(
                "'select' expression must evaluate to a node-set."),

            # xsl:value-of
            #XsltError.VALUEOF_MISSING_SELECT: _('Empty "value-of" requires "select" attribute (see XSLT 1.0 sec. 7.6.1)'),

            # xsl:copy-of
            #XsltError.COPYOF_MISSING_SELECT: _('Empty "copy-of" requires "select" attribute (see XSLT 1.0 sec. 11.3)'),

            # xsl:apply-templates
            #XsltError.ILLEGAL_APPLYTEMPLATE_CHILD: _('apply-templates child must be with-param or sort. (see XSLT Spec 5.4)'),
            #XsltError.ILLEGAL_APPLYTEMPLATE_MODE: _('apply-templates mode must be a QName. (see XSLT Spec 5.4)'),
            XsltError.INVALID_APPLY_TEMPLATES_SELECT: _(
                "'select' expression must evaluate to a node-set."),

            # xsl:attribute-set
            #XsltError.ILLEGAL_ATTRIBUTESET_CHILD: _('xsl:attribute-set child must be "attribute" (see XSLT 1.0 sec. 7.1.4)'),
            #XsltError.ATTRIBUTESET_REQUIRES_NAME: _('xsl:attribute-set requires "name" attribute (see XSLT 1.0 sec. 7.1.4)'),
            XsltError.CIRCULAR_ATTRIBUTE_SET: _("Circular attribute-set error for '%s'. (see XSLT 1.0 sec. 7.1.4)"),

            # xsl:param and xsl:variable
            #XsltError.ILLEGAL_PARAM: _('xsl:param elements must be the first children of xsl:template (see XSLT 1.0 sec. 11).'),
            #XsltError.ILLEGAL_PARAM_PARENT: _('Uri: %s line %s col: %s\n   xsl:param can only appear at top level or as the child of an xsl:template (see XSLT 1.0 sec. 11).'),
            XsltError.ILLEGAL_SHADOWING: _('Illegal shadowing of %(variable)s.  An xsl:param or xsl:variable may not shadow another variable not at top level (see XSLT 1.0 sec. 11).'),
            XsltError.VAR_WITH_CONTENT_AND_SELECT: _('Illegal binding of of %(name)s.  An xsl:param or xsl:variable may not have both a select attribute and non-empty content. (see XSLT 1.0 sec. 11.2).'),

            # xsl:message
            #XsltError.ILLEGAL_MESSAGE_PARENT: _('xsl:message cannot be a top-level element. (see XSLT 1.0 sec. 2.2)'),
            XsltError.STYLESHEET_REQUESTED_TERMINATION: _('A message instruction in the Stylesheet requested termination of processing:\n%(msg)s'),

            # xsl:processing-instruction
            XsltError.ILLEGAL_XML_PI: _('A processing instruction cannot be used to output an XML or text declaration. (see XSLT 1.0 sec. 7.3)'),
            XsltError.NONTEXT_IN_PI: _('Nodes other than text nodes created during xsl:processing-instruction instantiation. (see XSLT 1.0 sec. 7.4)'),

            # xsl:output
            XsltError.UNKNOWN_OUTPUT_METHOD: _('Unknown output method (%s)'),

            # xsl:decimal-format
            XsltError.DUPLICATE_DECIMAL_FORMAT: _('Duplicate declaration of decimal-format %s. (XSLT Spec: 12.3)'),
            XsltError.UNDEFINED_DECIMAL_FORMAT: _('Undefined decimal-format (%s)'),

            # xsl:sort
            #XsltError.ILLEGAL_SORT_CASE_ORDER_VALUE: _('The case-order attribute of sort must be either "upper-first" or "lower-first" (see XSLT 1.0 sec. 10)'),
            #XsltError.ILLEGAL_SORT_DATA_TYPE_VALUE: _('The data-type attribute of sort must be either "text" or "number" (see XSLT 1.0 sec. 10).'),
            #XsltError.ILLEGAL_SORT_ORDER_VALUE: _('The order attribute of sort must be either "ascending" or "descending". (see XSLT 1.0 sec. 10)'),

            # xsl:number
            #XsltError.ILLEGAL_NUMBER_GROUPING_SIZE_VALUE: _('The "grouping-size" attribute of number must be an integer. (see XSLT 1.0 sec. 7.7.1)'),
            #XsltError.ILLEGAL_NUMBER_LEVEL_VALUE: _('The "level" attribute of number must be "single", "multiple" or "any". (see XSLT 1.0 sec. 7.7)'),
            #XsltError.ILLEGAL_NUMBER_LETTER_VALUE: _('The "letter-value" attribute of number must be "alphabetic" or "traditional". (see XSLT 1.0 sec. 7.7.1)'),
            XsltError.ILLEGAL_NUMBER_FORMAT_VALUE: _('Value "%s" for "format" attribute of xsl:number is invalid. (see XSLT 1.0 sec. 7.7)'),
            XsltError.UNSUPPORTED_NUMBER_LANG_VALUE: _('Language "%s" for alphabetic numbering in xsl:number is unsupported.'),
            XsltError.UNSUPPORTED_NUMBER_LETTER_FOR_LANG: _('Value "%s" for "letter-value" attribute of xsl:number is not supported with the language "%s".'),

            # xsl:namespace-alias
            #XsltError.INVALID_NAMESPACE_ALIAS: _('Invalid arguments to the namespace-alias instruction. (see XSLT 1.0 sec. 7.1.1)'),

            # xsl:comment
            XsltError.NONTEXT_IN_COMMENT: _('Nodes other than text nodes created during xsl:comment instantiation. (see XSLT 1.0 sec. 7.4)'),

            # xsl:fallback and forwards-compatible processing
            XsltError.FWD_COMPAT_WITHOUT_FALLBACK: _(
                "No 'xsl:fallback' instruction found for element '%(element)s' "
                "processed in forward-compatible mode."),
            XsltError.UNKNOWN_EXTENSION_ELEMENT: _(
                "'No implementation for extension element '%(element)s'"),

            # built-in functions and XSLT-specific extension functions
            XsltError.DOC_FUNC_EMPTY_NODESET: _('Second argument to document(), if given, must be a non-empty node-set. (see XSLT 1.0 sec. 12.1 erratum E14)'),
            XsltError.UNKNOWN_NODE_BASE_URI: _('Could not determine base URI of node: %s'),
            #XsltError.KEY_WITH_RTF_CONTEXT: _('key() must not be invoked when the context node comes from the result tree (probably due to an earlier invokation of node-set()).'),
            #XsltError.WRONG_NUMBER_OF_ARGUMENTS: _('A built-in or extension function was called with the wrong number of arguments.'),
            XsltError.WRONG_ARGUMENT_TYPE: _('A built-in or extension function was called with the wrong type of argument(s).'),
            XsltError.INVALID_QNAME_ARGUMENT: _('A built-in or extension function requiring a QName argument was called with this non-QName value: "%(value)s".'),

            # EXSLT messages use 3000-3999
            XsltError.UNSUPPORTED_DOCUMENT_URI_SCHEME: _(
                "Amara's implementation of `exsl:document` only supports an "
                "href value having the 'file' URI scheme, which may be "
                "implicit. Scheme '%(scheme)s' was found."),
            XsltError.ABORTED_EXSLDOCUMENT_OVERWRITE: _(
                "An attempt was made to write to '%(filename)s', which "
                "already exists.  The attempt to save the contents of this "
                "file to '%(backup)s' also failed, and so the instruction has "
                "been aborted.  If you are sure it is OK to overwrite this "
                "file, please indicate this by adding the `f:overwrite-okay` "
                "attribute to the `exsl:document` instruction."),
            XsltError.NO_EXSLTDOCUMENT_BASE_URI: _(
                "An `exsl:document` element referred to a relative reference "
                "'%(uriref)s', but there is no explicit output document to "
                "provide a base URI in order to resolve this relative "
                "reference."),
            XsltError.ILLEGAL_DURATION_FORMAT: _(
                "Duration string '%(duration)s' not in `xs:duration` format."),
            XsltError.RESULT_NOT_IN_FUNCTION: _(
                "An EXSLT `func:result` element must occur within a "
                "`func:function` element."),
            XsltError.ILLEGAL_RESULT_SIBLINGS: _(
                "An EXSLT `func:result` element must not have following "
                "sibling elements besides `xsl:fallback.`"),

            # built-in output methods
            XsltError.RESTRICTED_OUTPUT_VIOLATION: _('The requested output of element "%s" is forbidden according to output restrictions'),

            #XsltError.FEATURE_NOT_SUPPORTED: _('4XSLT does not yet support this feature.'),
        }


class XsltStaticError(XsltError, TypeError):
    def __init__(self, code, xslt_element, **kwords):
        XsltError.__init__(self, code, **kwords)
        # Just save the information needed from `xslt_element`
        self.uri = xslt_element.baseUri
        self.lineno = xslt_element.lineNumber
        self.offset = xslt_element.columnNumber
        self.tagname = xslt_element.nodeName

    def __str__(self):
        from gettext import gettext as _
        return _("Stylesheet '%s', line %s, column %s, in '%s': %s") % (
            self.uri, self.lineno, self.offset, self.tagname, self.message)


class XsltRuntimeError(XsltError, RuntimeError):

    @classmethod
    def update_error(cls, error, xslt_element):
        error.__class__ = cls
        error.uri = xslt_element.baseUri
        error.lineno = xslt_element.lineNumber
        error.offset = xslt_element.columnNumber
        error.tagname = xslt_element.nodeName

    def __init__(self, code, xslt_element, **kwords):
        XsltError.__init__(self, code, **kwords)
        # Just save the information needed from `xslt_element`
        self.uri = xslt_element.baseUri
        self.lineno = xslt_element.lineNumber
        self.offset = xslt_element.columnNumber
        self.tagname = xslt_element.nodeName

    def __str__(self):
        from gettext import gettext as _
        return _("Stylesheet '%s', line %s, column %s, in '%s': %s") % (
            self.uri, self.lineno, self.offset, self.tagname, self.message)


def transform(source, transforms, params=None, output=None):
    """
    Convenience function for applying an XSLT transform.  Returns
    a result object.

    source - XML source document in the form of a string (not Unicode
             object), file-like object (stream), file path, URI or
             amara.lib.inputsource instance.  If string or stream
             it must be self-contained  XML (i.e. not requiring access to
             any other resource such as external entities or includes)
    transforms - XSLT document (or list thereof) in the form of a string, stream, URL,
                file path or amara.lib.inputsource instance
    params - optional dictionary of stylesheet parameters, the keys of
             which may be given as unicode objects if they have no namespace,
             or as (uri, localname) tuples if they do.
    output - optional file-like object to which output is written (incrementally, as processed)
    """
    #do the imports within the function: a tad bit less efficient, but
    #avoid circular crap
    from amara.lib import inputsource
    from amara.xpath.util import parameterize
    from amara.xslt.result import streamresult, stringresult
    from amara.xslt.processor import processor
    params = parameterize(params) if params else {}
    proc = processor()
    if isinstance(transforms, (list, tuple)):
        for transform in transforms:
            proc.append_transform(inputsource(transform))
    else:
        proc.append_transform(inputsource(transforms))
    if output is not None:
        result = streamresult(output)
    else:
        result = stringresult()
    return proc.run(inputsource(source), params, result)


def launch(*args, **kwargs):
    source = args[0]
    transforms = args[1:]
    out = sys.stdout
    #print >> out, 
    params = dict(( k.split(u'=') for k in kwargs.get('define', []) ))
    #print params
    transform(source, transforms, params=params, output=out)
    return


help_message = '''
Amara 2.x.  Command line support for XSLT processing.
'''

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hD:v", ["help", "define="])
        except getopt.error, msg:
            raise Usage(msg)
    
        # option processing
        kwargs = {}
        for option, value in opts:
            if option == "-v":
                verbose = True
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-D", "--define"):
                kwargs.setdefault('define', []).append(value)
    
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2

    launch(*args, **kwargs)


if __name__ == "__main__":
    sys.exit(main())

