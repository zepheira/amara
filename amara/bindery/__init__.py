########################################################################
# amara/bindery/__init__.py

"""
Extra friendly XML node API for Python
"""

import nodes
from amara import Error

def parse(obj, uri=None, entity_factory=None, standalone=False, validate=False, model=None):
    from amara import tree
    if model:
        entity_factory = model.clone
    if not entity_factory:
        entity_factory = nodes.entity_base
    return tree.parse(obj, uri, entity_factory=entity_factory, standalone=standalone, validate=validate)


class BinderyError(Error):
    CONSTRAINT_VIOLATION = 1

    @classmethod
    def _load_messages(cls):
        from gettext import gettext as _
        return {
            # -- internal/unexpected errors --------------------------------
            BinderyError.CONSTRAINT_VIOLATION: _(
                'Failed constraint: %(constraint)s'),
        }


#FIXME: Use proper L10N (gettext)
def _(t): return t

