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
    UNDEFINED_PREFIX = 12

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
            XUpdateError.UNDEFINED_PREFIX: _(
                'Undefined namespace prefix %(prefix)r'),
        }


class xupdate_primitive(list):
    # Note, no need to call `list.__init__` if there are no initial
    # items to be added. `list.__new__` takes care of the setup for
    # new empty lists.

    # `pipeline` indicates in which processing stage a command should be
    # executed. The default value of `0` indicates a non-command and thus
    # will be ignored.
    pipeline = 0

    has_setup = False
    def setup(self):
        pass

    def instantiate(self, context):
        raise NotImplementedError("subclass '%s' must override" %
                                  self.__class__.__name__)

# -- High-level API ----------------------------------------------------

from amara import tree
from amara.xupdate import reader

def apply_xupdate(source, xupdate):
    xupdate = reader.parse(xupdate)
    source = tree.parse(source)
    return xupdate.apply_updates(source)
