########################################################################
# amara/xslt/tree/fallback_elements.py
"""
Implementation of `xsl:fallback` element.
"""

from amara.xslt import XsltError, XsltRuntimeError
from amara.xslt.tree import xslt_element, content_model, attribute_types

__all__ = (
    'fallback_element', 'undefined_xslt_element', 'undefined_extension_element'
    )

class fallback_element(xslt_element):
    content_model = content_model.template
    attribute_types = {}

    def instantiate(self, context):
        # By default, fallback element children are not instaniated.
        return


class _undefined_element(xslt_element):

    content_model = content_model.template
    _error_code = XsltError.INTERNAL_ERROR

    def setup(self):
        self._fallback = [ child for child in self.children
                           if isinstance(child, fallback_element) ]

    def instantiate(self, context):
        context.instruction = self
        context.namespaces = self.namespaces

        if not self._fallback:
            raise XsltRuntimeError(self._error_code, self,
                                   element=self.nodeName)

        for fallback in self._fallback:
            fallback.process_children(context)
        return


class undefined_xslt_element(_undefined_element):

    attribute_types = {}
    _error_code = XsltError.FWD_COMPAT_WITHOUT_FALLBACK


class undefined_extension_element(_undefined_element):

    attribute_types = None
    _error_code = XsltError.UNKNOWN_EXTENSION_ELEMENT

