########################################################################
# amara/xslt/tree/call_template_element.py
"""
Implementation of `xsl:call-template` element
"""

from amara.namespaces import XSL_NAMESPACE
from amara.xslt import XsltError
from amara.xslt.tree import \
    xslt_element, choose_element, when_element, otherwise_element, if_element
from amara.xslt.reader import content_model, attribute_types

_conditional_elements = (
    choose_element, when_element, otherwise_element, if_element)


class call_template_element(xslt_element):

    content_model = content_model.rep(
        content_model.qname(XSL_NAMESPACE, 'xsl:with-param')
        )
    attribute_types = {
        'name': attribute_types.qname(required=True),
        }

    def setup(self):
        self._tail_recursive = 0
        self._called_template = None
        self._params = [ (child, child._name, child._select.evaluate)
                         for child in self.children ]
        return

    def prime(self, context):
        transform = context.transform
        try:
            self._called_template = transform.named_templates[self._name]
        except KeyError:
            return
        # check for tail recursion
        current = self.parent
        while current is not transform:
            if current is self._called_template:
                # we are within the template that we call
                if self.isLastChild():
                    use_tail = 1
                    node = self.parent
                    while node is not current:
                        if not (node.isLastChild() and
                                isinstance(node, _conditional_elements)):
                            use_tail = 0
                            break
                        node = node.parent
                    self._tail_recursive = use_tail
                break
            current = current.parent
        return

    def instantiate(self, context):
        # setup parameters for called template

        # This handles the case of top-level variables using call-templates
        if not self._called_template:
            self.prime(context)
            if not self._called_template:
                raise XsltRuntimeException(XsltError.NAMED_TEMPLATE_NOT_FOUND,
                                           self, self._name)
            self._called_template.prime(context)

        # We need to calculate the parameters before the variable context
        # is changed back in the template element
        params = {}
        for param, name, evaluate in self._params:
            context.instruction = param
            context.namespaces = param.namespaces
            params[name] = evaluate(context)

        if self._tail_recursive:
            context.recursive_parameters = params
        else:
            context.current_node = context.node
            self._called_template.instantiate(context, params)
        return

    #def __getstate__(self):
    #    del self._params
    #    return xslt_element.__getstate__(self)

    #def __setstate__(self, state):
    #    xslt_element.__setstate__(self, state)
    #    self._params = [ (child, child._name, child._select.evaluate)
    #                     for child in self.children ]
    #    return
