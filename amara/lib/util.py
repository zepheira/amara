########################################################################
# amara/lib/util.py

"""
Some utilities for Amara overall
"""

from amara import tree
from itertools import *

def element_subtree_iter(node, include_root=False):
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

