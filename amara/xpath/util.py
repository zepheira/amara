########################################################################
# amara/xpath/util.py
"""
General utilities for XPath applications
"""

import os
import cStringIO
import traceback

from amara import domlette
from amara._domlette import GetAllNs as getallns
from amara.xpath import XPathError, datatypes
from amara.xpath.parser import xpathparser

# NOTE: XPathParser and Context are imported last to avoid import errors

__all__ = [# XPath expression processing:
           'Compile', 'Evaluate', 'SimpleEvaluate', 'paramvalue', 'parameterize'
           ]


# -- Core XPath API ---------------------------------------------------------


def SimpleEvaluate(expr, node, explicitNss=None):
    """
    Designed to be the most simple/brain-dead interface to using XPath
    Usually invoked through Node objects using:
      node.xpath(expr[, explicitNss])

    expr - XPath expression in string or compiled form
    node - the node to be used as core of the context for evaluating the XPath
    explicitNss - (optional) any additional or overriding namespace mappings
                  in the form of a dictionary of prefix: namespace
                  the base namespace mappings are taken from in-scope
                  declarations on the given node.  This explicit dictionary
                  is superimposed on the base mappings
    """
    if 'EXTMODULES' in os.environ:
        ext_modules = os.environ["EXTMODULES"].split(':')
    else:
        ext_modules = []
    explicitNss = explicitNss or {}

    nss = dict((ns.nodeValue or None, ns.nodeName) 
               for ns in node.xml_namespaces)
    nss.update(explicitNss)
    context = Context.Context(node, 0, 0, processorNss=nss,
                              extModuleList=ext_modules)

    if hasattr(expr, "evaluate"):
        retval = expr.evaluate(context)
    else:
        retval = XPathParser.Parse(expr).evaluate(context)
    return retval


def Evaluate(expr, contextNode=None, context=None):
    """
    Evaluates the given XPath expression.

    Two arguments are required: the expression (as a string or compiled
    expression object), and a context. The context can be given as a
    Domlette node via the 'contextNode' named argument, or can be given as
    an Ft.Xml.XPath.Context.Context object via the 'context' named
    argument.

    If namespace bindings or variable bindings are needed, use a
    Context object. If extension functions are needed, either use a
    Context object, or set the EXTMODULES environment variable to be a
    ':'-separated list of names of Python modules that implement
    extension functions.

    The return value will be one of the following:
    node-set: list of Domlette node objects (xml.dom.Node based);
    string: Unicode string type;
    number: float type;
    boolean: Ft.Lib.boolean C extension object;
    or a non-XPath object (i.e. as returned by an extension function).
    """
    if 'EXTMODULES' in os.environ:
        ext_modules = os.environ["EXTMODULES"].split(':')
    else:
        ext_modules = []

    if contextNode and context:
        con = context.clone()
        con.node = contextNode
    elif context:
        con = context
    elif contextNode:
        #contextNode should be a node, not a context obj,
        #but this is a common error.  Be forgiving?
        if isinstance(contextNode, Context.Context):
            con = contextNode
        else:
            con = Context.Context(contextNode, 0, 0, extModuleList=ext_modules)
    else:
        raise XPathException(XPathException.NO_CONTEXT)

    if hasattr(expr, "evaluate"):
        retval = expr.evaluate(con)
    else:
        retval = XPathParser.Parse(expr).evaluate(con)
    return retval


def Compile(expr):
    """
    Given an XPath expression as a string, returns an object that allows
    an evaluation engine to operate on the expression efficiently.
    This "compiled" expression object can be passed to the Evaluate
    function instead of a string, in order to shorten the amount of time
    needed to evaluate the expression.
    """
    try:
        return XPathParser.Parse(expr)
    except XPathException:
        raise
    except:
        stream = cStringIO.StringIO()
        traceback.print_exc(None, stream)
        raise XPathException(XPathException.INTERNAL, stream.getvalue())


def paramvalue(obj):
    """
    Try to convert a Python object into an XPath data model value
    
    returns the value if successful, else None
    """
    if isinstance(obj, datatypes.xpathobject):
        return obj
    if isinstance(obj, unicode):
        return datatypes.string(obj)
    elif isinstance(obj, str):
        try:
            obj = obj.decode('utf-8')
        except UnicodeError:
            return None
        else:
            return datatypes.string(obj)
    elif isinstance(obj, bool): # <bool> is subclasses of <int>, test first
        return datatypes.TRUE if obj else datatypes.FALSE
    elif isinstance(obj, (int, long, float)):
        return datatypes.number(obj)
    elif isinstance(obj, domlette.Node):
        return obj
    #NOTE: At one time (WSGI.xml days) this attemped to be smart and handle all iterables
    #But this would mean blindly dealing with dangerous creatures, such as sockets
    #So now it's more conservative and sticks to list & tuple
    elif isinstance(obj, (list, tuple)):
        # We can only use the list if all the items are Nodes.
        for item in obj:
            if not isinstance(item, domlette.Node):
                return None
        return datatypes.nodeset(obj)
    else:
        return None


def parameterize(inputdict, defaultns=None):
    """
    Convert a dictionary of name to object mappings into a dict of parameters suitable for
    passing into XPath context, or an XSLT transform
    
    inputdict - input mapping of name (string or tuple) to values
    
    defaultns - the namespace to use for parameter names given as string/unicode rather than tuple
    
    return the resulting param dict if successful.  If inputdict cannot completely be converted, return None
    """
    resultdict = {}
    for key in inputdict:
        value = paramvalue(inputdict[key])
        if value is None: return None
        if isinstance(key, basestring):
            if isinstance(key, str): key = key.decode('utf-8')
            if defaultns:
                resultdict[(defaultns, key)] = value
            else:
                resultdict[key] = value
        elif isinstance(key, list) or isinstance(key, tuple):
            resultdict[key] = value
        else:
            return None

    return resultdict

