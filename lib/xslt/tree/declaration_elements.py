########################################################################
# amara/xslt/tree/declaration_elements.py
"""
Implementation of the top-level elements.
"""

from amara.namespaces import XSL_NAMESPACE, EXTENSION_NAMESPACE
from amara.xslt import XsltError
from amara.xslt.tree import xslt_element, content_model, attribute_types

__all__ = (
    'import_element', 'include_element', 'strip_space_element',
    'preserve_space_element', 'output_element', 'key_element',
    'decimal_format_element', 'namespace_alias_element',
    'attribute_set_element'
    )


class _combining_element(xslt_element):
    content_model = content_model.empty
    attribute_types = {
        'href': attribute_types.uri_reference(required=True),
        }

class import_element(_combining_element):
    """Implementation of the `xsl:import` element"""
    pass

class include_element(_combining_element):
    """Implementation of the `xsl:include_elementelement"""
    pass


class _whitespace_element(xslt_element):
    content_model = content_model.empty
    attribute_types = {
        'elements' : attribute_types.tokens(required=1),
        }

    _strip_whitespace = None


class strip_space_element(_whitespace_element):
    """Implementation of the `xsl:strip-space` element"""
    _strip_whitespace = True

class preserve_space_element(_whitespace_element):
    """Implementation of the `xsl:preserve-space` element"""
    _strip_whitespace = False


class output_element(xslt_element):
    """Implementation of the `xsl:output` element"""
    content_model = content_model.empty
    attribute_types = {
        'method': attribute_types.qname(),
        'version': attribute_types.nmtoken(),
        'encoding': attribute_types.string(),
        'omit-xml-declaration': attribute_types.yesno(),
        'standalone': attribute_types.yesno(),
        'doctype-public': attribute_types.string(),
        'doctype-system': attribute_types.string(),
        'cdata-section-elements': attribute_types.qnames(),
        'indent': attribute_types.yesno(),
        'media-type': attribute_types.string(),
        'f:byte-order-mark': attribute_types.yesno(
            description=("Whether to force output of a byte order mark (BOM). "
                         "Usually used to generate a UTF-8 BOM.  Do not use "
                         "unless you're sure you know what you're doing")),
        'f:canonical-form': attribute_types.yesno(),
        }

    def setup(self):
        if (EXTENSION_NAMESPACE, 'byte-order-mark') in self.attributes:
            value = self.attributes[EXTENSION_NAMESPACE, 'byte-order-mark']
            self._byte_order_mark = value == 'yes'
        else:
            self._byte_order_mark = None
        if (EXTENSION_NAMESPACE, 'canonical-form') in self.attributes:
            value = self.attributes[EXTENSION_NAMESPACE, 'canonical-form']
            self._canonical_form = value == 'yes'
        else:
            self._canonical_form = None
        return

class key_element(xslt_element):
    """Implementation of the `xsl:key` element"""
    content_model = content_model.empty
    attribute_types = {
        'name': attribute_types.qname(required=True),
        'match': attribute_types.pattern(required=True),
        'use': attribute_types.expression(required=True),
        }


class decimal_format_element(xslt_element):
    content_model = content_model.empty
    attribute_types = {
        'name': attribute_types.qname(),
        'decimal-separator': attribute_types.char(default='.'),
        'grouping-separator': attribute_types.char(default=','),
        'infinity': attribute_types.string(default='Infinity'),
        'minus-sign': attribute_types.char(default='-'),
        'NaN': attribute_types.string(default='NaN'),
        'percent': attribute_types.char(default='%'),
        'per-mille': attribute_types.char(default=unichr(0x2030)),
        'zero-digit': attribute_types.char(default='0'),
        'digit': attribute_types.char(default='#'),
        'pattern-separator': attribute_types.char(default=';'),
        }


class namespace_alias_element(xslt_element):
    content_model = content_model.empty
    attribute_types = {
        'stylesheet-prefix': attribute_types.prefix(required=True),
        'result-prefix': attribute_types.prefix(required=True),
        }


class attribute_set_element(xslt_element):
    content_model = content_model.rep(
        content_model.qname(XSL_NAMESPACE, 'xsl:attribute')
        )
    attribute_types = {
        'name': attribute_types.qname(required=True),
        'use-attribute-sets': attribute_types.qnames(),
        }

    def instantiate(self, context, used=None):
        if used is None:
            used = []

        if self in used:
            raise XsltError(XsltError.CIRCULAR_ATTRIBUTE_SET,
                                       self, self._name)
        else:
            used.append(self)

        # XSLT 1.0, Section 7.1.4, Paragraph 4:
        # The available variable bindings are only the top-level ones.
        variables = context.variables
        context.variables = context.global_variables

        attribute_sets = context.transform.attribute_sets
        for name in self._use_attribute_sets:
            try:
                attribute_set = attribute_sets[name]
            except KeyError:
                raise XsltError(XsltError.UNDEFINED_ATTRIBUTE_SET,
                                           self, attr_set_name)
            else:
              attribute_set.instantiate(context)

        self.process_children(context)

        context.variables = variables
        used.remove(self)
        return
