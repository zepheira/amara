########################################################################
# amara/lib/util.py

"""
Some utilities for Amara overall
"""

from amara import tree
from itertools import *


def element_subtree_iter(node, include_root=False):
    '''
    An iterator over the subtree, in document order, elements in the given subtree

    Basically equivalent to the descendant-or-self axis of XPath
    '''
    if isinstance(node, tree.element) or (include_root and isinstance(node, tree.entity)):
        process_stack = [(node,)]
    else:
        process_stack = [(ch for ch in node.xml_children if isinstance(ch, tree.element))]
    while process_stack:
        curr_iter = process_stack.pop()
        for e in curr_iter:
            yield e
            process_stack.append(( ch for ch in e.xml_children if isinstance(ch, tree.element) ))
    return


def top_namespaces(doc):
    '''
    Return a namespace mapping for an entity node derived from its children

    It is not safe to pass this function anything besides an entity node
    '''
    elems = [ dict([(prefix, ns) for (prefix, ns) in e.xml_namespaces.iteritems()])
                                 for e in doc.xml_children if hasattr(e, 'xml_namespaces') ]
    elems.reverse()
    return reduce(lambda a, b: a.update(b) or a, elems, {})


def replace_namespace(node, oldns, newns):
    '''
    Checks the subtree at node for elements in oldns, and changes their xml_namespace to newns.
    If newprefix is provided, update the xml_qname as well.
    Update namespace declarations on node accordingly

    You should probably ensure the appropriate namespace declaration is ready first:
    node.xmlns_attributes[newprefix] = newns
    '''
    for elem in node.xml_select(u'.//*'):
        if elem.xml_namespace == oldns:
            elem.xml_namespace = newns
    return

