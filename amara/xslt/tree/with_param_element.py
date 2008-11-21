########################################################################
# amara/xslt/elements/with_param_element.py
"""
Implementation of the xsl:with-param element.
"""

from amara.xslt import XsltError
from amara.xslt.tree import xslt_element, content_model, attribute_types
from amara.xslt.expressions import rtf_expression

class with_param_element(xslt_element):
    """
    Implementation of the `xsl:with-param` element.
    """
    content_model = content_model.template
    attribute_types = {
        'name': attribute_types.qname(required=True),
        'select': attribute_types.expression(),
        }

    def setup(self):
        if not self._select:
            self._select = rtf_expression(self)
        return
