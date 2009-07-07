########################################################################
# amara/xslt/tree/attribute_element.py
"""
Implementation of `xsl:attribute` element
"""

from amara.namespaces import XSL_NAMESPACE
from amara.xslt import XsltError
from amara.xslt.tree import xslt_element, content_model, attribute_types

class attribute_element(xslt_element):
    content_model = content_model.template
    attribute_types = {
        'name': attribute_types.raw_qname_avt(required=True),
        'namespace': attribute_types.namespace_uri_avt(),
        }

    def instantiate(self, context):
        context.instruction = self
        context.namespaces = self.namespaces

        prefix, name = self._name.evaluate(context)
        if prefix:
            name = prefix + u':' + name
        elif name == 'xmlns':
            # Section 7.1.3, Paragraph 2
            raise XsltError(XsltError.BAD_ATTRIBUTE_NAME, name=name)

        # From sec. 7.1.3 of the XSLT spec:
        # 1. if 'namespace' is not present, use ns in scope, based on prefix
        #    from the element QName in 'name'; if no prefix, use null-namespace
        # 2. if 'namespace' is present and empty string, use null-namespace
        # 3. otherwise, use 'namespace' directly
        #
        if not self._namespace:
            if prefix is not None:
                try:
                    namespace = self.namespaces[prefix]
                except KeyError:
                    raise XsltError(XsltError.UNDEFINED_PREFIX, prefix=prefix)
            else:
                namespace = None
        else:
            namespace = self._namespace.evaluate_as_string(context) or None

        context.push_string_writer()
        try:
            try:
                self.process_children(context)
            except RuntimeError:
                raise XsltError(XsltError.NONTEXT_IN_ATTRIBUTE)
        finally:
            writer = context.pop_writer()
        context.attribute(name, writer.get_result(), namespace)
        return
