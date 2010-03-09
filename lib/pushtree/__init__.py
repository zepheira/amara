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
    
    # Create a rule handler object
    rhand = RulePatternHandler(pattern,target,namespaces)

    # Run the parser on the rule handler
    return parse(obj,uri,entity_factory,standalone,validate,rule_handler=rhand)


