#######################################################################
# amara/xpath/functions/booleans.py
"""
The implementation of the core boolean functions from XPath 1.0.
"""

from amara import XML_NAMESPACE
from amara.xpath import datatypes
from amara.xpath.functions import builtin_function

__all__ = ('boolean_function', 'not_function', 'true_function',
           'false_function', 'lang_function')

class boolean_function(builtin_function):
    """Function: <boolean> boolean(<object>)"""
    name = 'boolean'
    arguments = (datatypes.xpathobject,)
    return_type = datatypes.boolean

    def evaluate_as_boolean(self, context):
        arg, = self._args
        return arg.evaluate_as_boolean(context)
    evaluate = evaluate_as_boolean


class not_function(builtin_function):
    """Function: <boolean> not(<boolean>)"""
    name = 'not'
    arguments = (datatypes.boolean,)
    return_type = datatypes.boolean

    def evaluate_as_boolean(self, context):
        arg, = self._args
        if arg.evaluate_as_boolean(context):
            return datatypes.FALSE
        return datatypes.TRUE
    evaluate = evaluate_as_boolean


class true_function(builtin_function):
    """Function: <boolean> true()"""
    name = 'true'
    arguments = ()
    return_type = datatypes.boolean

    def compile_as_boolean(self, compiler):
        compiler.emit('LOAD_CONST', datatypes.TRUE)
        return
    compile = compile_as_boolean

    def evaluate_as_boolean(self, context):
        return datatypes.TRUE
    evaluate = evaluate_as_boolean


class false_function(builtin_function):
    """Function: <boolean> false()"""
    name = 'false'
    arguments = ()
    return_type = datatypes.boolean

    def compile_as_boolean(self, compiler):
        compiler.emit('LOAD_CONST', datatypes.FALSE)
        return
    compile = compile_as_boolean

    def evaluate_as_boolean(self, context):
        return datatypes.FALSE
    evaluate = evaluate_as_boolean


class lang_function(builtin_function):
    """Function: <boolean> lang(<string>)"""
    name = 'lang'
    arguments = (datatypes.string,)
    return_type = datatypes.boolean

    def evaluate_as_boolean(self, context):
        arg, = self._args
        lang = arg.evaluate_as_string(context).lower()
        node = context.node
        while node.xml_parent:
            for attr in node.xml_attributes.nodes():
                # Search for xml:lang attribute
                if attr.xml_name == (XML_NAMESPACE, 'lang'):
                    value = attr.xml_value.lower()
                    # Exact match (PrimaryPart and possible SubPart)
                    if value == lang:
                        return datatypes.TRUE

                    # Just PrimaryPart (ignore '-' SubPart)
                    if '-' in value:
                        primary, sub = value.split('-', 1)
                        if lang == primary:
                            return datatypes.TRUE

                    # Language doesn't match
                    return datatypes.FALSE

            # Continue to next ancestor
            node = node.xml_parent

        # No xml:lang declarations found
        return datatypes.FALSE
    evaluate = evaluate_as_boolean
