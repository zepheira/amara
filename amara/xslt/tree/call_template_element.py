########################################################################
# amara/xslt/tree/call_template_element.py
"""
Implementation of `xsl:call-template` element
"""

from amara.namespaces import XSL_NAMESPACE
from amara.xslt import XsltError
from amara.xslt.tree import (xslt_element, content_model, attribute_types,
                             choose_elements, if_element)


class call_template_element(xslt_element):

    content_model = content_model.rep(
        content_model.qname(XSL_NAMESPACE, 'xsl:with-param')
        )
    attribute_types = {
        'name': attribute_types.qname(required=True),
        }

    _tail_recursive = False

    def setup(self):
        self._params = [ (child, child._name, child._select)
                         for child in self.children ]
        return

    def prime(self, context,
                 _test_elements=(if_element.if_element,),
                 _choose_elements=(choose_elements.when_element,
                                   choose_elements.otherwise_element,)):
        transform = self.root.stylesheet
        try:
            template = self._template = transform.named_templates[self._name]
        except KeyError:
            raise XsltError(XsltError.NAMED_TEMPLATE_NOT_FOUND,
                            self, self._name)
        # NOTE: Tail recursion is now checked for in the xsl:template setup().
        return

    def instantiate(self, context):
        # We need to calculate the parameters before the variable context
        # is changed back in the template element
        params = {}
        for param, name, select in self._params:
            context.instruction, context.namespaces = param, param.namespaces
            params[name] = select.evaluate(context)

        if self._tail_recursive:
            context.recursive_parameters = params
        else:
            #context.current_node = context.node
            self._template.instantiate(context, params)
        return

    #def __getstate__(self):
    #    del self._params
    #    return xslt_element.__getstate__(self)

    #def __setstate__(self, state):
    #    xslt_element.__setstate__(self, state)
    #    self._params = [ (child, child._name, child._select.evaluate)
    #                     for child in self.children ]
    #    return
