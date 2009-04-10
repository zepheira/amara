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


def first_item(seq, next=None):
    if next is None:
        return chain(seq or (), (None,)).next()
    else:
        return next(chain(seq or (), (None,)).next())


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


def coroutine(func):
    '''
    A simple tool to eliminate the need to call next() to kick-start a co-routine
    From David Beazley: http://www.dabeaz.com/generators/index.html
    '''
    def start(*args,**kwargs):
        coro = func(*args,**kwargs)
        coro.next()
        return coro
    return start

#Grabbed from unittest.py

def fail(msg=None):
    """Fail immediately, with the given message."""
    raise AssertionError(msg)


def fail_if(expr, msg=None):
    "Fail the test if the expression is true."
    if expr: raise AssertionError(msg)


def fail_unless(expr, msg=None):
    """Fail the test unless the expression is true."""
    if not expr: raise AssertionError(msg)


def fail_unless_equal(first, second, msg=None):
    """Fail if the two objects are unequal as determined by the '=='
       operator.
    """
    if not first == second:
        raise AssertionError(msg or '%r != %r' % (first, second))


def fail_if_equal(first, second, msg=None):
    """Fail if the two objects are equal as determined by the '=='
       operator.
    """
    if first == second:
        raise AssertionError(msg or '%r == %r' % (first, second))


def fail_unless_almost_equal(first, second, places=7, msg=None):
    """Fail if the two objects are unequal as determined by their
       difference rounded to the given number of decimal places
       (default 7) and comparing to zero.

       Note that decimal places (from zero) are usually not the same
       as significant digits (measured from the most signficant digit).
    """
    if round(second-first, places) != 0:
        raise AssertionError(msg or '%r != %r within %r places' % (first, second, places))


def fail_if_almost_equal(first, second, places=7, msg=None):
    """Fail if the two objects are equal as determined by their
       difference rounded to the given number of decimal places
       (default 7) and comparing to zero.

       Note that decimal places (from zero) are usually not the same
       as significant digits (measured from the most signficant digit).
    """
    if round(second-first, places) == 0:
        raise AssertionError(msg or '%r == %r within %r places' % (first, second, places))

# Synonyms for assertion methods

assert_equal = fail_unless_equal

assert_not_equal = fail_if_equal

assert_almost_equal = fail_unless_almost_equal

assert_not_almostEqual = fail_if_almost_equal

assert_ = fail_unless

assert_false = fail_if


