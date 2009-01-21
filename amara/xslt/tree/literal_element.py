########################################################################
# amara/xslt/tree/literal_element.py
"""
Implementation of XSLT literal result elements
"""

from amara.xslt import XsltError
from amara.xslt.tree import xslt_element

__all__ = ['literal_element']

class literal_element(xslt_element):

    # usually not supplied so default it
    _use_attribute_sets = None

    # This will be called by the stylesheet if it contains any
    # xsl:namespace-alias declarations
    def fixup_aliases(self, aliases):
        # handle the element itself
        if self._output_namespace in aliases:
            self._output_namespace, self.prefix = \
                aliases[self._output_namespace]

        # reprocess the attributes
        pos = 0
        for name, namespace, value in self._output_attrs:
            # NOTE - attributes do not use the default namespace
            if namespace and namespace in aliases:
                prefix, name = name.split(':', 1)
                namespace, prefix = aliases[namespace]
                if prefix:
                    name = prefix + ':' + name
                self._output_attrs[pos] = (name, namespace, value)
            pos += 1

        # handle the namespaces
        for prefix, namespace in self._output_nss.items():
            if namespace in aliases:
                # remove the old entry
                del self._output_nss[prefix]
                # get the aliased namespace and set that pairing
                namespace, prefix = aliases[namespace]
                self._output_nss[prefix] = namespace
        return

    def instantiate(self, context):
        context.instruction = self
        context.namespaces = self.namespaces

        context.start_element(self.nodeName, self._output_namespace,
                              self._output_nss)

        for name, namespace, value in self._output_attrs:
            value = value.evaluate(context)
            context.attribute(name, value, namespace)

        if self._use_attribute_sets:
            attribute_sets = context.transform.attribute_sets
            for name in self._use_attribute_sets:
                try:
                    attribute_set = attribute_sets[name]
                except KeyError:
                    raise XsltError(XsltError.UNDEFINED_ATTRIBUTE_SET, name=name)
                attribute_set.instantiate(context)

        self.process_children(context)

        context.end_element(self.nodeName, self._output_namespace)
        return
