# __init__.py
#
# Pushtree interface

from pushtree_nfa import PushtreeManager, RuleMachineHandler
from amara.tree import parse

# ------------------------------------------------------------
# Experimental pushtree() support.   This should not be used
# for any kind of production.  It is an experimental prototype
# ------------------------------------------------------------

def pushtree(obj, pattern, target, uri=None, entity_factory=None, standalone=False, validate=False, namespaces=None):
    # Adapter for what Dave uses. FIXME?!
    class Handler(object):
        def startElementMatch(self, node):
            pass
        def endElementMatch(self, node):
            target(node)
        def attributeMatch(self, pair):
            # Returns the node and the attribute name (hack!)
            # Get just the node
            target(pair[0])
    
    # Create a rule handler object
    mgr = PushtreeManager(pattern, Handler(),
                          namespaces = namespaces)
    rhand = mgr.build_pushtree_handler()

    # Run the parser on the rule handler
    return parse(obj,uri,entity_factory,standalone,validate,rule_handler=rhand)


