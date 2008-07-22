########################################################################
# amara/xslt/tree/message_element.py
"""
Implementation of the `xsl:message` element.
"""

from cStringIO import StringIO
from amara.namespaces import XSL_NAMESPACE
from amara.writers import outputparameters, xmlwriter
from amara.xslt import XsltError
from amara.xslt.tree import xslt_element, content_model, attribute_types

class message_element(xslt_element):
    content_model = content_model.template
    attribute_types = {
        'terminate': attribute_types.yesno(default='no'),
        }

    def instantiate(self, context):
        output_parameters = outputparameters.output_parameters(
            method='xml', encoding=context.output_parameters.encoding,
            omit_xml_declaration=True)
        context.push_writer(xmlwriter(output_parameters, StringIO()))
        try:
            for child in self.children:
                child.instantiate(context, processor)
        finally:
            writer = context.pop_writer()
        msg = writer.stream.getvalue()
        if self._terminate:
            raise XsltError(XsltError.STYLESHEET_REQUESTED_TERMINATION,
                            self, msg)
        else:
            context.message(msg)
        return

