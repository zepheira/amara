########################################################################
# amara/dom/__init__.py

"""
Old school W3C DOM...mostly
"""

def parse(obj, uri=None, node_factories=None, standalone=False, validate=False):
    import factory
    from amara import tree
    if not node_factories:
        node_factories = factory.FACTORIES
    return tree.parse(obj, uri, node_factories=node_factories, standalone=standalone, validate=validate)


#FIXME: Use proper L10N (gettext)
def _(t): return t

from nodes import *

