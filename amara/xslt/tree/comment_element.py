########################################################################
# amara/xslt/tree/comment_element.py
"""
Implementation of `xsl:comment` instruction element.
"""

from amara.namespaces import XSL_NAMESPACE
from amara.xslt import XsltError
from amara.xslt.tree import xslt_element, content_model, attribute_types

class comment_element(xslt_element):

    content_model = content_model.template
    attribute_types = {}

    def instantiate(self, context):
        context.instruction = self
        context.namespaces = self.namespaces

        # XSLT 1.0, Section 7.4, Paragraph 3:
        # ERROR: create anything other than text nodes as content
        # RECOVERY: ignore the offending nodes.
        context.push_string_writer()
        try:
            try:
                self.process_children(context)
            except RuntimeError:
                raise XsltRuntimeException(XsltError.NONTEXT_IN_COMMENT)
        finally:
            writer = context.pop_writer()

        # XSLT 1.0, Section 7.4, Paragraph 4:
        # ERROR: content contains '--' or ends with '-'
        # RECOVERY: add space after '-' (e.g., resulting in '- -' or '- ')
        data = writer.get_result().replace(u'--', u'- -')
        if data[-1:] == u'-':
            data += u' '
        context.comment(data)
        return
