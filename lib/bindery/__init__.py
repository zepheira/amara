########################################################################
# amara/bindery/__init__.py

"""
Extra friendly XML node API for Python
"""

from amara import Error
from amara.lib.util import set_namespaces
from amara import tree

def parse(obj, uri=None, entity_factory=None, standalone=False, validate=False, prefixes=None, model=None):
    if model:
        entity_factory = model.clone
    if not entity_factory:
        entity_factory = nodes.entity_base
    doc = tree.parse(obj, uri, entity_factory=entity_factory, standalone=standalone, validate=validate)
    if prefixes: set_namespaces(doc, prefixes)
    return doc


class BinderyError(Error):
    CONSTRAINT_VIOLATION = 1

    @classmethod
    def _load_messages(cls):
        from gettext import gettext as _
        return {
            # -- internal/unexpected errors --------------------------------
            BinderyError.CONSTRAINT_VIOLATION: _(
                'Failed constraint: "%(constraint)s" in context of node %(node)s.'),
        }


#FIXME: Use proper L10N (gettext)
def _(t): return t

import nodes
