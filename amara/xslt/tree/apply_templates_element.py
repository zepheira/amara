########################################################################
# amara/xslt/tree/apply_templates_element.py
"""
Implementation of `xsl:apply-templates` instruction
"""

from amara.namespaces import XSL_NAMESPACE
from amara.xpath import XPathError
from amara.xslt import XsltError, XsltStaticError
from amara.xslt.tree import xslt_element, content_model, attribute_types
from amara.xslt.tree.sort_element import sort_element
from amara.xslt.tree.with_param_element import with_param_element
from amara.xslt.expressions import sorted_expression

class apply_templates_element(xslt_element):

    content_model = content_model.rep(
        content_model.alt(content_model.qname(XSL_NAMESPACE, 'xsl:sort'),
                          content_model.qname(XSL_NAMESPACE, 'xsl:with-param'))
        )
    attribute_types = {
        'select': attribute_types.expression(),
        'mode': attribute_types.qname(),
        }

    def setup(self):
        sort_keys = []
        self._params = params = []
        for child in self.children:
            if isinstance(child, sort_element):
                sort_keys.append(child)
            elif isinstance(child, with_param_element):
                params.append((child, child._name, child._select))
        if sort_keys:
            self._select = sorted_expression(self._select, sort_keys)
        return

    def instantiate(self, context):
        params = {}
        for param, name, select in self._params:
            context.instruction, context.namespaces = param, param.namespaces
            params[name] = select.evaluate(context)

        if self._select:
            context.instruction, context.namespaces = self, self.namespaces
            try:
              nodes = self._select.evaluate_as_nodeset(context)
            except TypeError:
                raise
                raise XsltStaticError(XsltError.INVALID_APPLY_TEMPLATES_SELECT,
                                      self)
        else:
            nodes = context.node.xml_children

        # Process the selected nodes using `self._mode`
        context.transform.apply_templates(context, nodes, self._mode, params)
        return
