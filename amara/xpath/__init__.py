########################################################################
# amara/xpath/__init__.py
"""
XPath initialization and principal functions
"""

EXTENSION_NAMESPACE = 'http://xmlns.4suite.org/ext'

__all__ = [# global constants:
           'EXTENSION_NAMESPACE',
           # exception class:
           'XPathError',
           # XPath expression processing:
           #'Compile', 'Evaluate', 'SimpleEvaluate',
           # DOM preparation for XPath processing:
           #'NormalizeNode',
           'context'
           ]


# -- XPath exceptions --------------------------------------------------------

from amara import Error

class XPathError(Error):
    """
    Base class for exceptions specific to XPath processing
    """

    # internal or other unexpected errors
    INTERNAL = 1

    # syntax or other static errors
    SYNTAX             = 10
    UNDEFINED_VARIABLE = 11
    UNDEFINED_PREFIX   = 12
    UNDEFINED_FUNCTION = 13
    ARGCOUNT_NONE      = 14
    ARGCOUNT_ATLEAST   = 15
    ARGCOUNT_EXACT     = 16
    ARGCOUNT_ATMOST    = 17

    TYPE_ERROR         = 20

    NO_CONTEXT         = 30

    @classmethod
    def _load_messages(cls):
        from gettext import gettext as _
        return {
            # -- internal/unexpected errors --------------------------------
            XPathError.INTERNAL: _(
                'There is an internal bug in 4XPath.  Please make a post to '
                'the 4Suite mailing list to report this error message to the '
                'developers. Include platform details and info about how to '
                'reproduce the error. Info about the mailing list is at '
                'http://lists.4suite.org/mailman/listinfo/4suite.\n'
                'The error code to report is: %s'),

            # -- expression syntax errors ----------------------------------
            XPathError.SYNTAX: _(
                'XPath expression syntax error at line %(line)d, '
                'column %(column)d: %(text)s'),
            XPathError.UNDEFINED_VARIABLE: _(
                "Variable '%(variable)s' not declared"),
            XPathError.UNDEFINED_PREFIX: _(
                'Undefined namespace prefix: "%(prefix)s".'),
            XPathError.UNDEFINED_FUNCTION: _(
                'Undefined function: "%(function)s".'),
            XPathError.ARGCOUNT_NONE: _(
                '%(function)s() takes no arguments (%(total)d given)'),
            XPathError.ARGCOUNT_ATLEAST: _(
                '%(function)s() takes at least %(count)d arguments '
                '(%(total)d given)'),
            XPathError.ARGCOUNT_EXACT: _(
                '%(function)s() takes exactly %(count)d arguments '
                '(%(total)d given)'),
            XPathError.ARGCOUNT_ATMOST: _(
                '%(function)s() takes at most %(count)d arguments '
                '(%(total)d given)'),
            XPathError.TYPE_ERROR: _(
                "%(what)s must be '%(expected)s', not '%(actual)s'"),

            # -- evaluation errors -----------------------------------------
            XPathError.NO_CONTEXT: _(
                'An XPath Context object is required in order to evaluate an '
                'expression.'),
            }

# -- Additional setup --------------------------------------------------------

# -- Core XPath API ----------------------------------------------------------

#from Util import Compile, Evaluate, SimpleEvaluate, NormalizeNode

import types

from amara import XML_NAMESPACE
from amara.xpath import extensions
from amara.xpath import parser

class context:
    """
    The context of an XPath expression
    """
    functions = extensions.extension_functions
    currentInstruction = None

    def __init__(self, node, position=1, size=1,
                 variables=None, namespaces=None,
                 extmodules=(), extfunctions=None):
        self.node, self.position, self.size = node, position, size
        self.variables = variables or {}
        self.namespaces = {'xml': XML_NAMESPACE}
        if namespaces:
            self.namespaces.update(namespaces)

        # This may get mutated during processing
        self.functions = self.functions.copy()
        # Search the extension modules for defined functions
        for module in extmodules:
            if module:
                if not isinstance(module, types.ModuleType):
                    module = __import__(module, {}, {}, ['ExtFunctions'])
                funcs = getattr(module, 'extension_functions', None)
                if funcs:
                    self.functions.update(funcs)
        # Add functions given directly
        if extfunctions:
            self.functions.update(extfunctions)
        return

    def __repr__(self):
        ptr = id(self)
        if ptr < 0: ptr += 0x100000000L
        return "<Context at 0x%x: Node=%s, Postion=%d, Size=%d>" % (
            ptr, self.node, self.position, self.size)

    def addFunction(self, expandedName, function):
        if not callable(function):
            raise TypeError("function must be a callable object")
        self.functions[expandedName] = function
        return

    def copy(self):
        return (self.node, self.position, self.size)

    def set(self, state):
        self.node, self.position, self.size = state
        return

    def clone(self):
        newobj = self.__class__(self, self.node, self.position, self.size)
        newobj.variables = self.variables.copy()
        newobj.namespaces = self.namespaces.copy()
        return newobj

    def evaluate(self, expr):
        """
        The main entry point for evaluating an XPath expression, using self as context
        expr - a unicode object with the XPath expression
        """
        parsed = parser.parse(expr)
        return parsed.evaluate(self)

