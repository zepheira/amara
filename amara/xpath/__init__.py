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

    def __init__(self, code, **kwds):
        import MessageSource
        messages = MessageSource.ERROR_STRINGS
        Error.__init__(self, code, messages, args, **kwds)


# -- Additional setup --------------------------------------------------------

# -- Core XPath API ----------------------------------------------------------

#from Util import Compile, Evaluate, SimpleEvaluate, NormalizeNode
