########################################################################
# amara/xslt/elements/__init__.py

__all__ = [
    'xslt_node', 'xslt_root', 'xslt_text', 'xslt_element',
    'apply_imports_element',        # xsl:apply-imports
    'apply_templates_element',      # xsl:apply-templates
    'attribute_element',            # xsl:attribute
    'attribute_set_element',        # xsl:attribute-set
    'call_template_element',        # xsl:call-template
    'choose_element',               # xsl:choose
    'comment_element',              # xsl:comment
    'copy_element',                 # xsl:copy
    'copy_of_element',              # xsl:copy-of
    'decimal_format_element',       # xsl:decimal-format
    'element_element',              # xsl:element
    'fallback_element',             # xsl:fallback
    'for_each_element',             # xsl:for-each
    'if_element',                   # xsl:if
    'import_element',               # xsl:import
    'include_element',              # xsl:include
    'key_element',                  # xsl:key
    'message_element',              # xsl:message
    'namespace_alias_element',      # xsl:namespace-alias
    'number_element',               # xsl:number
    'otherwise_element',            # xsl:otherwise
    'output_element',               # xsl:otherwise
    'param_element',                # xsl:param
    'preserve_space_element',       # xsl:preserve-space
    'processing_instruction_element', # xsl:processing-instruction
    'sort_element',                 # xsl:sort
    'strip_space_element',          # xsl:strip-space
    'template_element',             # xsl:template
    'text_element',                 # xsl:text
    'transform_element',            # xsl:transform, xsl:stylesheet
    'value_of_element',             # xsl:value-of
    'variable_element',             # xsl:variable, xsl:param
    'when_element',                 # xsl:when
    'with_param_element',           # xsl:with-param
    'ELEMENT_CLASSES',
    ]

from _tree import xslt_node, xslt_root, xslt_text, xslt_element
from literal_element import literal_element

# referenced by other element implementations
from sort_element import sort_element
from with_param_element import with_param_element
from variable_elements import variable_element, param_element

from apply_imports_element import apply_imports_element
from apply_templates_element import apply_templates_element
from attribute_element import attribute_element
from choose_elements import choose_element, when_element, otherwise_element
from comment_element import comment_element
from copy_element import copy_element
from copy_of_element import copy_of_element
from element_element import element_element
from fallback_elements import fallback_element
from for_each_element import for_each_element
from if_element import if_element
from message_element import message_element
from number_element import number_element
from processing_instruction_element import processing_instruction_element
from template_element import template_element
# imported here for purposes of tail-recursion checking
from call_template_element import call_template_element
from text_element import text_element
from transform_element import transform_element
from value_of_element import value_of_element
from declaration_elements import (import_element, include_element,
                                  strip_space_element, preserve_space_element,
                                  output_element,  key_element,
                                  decimal_format_element,
                                  namespace_alias_element,
                                  attribute_set_element)

ELEMENT_CLASSES = {
    'apply-imports': apply_imports_element,
    'apply-templates': apply_templates_element,
    'attribute': attribute_element,
    'attribute-set': attribute_set_element,
    'call-template': call_template_element,
    'choose': choose_element,
    'comment': comment_element,
    'copy': copy_element,
    'copy-of': copy_of_element,
    'decimal-format': decimal_format_element,
    'element': element_element,
    'fallback': fallback_element,
    'for-each': for_each_element,
    'if': if_element,
    'import': import_element,
    'include': include_element,
    'key': key_element,
    'message': message_element,
    'namespace-alias': namespace_alias_element,
    'number': number_element,
    'otherwise': otherwise_element,
    'output': output_element,
    'param': param_element,
    'preserve-space': preserve_space_element,
    'processing-instruction': processing_instruction_element,
    'sort': sort_element,
    'strip-space': strip_space_element,
    'stylesheet': transform_element,
    'template': template_element,
    'text': text_element,
    'transform': transform_element,
    'value-of': value_of_element,
    'variable': variable_element,
    'when': when_element,
    'with-param': with_param_element,
    }