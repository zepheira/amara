########################################################################
# amara/xslt/tree/copy_of_element.py
"""
Implementation of `xsl:copy-of` element.
"""

from xml.dom import Node
from amara.namespaces import XMLNS_NAMESPACE, XSL_NAMESPACE, NAMESPACE_NODE
from amara.xpath import datatypes
from amara.xslt import XsltError
from amara.xslt.tree import xslt_element
from amara.xslt.reader import content_model, attribute_types

class copy_of_element(xsltelement):

    content_model = content_model.empty
    attribute_types = {
        'select': attribute_types.expression(required=True),
        }

    def instantiate(self, context):
        context.instruction = self
        context.namespaces = self.namespaces

        result = self._select.evaluate(context)
        if isinstance(result, Node):
            context.copy_node(result)
        elif isinstance(result, datatypes.nodeset):
            context.copy_nodes(result)
        else:
            context.text(datatypes.string(result))
        return
