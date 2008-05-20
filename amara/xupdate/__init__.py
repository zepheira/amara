########################################################################
# amara/xupdate/__init__.py
"""
XUpdate request processing
"""

from amara import Error
from amara._xmlstring import IsQName

__all__ = ['XUPDATE_NAMESPACE', 'XUpdateError']

XUPDATE_NAMESPACE = u'http://www.xmldb.org/xupdate'

class XUpdateError(Error):
    """
    Exception class for errors specific to XUpdate processing
    """
    SYNTAX_ERROR = 1
    ILLEGAL_ELEMENT = 2
    ILLEGAL_ELEMENT_CHILD = 3
    MISSING_REQUIRED_ATTRIBUTE = 4
    INVALID_TEXT = 5

    UNSUPPORTED_VERSION = 10
    INVALID_SELECT = 11

    @classmethod
    def _load_messages(cls):
        from gettext import gettext as _
        return {
            XUpdateError.SYNTAX_ERROR: _(
                'Syntax error in expression %(expression)r: %(text)s'),
            XUpdateError.ILLEGAL_ELEMENT: _(
                "Illegal element '%(element)s' in XUpdate namespace"),
            XUpdateError.ILLEGAL_ELEMENT_CHILD: _(
                "Illegal child '%(child)s' within element '%(element)s'"),
            XUpdateError.MISSING_REQUIRED_ATTRIBUTE: _(
                "Element '%(element)s' missing required attribute "
                "'%(attribute)s'"),
            XUpdateError.INVALID_TEXT: _(
                "Character data not allowed in the content of element "
                "'%(element)s'"),

            XUpdateError.UNSUPPORTED_VERSION: _(
                "XUpdate version ''%(version)s' unsupported by this "
                "implementation"),
            XUpdateError.INVALID_SELECT: _(
                'select expression "%(expr)s" must evaluate to a non-empty '
                'node-set'),
        }


class xupdate_element(object):
    class __metaclass__ignore(type):
        def __init__(cls, name, bases, namespace):
            # The base class, the one defining the metaclass, is not a
            # candidate for the dispatch table.
            if '__metaclass__' in namespace and cls.__base__ is object:
                return
            # All other sub-classes *MUST* define the attribute `element`.
            try:
                mapping[cls.element_name] = cls
            except AttributeError:
                raise TypeError("class '%s' must define attribute "
                                "'element_name'" % (name,))

    __slots__ = ('namespaces', 'attributes')

    def __init__(self, tagname, namespaces, attributes):
        self.namespaces = namespaces
        self.attributes = attributes
        return
