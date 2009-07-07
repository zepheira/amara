########################################################################
# amara/dom/__init__.py

"""
Old school W3C DOM...mostly
"""

import nodes

def parse(obj, uri=None, entity_factory=None, standalone=False, validate=False):
    from amara import tree
    if not entity_factory:
        entity_factory = nodes.Document
    return tree.parse(obj, uri, entity_factory=entity_factory, standalone=standalone, validate=validate)


#FIXME: Use proper L10N (gettext)
def _(t): return t

