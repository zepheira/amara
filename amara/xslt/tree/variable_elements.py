########################################################################
# amara/xslt/elements/variable_elements.py
"""
Implementation of XSLT variable assigning elements
"""

from amara.xslt import XsltError
from amara.xslt.tree import xslt_element, content_model, attribute_types

__all__ = ['variable_element', 'param_element']

class variable_element(xslt_element):
    """
    Implementation of the `xsl:variable` element.
    """
    content_model = content_model.template
    attribute_types = {
        'name': attribute_types.qname(required=True),
        'select': attribute_types.expression(),
        }

    def setup(self):
        # check for a bad binding
        if self._select and self.children:
            raise XsltError(XsltError.VAR_WITH_CONTENT_AND_SELECT, name=self._name)
        return

    def instantiate(self, context):
        # NOTE: all we want to do is change the varBindings
        if self._select:
            context.instruction = self
            context.namespaces = self.namespaces
            result = self._select.evaluate(context)
        elif self.children:
            context.push_tree_writer(self.base_uri)
            self.process_children(context)
            writer = context.pop_writer()
            result = writer.get_result()
        else:
            result = u""
        context.variables[self._name] = result
        return


class param_element(variable_element):
    """
    Implementation of the `xsl:param` element.
    """
    pass
