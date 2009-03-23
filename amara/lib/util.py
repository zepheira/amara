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


def first_item(seq): return chain(seq or (), (None,)).next()

identity = lambda x: x

def omit_blanks():
    return "..."

def make_date():
    return "..."


#See: http://docs.python.org/dev/howto/functional.html
#from functional import *
#Will work as of 2.7
#mcompose = partial(reduce, compose)

def mcompose(*funcs):
    def f(val):
        result = val
        for func in funcs:
            result = pipeline_stage(func, result)
        return result
    return f
#    return result
#        result = tuple(pipeline_stage(func, result))
#    for item in result:
#        yield item


def pipeline_stage(obj, arg):
    if callable(obj):
        fresult = obj(arg)
    else:
        fresult = arg
#        try:
#            it = (fresult,)
#            if not isinstance(fresult, basestring): it = iter(fresult)
#        except TypeError:
#            pass
#    else:
#        it = (arg,)
#    return iter(it)
    return fresult


from copy import *
def trim_word_count(node, maxcount):
    '''
    import amara
    from amara.lib.util import trim_word_count
    x = amara.parse('<a>one two <b>three four </b><c>five <d>six seven</d> eight</c> nine</a>')
    amara.xml_print(trim_word_count(x, 1))
    amara.xml_print(trim_word_count(x, 2))
    amara.xml_print(trim_word_count(x, 3))
    amara.xml_print(trim_word_count(x, 5))
    amara.xml_print(trim_word_count(x, 6))
    amara.xml_print(trim_word_count(x, 7))
    amara.xml_print(trim_word_count(x, 8))
    amara.xml_print(trim_word_count(x, 9))
    amara.xml_print(trim_word_count(x, 10))
    '''
    import amara
    def trim(node, count):
        newnode = copy(node)
        for child in node.xml_children:
            if count >= maxcount:
                continue
            addendum = len(child.xml_select(u'string(.)').split())
            if count + addendum > maxcount:
                if isinstance(child, amara.tree.text):
                    newnode.xml_append(amara.tree.text(child.xml_value.rsplit(None, maxcount-count)[0]))
                else:
                    newnode.xml_append(trim(child, count))
                count = maxcount
            else:
                newnode.xml_append(deepcopy(child))
                count += addendum
        return newnode
    return trim(node, 0)

