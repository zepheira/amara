########################################################################
# amara/xslt/tree/copy_element.py
"""
Implementation of `xsl:copy` element.
"""

from amara.domlette import Node, XPathNamespace
from amara.namespaces import XMLNS_NAMESPACE, XSL_NAMESPACE
from amara.xslt import XsltError
from amara.xslt.tree import xslt_element, content_model, attribute_types


class copy_element(xslt_element):

    content_model = content_model.template
    attribute_types = {
        'use-attribute-sets': attribute_types.qnames(),
        }

    def instantiate(self, context):
        context.instruction = self
        context.namespaces = self.namespaces

        node = context.node
        node_type = node.nodeType
        if node_type == Node.ELEMENT_NODE:
            namespaces = {}
            for (namespace, name), attr in node.attributes.iteritems():
                # Namespace nodes are automatically copied as well
                # See XSLT 1.0 Sect 7.5
                if namespace == XMLNS_NAMESPACE:
                    namespaces[name] = attr.value
            context.start_element(node.nodeName, node.namespaceURI, namespaces)
            if self._use_attribute_sets:
                attribute_sets = context.transform.attribute_sets
                for name in self._use_attribute_sets:
                    try:
                        attribute_set = attribute_sets[name]
                    except KeyError:
                        raise XsltError(XsltError.UNDEFINED_ATTRIBUTE_SET, self,
                                        name)
                    attribute_set.instantiate(context)
            self.process_children(context)
            context.end_element(node.nodeName, node.namespaceURI)

        elif node_type == Node.TEXT_NODE:
            context.text(node.data)

        elif node_type == Node.DOCUMENT_NODE:
            self.process_children(context)

        elif node_type == Node.ATTRIBUTE_NODE:
            if node.namespaceURI != XMLNS_NAMESPACE:
                context.attribute(node.name, node.value, node.namespaceURI)

        elif node_type == Node.PROCESSING_INSTRUCTION_NODE:
            context.processing_instruction(node.target, node.data)

        elif node_type == Node.COMMENT_NODE:
            context.comment(node.data)

        elif node_type == XPathNamespace.XPATH_NAMESPACE_NODE:
            # Relies on XmlWriter rules, which is very close to spec:
            # http://www.w3.org/1999/11/REC-xslt-19991116-errata/#E25
            context.namespace(node.nodeName, node.nodeValue)

        else:
            raise RuntimeError("Unupported node type: %r" % node_type)

        return

