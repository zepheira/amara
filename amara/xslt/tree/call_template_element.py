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
        self._params = [ (child, child._name, child._select.evaluate)
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
        self._tail_recursive = template._tail_recursive
        return
        # Check for tail-recursion
        node = self.parent
        while node is not transform:
            if node is template:
                # The xsl:call-template is contained within the named template.
                node, parent = self, self.parent
                while parent is not template:
                    last = parent.last_instruction
                    if node is last:
                        if isinstance(parent, _test_elements):
                            node, parent = parent, parent.parent
                        elif isinstance(parent, _choose_elements):
                            # skip straight to the xsl:choose element
                            parent = parent.parent
                            node, parent = parent, parent.parent
                        else:
                            # Encountered an ancestor which *may* perform
                            # add'l processing after instantiating its children
                            # so this cannot be considered tail recursive.
                            break
                else:
                    self._tail_recursive = True
                break
            else:
                # Continue checking the ancestors until the xsl:stylesheet
                # element is reached.
                node = node.parent
        return

    def instantiate(self, context):
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
