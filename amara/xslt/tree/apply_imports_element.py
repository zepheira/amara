########################################################################
# amara/xslt/tree/apply_imports_element.py
"""
Implementation of the `xsl:apply-imports` element.
"""

from amara.xslt import XsltError
from amara.xslt.tree import xslt_element
from amara.xslt.reader import content_model, attribute_types

class apply_imports_element(xslt_element):

    content_model = content_model.empty
    attribute_types = {}

    def instantiate(self, context):
        if not context.template:
            raise XsltError(XsltError.APPLYIMPORTS_WITH_NULL_CURRENT_TEMPLATE,
                            self)
        context.transform.apply_templates(context, {}, self.import_precedence)
        return
