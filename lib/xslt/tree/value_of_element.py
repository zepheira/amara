########################################################################
# amara/xslt/tree/value_of_element.py
"""
Implementation of the `xsl:value-of` element.
"""

from amara.xslt.tree import xslt_element, content_model, attribute_types

class value_of_element(xslt_element):

    content_model = content_model.empty
    attribute_types = {
        'select': attribute_types.string_expression(required=True),
        'disable-output-escaping': attribute_types.yesno(default='no'),
        }

    def instantiate(self, context):
        context.instruction = self
        context.namespaces = self.namespaces

        text = self._select.evaluate_as_string(context)
        if text:
            if self._disable_output_escaping:
                context.text(text, False)
            else:
                context.text(text)
        return

