########################################################################
# amara/xslt/tree/apply_templates_element.py
"""
Implementation of `xsl:apply-templates` instruction
"""

from amara.namespaces import XSL_NAMESPACE
from amara.xslt import XsltError
from amara.xslt.tree import xslt_element
from amara.xslt.reader import content_model, attribute_types
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
            # only XSL children are guaranteed by the validation
            name = child.local_name
            if name == 'sort':
                sort_keys.append(child)
            else:
                assert name == 'with-param'
                params.append((child, child._name, child._select))

        if sort_keys:
            self._select = sorted_expression(self._select, sort_keys)
        return

    def instantiate(self, context):
        params = {}
        for param, name, select in self._params:
            context.instruction = param
            context.namespaces = param.namespaces
            params[name] = select.evaluate(context)

        if self._select:
            context.instruction = self
            context.namespaces = self.namespaces
            try:
              nodes = self._select.evaluate_as_nodeset(context)
            except TypeError:
                raise XsltError(XsltError.ILLEGAL_APPLYTEMPLATE_NODESET, self)
        else:
            nodes = context.node.childNodes

        # Process the selected nodes using `self._mode`
        context.transform.apply_templates(context, nodes, self._mode)
        return
