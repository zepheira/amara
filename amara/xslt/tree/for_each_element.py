########################################################################
# amara/xslt/tree/for_each_element.py
"""
Implementation of `xsl:for-each` element.
"""

from amara.namespaces import XSL_NAMESPACE
from amara.xslt import XsltError
from amara.xslt.tree import xslt_element, content_model, attribute_types
from amara.xslt.expressions import sorted_expression

from sort_element import sort_element

class for_each_element(xslt_element):

    content_model = content_model.seq(
        content_model.rep(content_model.qname(XSL_NAMESPACE, 'xsl:sort')),
        content_model.template,
        )
    attribute_types = {
        'select': attribute_types.nodeset_expression(required=True),
        }

    def setup(self):
        children = self.children
        nkeys = 0
        for child in children:
            if isinstance(child, sort_element):
                nkeys += 1
            else:
                break
        if nkeys:
            self._select = sorted_expression(self._select, children[:nkeys])
        return

    def instantiate(self, context):
        if self._select:
            context.instruction = self
            context.namespaces = self.namespaces
            try:
              nodes = self._select.evaluate_as_nodeset(context)
            except TypeError:
                raise
                raise XsltError(XsltError.INVALID_FOREACH_NODESET)
        else:
            nodes = context.node.xml_children

        # Save the current context state
        state = context.node, context.position, context.size, context.template
        # Now process the selected nodes
        context.template = None
        size = context.size = len(nodes)
        position = 1
        for node in nodes:
            context.node = context.current_node = node
            context.position = position
            self.process_children(context)
            position += 1

        context.node, context.position, context.size, context.template = state
        return
