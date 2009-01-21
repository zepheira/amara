########################################################################
# amara/xslt/exslt/functions.py
"""
EXSLT 2.0 - Functions (http://www.exslt.org/func/index.html)
"""
import itertools
from amara.namespaces import XSL_NAMESPACE
from amara.xpath import datatypes
from amara.xslt import XsltError, XsltRuntimeError
from amara.xslt.expressions import rtf_expression
from amara.xslt.tree import xslt_element, content_model, attribute_types
from amara.xslt.tree.variable_elements import param_element

EXSL_FUNCTIONS_NS = "http://exslt.org/functions"

class function_element(xslt_element):
    content_model = content_model.seq(
        content_model.rep(content_model.qname(XSL_NAMESPACE, 'xsl:param')),
        content_model.template,
        )
    attribute_types = {
        'name': attribute_types.qname_but_not_ncname(required=True),
        }

    def setup(self):
        params = self._params = []
        for child in self.children:
            if isinstance(child, param_element):
                params.append(child)
            elif isinstance(child, xslt_element):
                break
        if self._params:
            self._instructions = self.children[len(self._params)+1:-1]
        else:
            self._instructions = self.children
        return

    def prime(self, context):
        context.add_function(self._name, self)
        return

    def __call__(self, context, *args):
        # Save context state as XPath is side-effect free
        focus = context.node, context.position, context.size
        state = context.instruction, context.namespaces, context.variables

        context.instruction, context.namespaces = self, self.namespaces
        # Set the return value
        self.result = datatypes.EMPTY_STRING
        # Set the parameter list
        if self._params:
            context.variables = context.variables.copy()
            params = iter(self._params)
            # Handle the passed in arguments
            for arg, param in itertools.izip(args, params):
                context.variables[param._name] = arg.evaluate(context)
            # Handle remaining parameter defaults
            for param in params:
                param.instantiate(context)
        # Process the instruction template
        for child in self._instructions:
            child.instantiate(context)
        # Restore context state
        context.instruction, context.namespaces, context.variables = state
        context.node, context.position, context.size = focus
        return self.result


class result_element(xslt_element):
    """
    When an func:result element is instantiated, during the
    instantiation of a func:function element, the function returns
    with its value.
    """
    content_model = content_model.template
    attribute_types = {
        'select' : attribute_types.expression(),
        }

    _function = None

    def setup(self):
        if not self._select:
            self._select = rtf_expression(self)
        return

    def prime(self, context):
        current = self.parent
        while current:
            # this loop will stop when it hits the top of the tree
            if current.expanded_name == (EXSL_FUNCTIONS_NS, 'function'):
                self._function = current
                break
            current = current.parent

        if not self._function:
            raise XsltRuntimeError(XsltError.RESULT_NOT_IN_FUNCTION)

        if not self.isLastChild():
            siblings = iter(self.parent.children)
            for node in siblings:
                if node is self:
                    break
            for node in siblings:
                if node.expanded_name != (XSL_NAMESPACE, 'fallback'):
                    raise XsltRuntimeError(XsltError.ILLEGAL_RESULT_SIBLINGS)
        return

    def instantiate(self, context):
        context.instruction, context.namespaces = self, self.namespaces
        self._function.result = self._select.evaluate(context)
        return

## XSLT Extension Module Interface ####################################

extension_namespaces = {
    EXSL_FUNCTIONS_NS: 'func',
    }

extension_functions = {
    }

extension_elements = {
    (EXSL_FUNCTIONS_NS, 'function'): function_element,
    (EXSL_FUNCTIONS_NS, 'result'): result_element,
    }
