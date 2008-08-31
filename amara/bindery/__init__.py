########################################################################
# amara/bindery/__init__.py

"""
Extra friendly XML node API for Python
"""

def parse(obj, uri=None, node_factories=None, standalone=False, validate=False):
    from amara import tree
    if not node_factories:
        node_factories = FACTORIES
    return tree.parse(obj, uri, node_factories=node_factories, standalone=False, validate=False)


#FIXME: Use proper L10N (gettext)
def _(t): return t

from nodes import *

