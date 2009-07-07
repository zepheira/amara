########################################################################
# amara/xslt/tree/element_element.py
"""
Implementation of the `xsl:element` element.
"""

from amara.namespaces import XSL_NAMESPACE
from amara.xslt import XsltError
from amara.xslt.tree import xslt_element, content_model, attribute_types

class element_element(xslt_element):
    content_model = content_model.template
    attribute_types = {
        'name': attribute_types.raw_qname_avt(required=True),
        'namespace': attribute_types.namespace_uri_avt(),
        'use-attribute-sets': attribute_types.qnames(),
        }

    def instantiate(self, context):
        context.instruction = self
        context.namespaces = self.namespaces

        # XSLT 1.0, Section 7.1.2, Paragraph 2:
        # ERROR: not a QName
        # RECOVERY: instantiate children excluding attribute nodes
        prefix, name = self._name.evaluate(context)
        if prefix:
            name = prefix + u':' + name

        # XSLT 1.0, Section 7.1.2:
        # - if `namespace` is not present, `name` is expanded using the
        #   in-scope namespace declarations
        # - if `namespace` is present, the empty string is the null namespace,
        #   otherwise, the string is the namespace.
        if not self._namespace:
            try:
                namespace = self.namespaces[prefix]
            except KeyError:
                raise XsltError(XsltError.UNDEFINED_PREFIX, prefix=prefix)
        else:
            namespace = self._namespace.evaluate_as_string(context) or None

        context.start_element(name, namespace)
        if self._use_attribute_sets:
            attribute_sets = context.transform.attribute_sets
            for set_name in self._use_attribute_sets:
                try:
                    attribute_set = attribute_sets[set_name]
                except KeyError:
                    raise XsltError(XsltError.UNDEFINED_ATTRIBUTE_SET,
                                    name=set_name)
                attribute_set.instantiate(context)
        self.process_children(context)
        context.end_element(name, namespace)
        return

