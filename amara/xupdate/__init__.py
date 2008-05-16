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
    MISSING_REQUIRED_ATTRIBUTE = 3

    UNSUPPORTED_VERSION = 10

    UNRECOGNIZED_INSTRUCTION = 2
    NO_VERSION = 10
    NO_SELECT = 11
    NO_TEST = 12
    INVALID_SELECT = 13
    UNSUPPORTED_VERSION = 14
    INVALID_DOM_NODE = 100
    UNKNOWN_NODE_TYPE = 101

    @classmethod
    def _load_messages(cls):
        from gettext import gettext as _
        return {
            XUpdateError.SYNTAX_ERROR: _(
                'Syntax error in expression %(expression)r: %(text)s'),
            XUpdateError.UNSUPPORTED_VERSION: _('XUpdate version %(version)s unsupported by this implementation'),
            XUpdateError.ILLEGAL_ELEMENT: _(
                "Illegal element '%(element)s' in XUpdate namespace"),
            XUpdateError.MISSING_REQUIRED_ATTRIBUTE: _(
                "Element '%(element)s' missing required attribute "
                "'%(attribute)s'"),
            XUpdateException.INVALID_SELECT: _('select expression "%(expr)s" must evaluate to a non-empty node-set'),
            XUpdateException.INVALID_DOM_NODE: _('Invalid DOM node %(node)r'),
            XUpdateException.UNKNOWN_NODE_TYPE: _('Unknown node type %(nodetype)r'),
        }


class xupdate_element(object):
    class __metaclass__(type):
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


class handler(object):

    def startDocument(self):
        self._updates = []
        self._dispatch = {}
        self._new_namespaces = {}

    def startPrefixMapping(self, prefix, uri):
        self._new_namespaces[prefix] = uri

    def startElement(self, expandedName, tagName, attributes):
        parent_state = self._state_stack[-1]
        state = parsestate(**parent_state.__dict__)
        self._state_stack.append(state)

        # ------------------------------------------------------
        # udate in-scope namespaces
        namespaces = state.namespaces
        if self._new_namespaces:
            namespaces = state.namespaces = namespaces.copy()
            namespaces.update(self._new_namespaces)
            self._new_namespaces = {}

        # ------------------------------------------------------
        # get the class defining this element
        namespace, local = expandedName
        if namespace == XUPDATE_NAMESPACE:
            try:
                factory = state.dispatch[local]
            except KeyError:
                raise XUpdateError(XUpdateError.ILLEGAL_ELEMENT,
                                   element=tagName)
        else:
            pass
        return

    def endElement(self, expandedName, tagName):
        return

    def characters(self, data):
        return