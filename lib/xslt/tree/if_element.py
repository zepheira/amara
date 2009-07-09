########################################################################
# amara/xslt/tree/if_element.py
"""
Implementation of the `xsl:if` element.
"""

from amara.namespaces import XSL_NAMESPACE
from amara.xslt.tree import xslt_element, content_model, attribute_types

__all__ = ('if_element',)

class if_element(xslt_element):
    content_model = content_model.template
    attribute_types = {
        'test': attribute_types.boolean_expression(required=True),
        }

    def instantiate(self, context):
        context.instruction = self
        context.namespaces = self.namespaces
        if self._test.evaluate_as_boolean(context):
            self.process_children(context)
        return
