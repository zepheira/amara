########################################################################
# amara/xpath/functions/nodesets.py
"""
The implementation of the core node-set functions from XPath 1.0.
"""
from amara import tree
from amara.xpath import datatypes
from amara.xpath.functions import builtin_function
from amara.xpath.locationpaths import relative_location_path

__all__ = ('last_function', 'position_function', 'count_function',
           'id_function', 'local_name_function', 'namespace_uri_function',
           'name_function')

class last_function(builtin_function):
    """Function: <number> last()"""
    name = 'last'
    arguments = ()
    return_type = datatypes.number

    def evaluate_as_number(self, context):
        return datatypes.number(context.size)
    evaluate = evaluate_as_number


class position_function(builtin_function):
    """Function: <number> position()"""
    name = 'position'
    arguments = ()
    return_type = datatypes.number

    def evaluate_as_number(self, context):
        return datatypes.number(context.position)
    evaluate = evaluate_as_number


class count_function(builtin_function):
    """Function: <number> count(<node-set>)"""
    name = 'count'
    arguments = (datatypes.nodeset,)
    return_type = datatypes.number

    def evaluate_as_number(self, context):
        arg0, = self._args
        arg0 = arg0.evaluate_as_nodeset(context)
        return datatypes.number(len(arg0))
    evaluate = evaluate_as_number


class id_function(builtin_function):
    """Function: <node-set> id(<object>)"""
    name = 'id'
    arguments = (datatypes.xpathobject,)
    return_type = datatypes.nodeset

    def evaluate_as_nodeset(self, context):
        arg0, = self._args
        arg0 = arg0.evaluate(context)
        if isinstance(arg0, datatypes.nodeset):
            ids = set(datatypes.string(x) for x in arg0)
        else:
            arg0 = datatypes.string(arg0)
            ids = set(arg0.split())

        doc = context.node.xml_root
        nodeset = filter(None, (doc.xml_lookup(id) for id in ids))
        nodeset.sort()
        return datatypes.nodeset(nodeset)
    evaluate = evaluate_as_nodeset


class name_function(builtin_function):
    """Function: <string> name(<node-set>?)"""
    name = 'name'
    arguments = (datatypes.nodeset,)
    defaults = (None,)
    return_type = datatypes.string

    def __init__(self, name, args):
        # `name(.)` is the same as `name()`
        if args:
            try:
                arg, = args
            except ValueError:
                # This will become an error anyhow.
                pass
            else:
                if isinstance(arg, relative_location_path):
                    if len(arg._steps) == 1:
                        step, = arg._steps
                        if (step.axis.name == 'self' and
                            step.node_test.name == 'node' and
                            not step.predicates):
                            args = ()
        builtin_function.__init__(self, name, args)

    def evaluate_as_string(self, context):
        arg0, = self._args
        if arg0 is None:
            node = context.node
        else:
            arg0 = arg0.evaluate_as_nodeset(context)
            if not arg0:
                return datatypes.EMPTY_STRING
            node = arg0[0]

        if isinstance(node, (tree.element, tree.attribute)):
            return datatypes.string(node.xml_qname)
        elif isinstance(node, tree.processing_instruction):
            return datatypes.string(node.xml_target)
        elif isinstance(node, tree.namespace):
            return datatypes.string(node.xml_name)
        return datatypes.EMPTY_STRING
    evaluate = evaluate_as_string


class local_name_function(name_function):
    """Function: <string> local-name(<node-set>?)"""
    name = 'local-name'
    arguments = (datatypes.nodeset,)
    defaults = (None,)
    return_type = datatypes.string

    def evaluate_as_string(self, context):
        arg0, = self._args
        if arg0 is None:
            node = context.node
        else:
            arg0 = arg0.evaluate_as_nodeset(context)
            if not arg0:
                return datatypes.EMPTY_STRING
            node = arg0[0]

        if isinstance(node, (tree.element, tree.attribute)):
            return datatypes.string(node.xml_local)
        elif isinstance(node, tree.processing_instruction):
            return datatypes.string(node.xml_target)
        elif isinstance(node, tree.namespace):
            return datatypes.string(node.xml_name)
        return datatypes.EMPTY_STRING
    evaluate = evaluate_as_string


class namespace_uri_function(name_function):
    """Function: <string> namespace-uri(<node-set>?)"""
    name = 'namespace-uri'
    arguments = (datatypes.nodeset,)
    defaults = (None,)
    return_type = datatypes.string

    def evaluate_as_string(self, context):
        arg0, = self._args
        if arg0 is None:
            node = context.node
        else:
            arg0 = arg0.evaluate_as_nodeset(context)
            if not arg0:
                return datatypes.EMPTY_STRING
            node = arg0[0]

        try:
            namespace_uri = node.xml_namespace
        except AttributeError:
            # not a named node
            return datatypes.EMPTY_STRING
        # namespaceURI could be None
        if namespace_uri:
            return datatypes.string(namespace_uri)
        return datatypes.EMPTY_STRING
    evaluate = evaluate_as_string

