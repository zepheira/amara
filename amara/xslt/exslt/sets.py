########################################################################
# amara/xslt/exslt/sets.py
"""
EXSLT 2.0 - Sets (http://www.exslt.org/set/index.html)
"""
import itertools

from amara.xpath import datatypes

EXSL_SETS_NS = "http://exslt.org/sets"

def difference_function(context, nodeset1, nodeset2):
    """
    The set:difference function returns the difference between two node
    sets - those nodes that are in the node set passed as the first argument
    that are not in the node set passed as the second argument.
    """
    nodeset1 = set(nodeset1.evaluate_as_nodeset(context))
    nodeset2 = set(nodeset2.evaluate_as_nodeset(context))
    return datatypes.nodeset(nodeset1 - nodeset2)


def distinct_function(context, nodeset):
    """
    The set:distinct function returns a subset of the nodes contained in the
    node-set NS passed as the first argument. Specifically, it selects a node
    N if there is no node in NS that has the same string value as N, and that
    precedes N in document order.
    """
    nodeset = nodeset.evaluate_as_nodeset(context)
    # Process the nodes in reverse document-order so that same-value keys
    # will be mapped to the first (in document order) node.
    nodeset.reverse()
    strings = itertools.imap(datatypes.string, nodeset)
    result = dict(itertools.izip(strings, nodeset))
    return datatypes.nodeset(result.values())


def has_same_node_function(context, nodeset1, nodeset2):
    """
    The set:has-same-node function returns true if the node set passed as the
    first argument shares any nodes with the node set passed as the second
    argument. If there are no nodes that are in both node sets, then it
    returns false. 
    """
    nodeset1 = nodeset1.evaluate_as_nodeset(context)
    nodeset2 = nodeset2.evaluate_as_nodeset(context)
    nodeset2 = set(nodeset2)
    for node in nodeset1:
        if node in nodeset2:
            return datatypes.TRUE
    return datatypes.FALSE


def intersection_function(context, nodeset1, nodeset2):
    """
    The set:intersection function returns a node set comprising the nodes that
    are within both the node sets passed as arguments to it. 
    """
    nodeset1 = set(nodeset1.evaluate_as_nodeset(context))
    nodeset2 = set(nodeset2.evaluate_as_nodeset(context))
    return datatypes.nodeset(nodeset1 & nodeset2)


def leading_function(context, nodeset1, nodeset2):
    """
    The set:leading function returns the nodes in the node set passed as the
    first argument that precede, in document order, the first node in the node
    set passed as the second argument. If the first node in the second node
    set is not contained in the first node set, then an empty node set is
    returned. If the second node set is empty, then the first node set is
    returned.
    """
    nodeset1 = nodeset1.evaluate_as_nodeset(context)
    nodeset2 = nodeset2.evaluate_as_nodeset(context)
    try:
        index = nodeset.index(nodeset2[0])
    except IndexError:
        # `nodeset2` is empty
        return nodeset1
    except ValueError:
        # `nodeset2[0]` not in `nodeset1`
        index = 0
    return nodeset1[:index]


def trailing_function(context, nodeset1, nodeset2):
    """
    The set:trailing function returns the nodes in the node set passed as the
    first argument that follow, in document order, the first node in the node
    set passed as the second argument. If the first node in the second node
    set is not contained in the first node set, then an empty node set is
    returned. If the second node set is empty, then the first node set is
    returned. 
    """
    nodeset1 = nodeset1.evaluate_as_nodeset(context)
    nodeset2 = nodeset2.evaluate_as_nodeset(context)
    try:
        index = nodeset.index(nodeset2[0])
    except IndexError:
        # `nodeset2` is empty
        return nodeset1
    except ValueError:
        # `nodeset2[0]` not in `nodeset1`
        index = len(nodeset1)
    else:
        index += 1
    return nodeset1[index:]

## XSLT Extension Module Interface ####################################

extension_namespaces = {
    EXSL_SETS_NS : 'set',
    }

extension_functions = {
    (EXSL_SETS_NS, 'difference'): difference_function,
    (EXSL_SETS_NS, 'distinct'): distinct_function,
    (EXSL_SETS_NS, 'has-same-node'): has_same_node_function,
    (EXSL_SETS_NS, 'intersection'): intersection_function,
    (EXSL_SETS_NS, 'leading'): leading_function,
    (EXSL_SETS_NS, 'trailing'): trailing_function,
    }

extension_elements = {
    }

