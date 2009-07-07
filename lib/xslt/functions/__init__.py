#######################################################################
# amara/xslt/functions/__init__.py
"""
XSLT expression nodes that evaluate function calls.
"""

from cStringIO import StringIO

import amara
from amara.lib import iri
from amara.lib.xmlstring import isqname
from amara.namespaces import XSL_NAMESPACE, EXTENSION_NAMESPACE
from amara.xpath import datatypes
from amara.xpath.functions import builtin_function

import _functions

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
        if arg1 is None:
            base_uri = context.instruction.baseUri
        else:
            for node in arg1.evaluate_as_nodeset(context):
                base_uri = node.xml_base
                break
            else:
                raise XsltRuntimeError(XsltError.DOC_FUNC_EMPTY_NODESET,
                                       context.instruction)
        arg0 = arg0.evaluate(context)
        if isinstance(arg0, datatypes.nodeset):
            uris = set()
            for node in arg0:
                uri = datatypes.string(node)
                if arg1 is None:
                    base_uri = node.xml_base
                assert base_uri or iri.is_absolute(uri)
                uris.add(iri.DEFAULT_RESOLVER.normalize(uri, base_uri))
        else:
            uri = datatypes.string(arg0)
            assert base_uri or iri.is_absolute(uri)
            uris = [iri.DEFAULT_RESOLVER.normalize(uri, base_uri)]

        documents = context.documents
        sources = context.transform.root.sources
        result = []
        for uri in uris:
            if uri in documents:
                doc = documents[uri]
            else:
                if uri in sources:
                    doc = amara.parse(StringIO(sources[uri]), uri)
                else:
                    doc = amara.parse(uri)
                documents[uri] = doc
            result.append(doc)
        return datatypes.nodeset(result)
    evaluate = evaluate_as_nodeset


class key_function(builtin_function):
    """Function: <nodeset> key(string, object)"""
    name = 'key'
    arguments = (datatypes.string, datatypes.xpathobject)
    return_type = datatypes.nodeset

    def evaluate_as_nodeset(self, context):
        arg0, arg1 = self._args
        # Get the key table
        key_name = arg0.evaluate_as_string(context)
        if not isqname(key_name):
            raise XsltRuntimeError(XsltError.INVALID_QNAME_ARGUMENT,
                                   context.instruction, value=key_name)
        key_name = context.expand_qname(key_name)
        try:
            key_documents = context.keys[key_name]
        except KeyError:
            # Unknown key name
            return datatypes.nodeset()
        else:
            key_values = key_documents[context.node.xml_root]
        # Get the lookup value
        value = arg1.evaluate(context)
        if isinstance(value, datatypes.nodeset):
            result = []
            for value in value:
                value = datatypes.string(value)
                if value in key_values:
                    result.extend(key_values[value])
        else:
            value = datatypes.string(value)
            if value in key_values:
                result = key_values[value]
            else:
                result = ()
        return datatypes.nodeset(result)
    evaluate = evaluate_as_nodeset


class format_number_function(builtin_function):
    """Function: <string> format-number(number, string, string?)"""
    name = 'format-number'
    arguments = (datatypes.number, datatypes.string, datatypes.string)
    defaults = (None,)
    return_type = datatypes.string

    def evaluate_as_string(self, context):
        arg0, arg1, arg2 = self._args
        number = arg0.evaluate_as_number(context)
        pattern = arg1.evaluate_as_string(context)
        if arg2:
            qname = arg2.evaluate_as_string(context)
            name = context.expand_qname(qname)
            try:
                format = context.transform.decimal_formats[name]
            except KeyError:
                raise XsltRuntimeError(XsltError.UNDEFINED_DECIMAL_FORMAT,
                                       self, name=qname)
        else:
            format = None
        result = _functions.decimal_format(number, pattern, format)
        return datatypes.string(result)


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
        name = arg0.evaluate_as_string(context)
        try:
            uri = context.node.xml_root.xml_unparsed_entities[name]
        except KeyError:
            return datatypes.EMPTY_STRING
        return datatypes.string(uri)


class generate_id_function(builtin_function):
    """Function: <string> generate-id(nodeset?)"""
    name = 'generate-id'
    arguments = (datatypes.nodeset,)
    defaults = (None,)
    return_type = datatypes.string

    def evaluate_as_string(self, context):
        arg0, = self._args
        if arg0 is None:
            return datatypes.string(context.node.xml_nodeid)
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
