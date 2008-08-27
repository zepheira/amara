########################################################################
# amara/xslt/tree/copy_element.py
"""
Implementation of `xsl:copy` element.
"""

from amara.tree import (Element, Attr, Text, ProcessingInstruction,
                        Comment, Document, Namespace)
from amara.xslt import XsltError
from amara.xslt.tree import xslt_element, content_model, attribute_types

__all__ = ['copy_element']

class copy_element(xslt_element):

    content_model = content_model.template
    attribute_types = {
        'use-attribute-sets': attribute_types.qnames(),
        }

    def instantiate(self, context):
        context.instruction = self
        context.namespaces = self.namespaces

        node = context.node
        if isinstance(node, Element):
            # Namespace nodes are automatically copied as well
            # See XSLT 1.0 Sect 7.5
            nodemap = node.xmlns_attributes
            if nodemap:
                namespaces = {}
                for (xmlns_uri, prefix), value in nodemap.iteritems():
                    namespaces[prefix] = value
            else:
                namespaces = None
            context.start_element(node.xml_qname, node.xml_namespace,
                                  namespaces)
            if self._use_attribute_sets:
                attribute_sets = context.transform.attribute_sets
                for name in self._use_attribute_sets:
                    try:
                        attribute_set = attribute_sets[name]
                    except KeyError:
                        raise XsltError(XsltError.UNDEFINED_ATTRIBUTE_SET,
                                        self, name)
                    attribute_set.instantiate(context)
            self.process_children(context)
            context.end_element(node.xml_qname, node.xml_namespace)

        elif isinstance(node, (Text, Comment)):
            context.text(node.xml_value)

        elif isinstance(node, Document):
            self.process_children(context)

        elif isinstance(node, Attr):
            context.attribute(node.xml_qname, node.xml_value,
                              node.xml_namespace)

        elif isinstance(node, ProcessingInstruction):
            context.processing_instruction(node.xml_target, node.xml_data)

        elif isinstance(node, Namespace):
            # Relies on XmlWriter rules, which is very close to spec:
            # http://www.w3.org/1999/11/REC-xslt-19991116-errata/#E25
            context.namespace(node.xml_qname, node.xml_value)

        else:
            raise RuntimeError("Unupported node type: %r" % type(node))

        return

