#######################################################################
# amara/xslt/functions/__init__.py
"""
XSLT expression nodes that evaluate function calls.
"""

from amara.namespaces import XSL_NAMESPACE, EXTENSION_NAMESPACE
from amara.xpath import datatypes
from amara.xpath.functions import builtin_function

__all__ = ('document_function', 'key_function', 'format_number_function',
           'current_function', 'unparsed_entity_uri_function',
           'generate_id_function', 'system_property_function',
           'element_available_function', 'function_available_function',
           )

class document_function(builtin_function):
    """Function: <nodeset> document(object, nodeset?)"""
    name = 'document'
    arguments = (datatypes.xpathobject, datatypes.nodeset)
    defaults = (None,)
    return_type = datatypes.nodeset

    def evaluate_as_nodeset(self, context):
        arg0, arg1 = self._args
        return datatypes.nodeset()
    evaluate = evaluate_as_nodeset


class key_function(builtin_function):
    """Function: <nodeset> key(string, object)"""
    name = 'key'
    arguments = (datatypes.string, datatypes.xpathobject)
    return_type = datatypes.nodeset

    def evaluate_as_nodeset(self, context):
        arg0, arg1 = self._args
        return datatypes.nodeset()
    evaluate = evaluate_as_nodeset


class format_number_function(builtin_function):
    """Function: <string> format-number(number, string, string?)"""
    name = 'format-number'
    arguments = (datatypes.number, datatypes.string, datatypes.string)
    defaults = (None,)
    return_type = datatypes.string

    def evaluate_as_string(self, context):
        arg0, arg1, arg2 = self._args
        return datatypes.string()


class current_function(builtin_function):
    """Function: <nodeset> current()"""
    name = 'current'
    arguments = ()
    return_type = datatypes.nodeset

    def evaluate_as_nodeset(self, context):
        return datatypes.nodeset((context.current_node,))
    evaluate = evaluate_as_nodeset


class unparsed_entity_uri_function(builtin_function):
    """Function: <string> unparsed-entity-uri(string)"""
    name = 'unparsed-entity-uri'
    arguments = (datatypes.string,)
    return_type = datatypes.string

    def evaluate_as_string(self, context):
        arg0, = self._args
        return datatypes.string()


class generate_id_function(builtin_function):
    """Function: <string> generate-id(nodeset?)"""
    name = 'generate-id'
    arguments = (datatypes.nodeset,)
    return_type = datatypes.string

    def evaluate_as_string(self, context):
        arg0, = self._args
        for node in arg0.evaluate_as_nodeset(context):
            return datatypes.string(node.xml_nodeid)
        return datatypes.EMPTY_STRING
    evaluate = evaluate_as_string


class system_property_function(builtin_function):
    """Function: <object> system-property(string)"""
    name = 'system-property'
    arguments = (datatypes.string,)
    return_type = datatypes.xpathobject

    def evaluate(self, context):
        arg0, = self._args
        arg0 = arg0.evaluate_as_string(context)
        namespace, property = context.expand_qname(arg0)
        if namespace == XSL_NAMESPACE:
            if property == 'version':
                return datatypes.number(1)
            elif property == 'vender':
                return datatypes.string('Amara')
            elif property == 'vender-url':
                return datatypes.string('http://hg.4suite.org/amara')
        elif namespace == EXTENSION_NAMESPACE:
            if property == 'version':
                return datatypes.string(__version__)
            elif property == 'platform':
                return datatypes.string(sys.platform)
            elif property == 'tempdir':
                raise
        elif namespace == 'http://xmlns.4suite.org/xslt/env-system-property':
            raise
        return datatypes.EMPTY_STRING


class element_available_function(builtin_function):
    """Function: <boolean> element-available(string)"""
    name = 'element-available'
    arguments = (datatypes.string,)
    return_type = datatypes.boolean

    def evaluate_as_boolean(self, context):
        arg0, = self._args
        qname = arg0.evaluate_as_string(context)
        name = namespace, local = context.expand_qname(qname)
        if namespace is None:
            return datatypes.FALSE
        if namespace == XSL_NAMESPACE:
            from amara.xslt.reader import ELEMENT_CLASSES
            available = local in ELEMENT_CLASSES
        else:
            available = name in context.transform.extension_elements
        return datatypes.TRUE if available else datatypes.FALSE
    evaluate = evaluate_as_boolean


class function_available_function(builtin_function):
    """Function: <boolean> function-available(string)"""
    name = 'function-available'
    arguments = (datatypes.string,)
    return_type = datatypes.boolean

    def evaluate_as_boolean(self, context):
        arg0, = self._args
        qname = arg0.evaluate_as_string(context)
        name = context.expand_qname(qname)
        return datatypes.TRUE if name in context.functions else datatypes.FALSE
    evaluate = evaluate_as_boolean
