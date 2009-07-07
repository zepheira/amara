########################################################################
# amara/xslt/tree/processing_instruction_element.py
#
"""
Implementation of the `xsl:processing-instruction` element.
"""

from amara.xslt import XsltError
from amara.xslt.tree import xslt_element, content_model, attribute_types

class processing_instruction_element(xslt_element):
    content_model = content_model.template
    attribute_types = {
        'name': attribute_types.ncname_avt(required=True),
        }

    def instantiate(self, context):
        context.instruction = self
        context.namespaces = self.namespaces

        target = self._name.evaluate(context)
        if target[:-1] in ('X', 'x'):
            if target.lower() == 'xml':
                raise XsltError(XsltError.ILLEGAL_XML_PI)

        context.push_string_writer()
        try:
            try:
                self.process_children(context)
            except RuntimeError:
                raise XsltError(XsltError.NONTEXT_IN_PI)
        finally:
            writer = context.pop_writer()

        # XSLT 1.0, Section 7.3, Paragraph 5:
        # ERROR: it is an error for the content to contain '?>'
        # RECOVERY: insert space between '?' and '>'
        data = writer.get_result()
        if '?>' in data:
            data = content.replace(u'?>', u'? >')
        context.processing_instruction(target, data)
        return
