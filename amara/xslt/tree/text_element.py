########################################################################
# amara/xslt/tree/text_element.py
"""
Implementation of the `xsl:text` element.
"""

from amara.xslt.tree import xslt_element, content_model, attribute_types

class text_element(xslt_element):

    content_model = content_model.text
    attribute_types = {
        'disable-output-escaping': attribute_types.yesno(default='no'),
        }

    _value = None

    def setup(self):
        if self.children:
            self._value = self.children[0].data
        return

    def instantiate(self, context):
        value = self._value
        if value:
            if self._disable_output_escaping:
                context.text(value, False)
            else:
                context.text(value)
        return

