# __init__.py
#
# Pushtree interface

from pushtree_nfa import RulePatternHandler
from amara.tree import parse

# ------------------------------------------------------------
# Experimental pushtree() support.   This should not be used
# for any kind of production.  It is an experimental prototype
# ------------------------------------------------------------

def pushtree(obj, pattern, target, uri=None, entity_factory=None, standalone=False, validate=False, namespaces=None):

    # Adapter for what Dave uses. FIXME?!
    # The target is only called on endElement. There are other
    # handlers for more complex rules, which isn't yet supported.
    def node_handler(event_ids, node):
        target(node)
    def attr_handler(event_ids, pair):
        target(pair[0]) # the node
    
    # Create a rule handler object
    rhand = RulePatternHandler(pattern, node_handler, attr_handler,
                               namespaces = namespaces)

    # Run the parser on the rule handler
    return parse(obj,uri,entity_factory,standalone,validate,rule_handler=rhand)


