########################################################################
# amara/xslt/exslt/dynamic.py
"""
EXSLT Dynamic (http://exslt.org/dyn/dyn.html)
"""
from __future__ import absolute_import

import traceback

from amara import tree
from amara.xpath import XPathError, datatypes
from amara.xpath.parser import parse as parse_xpath

from .common import EXSL_COMMON_NS

EXSL_DYNAMIC_NS = "http://exslt.org/dynamic"


def closure_function(context, nodeset, string):
    """
    The dyn:closure function creates a node set resulting from transitive
    closure of evaluating the expression passed as the second argument on
    each of the nodes passed as the first argument, then on the node set
    resulting from that and so on until no more nodes are found.

    http://www.exslt.org/dyn/functions/closure/index.html
    """
    nodeset = nodeset.evaluate_as_nodeset(context)
    string = string.evaluate_as_string(context)
    try:
        expr = parse_xpath(string)
    except XPathError:
        lines = traceback.format_exception(*sys.exc_info())
        lines[:1] = [("Syntax error in XPath expression '%(expr)s', "
                      "lower-level traceback:\n") % {'expr': string}]
        context.processor.warning(''.join(lines))
        return datatypes.nodeset()
    result = datatypes.nodeset()
    while nodeset:
        nodeset = _map(context, nodeset, expr)
        result.extend(nodeset)
    return result


def evaluate_function(context, string):
    """
    The dyn:evaluate function evaluates a string as an XPath expression and
    returns the resulting value, which might be a boolean, number, string,
    node set, result tree fragment or external object. The sole argument is
    the string to be evaluated. If the string is an invalid XPath expression,
    an empty node-set is returned.

    http://www.exslt.org/dyn/functions/evaluate/index.html
    """
    string = string.evaluate_as_string(context)
    try:
        expr = parse_xpath(string)
    except XPathError:
        lines = traceback.format_exception(*sys.exc_info())
        lines[:1] = [("Syntax error in XPath expression '%(expr)s', "
                      "lower-level traceback:\n") % {'expr': string}]
        context.processor.warning(''.join(lines))
        return datatypes.nodeset()
    try:
        result = expr.evaluate(context)
    except:
        lines = traceback.format_exception(*sys.exc_info())
        lines[:1] = [("Runtime error in XPath expression '%(expr)s', "
                      "lower-level traceback:\n") % {'expr': string}]
        context.processor.warning(''.join(lines))
        return datatypes.nodeset()
    return result


def _map(context, nodeset, expr):
    focus = context.node, context.position, context.size
    context.size = len(nodeset)
    position = 1

    inputs = iter(nodeset)
    return_type = None
    result = set()
    for node in inputs:
        context.node = node
        context.position = position
        position += 1

        try:
            obj = expr.evaluate(context)
        except:
            lines = traceback.format_exception(*sys.exc_info())
            lines[:1] = [("Runtime error in XPath expression '%(expr)s', "
                            "lower-level traceback:\n") % {'expr': string}]
            context.processor.warning(''.join(lines))
        else:
            if not return_type:
                if isinstance(obj, datatypes.nodeset):
                    tag_name = None
                elif isinstance(obj, datatypes.number):
                    tag_name = 'exsl:number'
                    converter = datatypes.string
                elif isinstance(obj, datatypes.boolean):
                    tag_name = 'exsl:boolean'
                    converter = lambda obj: u'true' if obj else u''
                else:
                    tag_name = 'exsl:string'
                    converter = datatypes.string
                return_type = True
            if tag_name:
                E = tree.element(EXSL_COMMON_NS, tag_name)
                E.xml_append(tree.text(converter(obj)))
                result.add(E)
            else:
                result.update(obj)
    context.node, context.position, context.size = focus
    return datatypes.nodeset(result)

def map_function(context, nodeset, string):
    """
    The dyn:map function evaluates the expression passed as the second
    argument for each of the nodes passed as the first argument, and returns
    a node set of those values.

    http://www.exslt.org/dyn/functions/map/index.html
    """
    nodeset = nodeset.evaluate_as_nodeset(context)
    string = string.evaluate_as_string(context)
    try:
        expr = parse_xpath(string)
    except XPathError:
        lines = traceback.format_exception(*sys.exc_info())
        lines[:1] = [("Syntax error in XPath expression '%(expr)s', "
                      "lower-level traceback:\n") % {'expr': string}]
        context.processor.warning(''.join(lines))
        return datatypes.nodeset()
    return _map(context, nodeset, expr)


def max_function(context, nodeset, string):
    """
    The dyn:max function calculates the maximum value for the nodes passed as
    the first argument, where the value of each node is calculated dynamically
    using an XPath expression passed as a string as the second argument.

    http://www.exslt.org/dyn/functions/max/index.html
    """
    nodeset = nodeset.evaluate_as_nodeset(context)
    string = string.evaluate_as_string(context)
    try:
        expr = parse_xpath(string)
    except XPathError:
        lines = traceback.format_exception(*sys.exc_info())
        lines[:1] = [("Syntax error in XPath expression '%(expr)s', "
                      "lower-level traceback:\n") % {'expr': string}]
        context.processor.warning(''.join(lines))
        return datatypes.nodeset()
    return max(map(datatypes.number, _map(context, nodeset, expr)))


def min_function(context, nodeset, string):
    """
    The dyn:min function calculates the minimum value for the nodes passed as
    the first argument, where the value of each node is calculated dynamically
    using an XPath expression passed as a string as the second argument.

    http://www.exslt.org/dyn/functions/min/index.html
    """
    nodeset = nodeset.evaluate_as_nodeset(context)
    string = string.evaluate_as_string(context)
    try:
        expr = parse_xpath(string)
    except XPathError:
        lines = traceback.format_exception(*sys.exc_info())
        lines[:1] = [("Syntax error in XPath expression '%(expr)s', "
                      "lower-level traceback:\n") % {'expr': string}]
        context.processor.warning(''.join(lines))
        return datatypes.nodeset()
    return min(map(datatypes.number, _map(context, nodeset, expr)))


def sum_function(context, nodeset, string):
    """
    The dyn:sum function calculates the sum for the nodes passed as the first
    argument, where the value of each node is calculated dynamically using an
    XPath expression passed as a string as the second argument.

    http://www.exslt.org/dyn/functions/sum/index.html
    """
    nodeset = nodeset.evaluate_as_nodeset(context)
    string = string.evaluate_as_string(context)
    try:
        expr = parse_xpath(string)
    except XPathError:
        lines = traceback.format_exception(*sys.exc_info())
        lines[:1] = [("Syntax error in XPath expression '%(expr)s', "
                      "lower-level traceback:\n") % {'expr': string}]
        context.processor.warning(''.join(lines))
        return datatypes.nodeset()
    return sum(map(datatypes.number, _map(context, nodeset, expr)))


## XSLT Extension Module Interface ####################################

extension_namespaces = {
    EXSL_DYNAMIC_NS : 'dyn',
    }

extension_functions = {
    (EXSL_DYNAMIC_NS, 'closure') : closure_function,
    (EXSL_DYNAMIC_NS, 'evaluate') : evaluate_function,
    (EXSL_DYNAMIC_NS, 'map') : map_function,
    (EXSL_DYNAMIC_NS, 'max') : max_function,
    (EXSL_DYNAMIC_NS, 'min') : min_function,
    (EXSL_DYNAMIC_NS, 'sum') : sum_function,
    }

extension_elements = {
    }

