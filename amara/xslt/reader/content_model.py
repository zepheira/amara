########################################################################
# amara/xslt/contentinfo.py
from amara._expat import ContentModel
from amara.namespaces import XSL_NAMESPACE
from amara.lib.xmlstring import isqname

__all__ = ['qname', 'seq', 'alt', 'rep1', 'rep', 'opt',
           'empty', 'text', 'resultelements', 'instructions', 'template',
           'toplevelelements',
           ]

RESULT_ELEMENT = (None, None)
TEXT_NODE = '#PCDATA'
EMPTY = '/empty/'
END_ELEMENT = ContentModel.FINAL_EVENT

def qname(namespace, name):
    """
    Matches a fully qualified name (e.g., xsl:sort)
    """
    assert isqname(name)
    if ':' in name:
        local = name[name.index(':')+1:]
    else:
        local = name
    return ContentModel(ContentModel.TYPE_NAME, (namespace, local), label=name)


def seq(*args):
    """
    Matches the each argument in sequential order.
    """
    return ContentModel(ContentModel.TYPE_SEQ, args)


def alt(*args):
    """
    Matches one of the given arguments.
    """
    return ContentModel(ContentModel.TYPE_ALT, args)


def rep1(arg):
    """
    Matches one or more occurrences of 'arg'.
    """
    assert isinstance(arg, ContentModel)
    arg.quant = ContentModel.QUANT_PLUS
    return arg


def opt(arg):
    """
    Matches zero or one occurrences of 'arg'
    """
    assert isinstance(arg, ContentModel)
    arg.quant = ContentModel.QUANT_OPT
    return arg


def rep(arg):
    """
    Matches zero or more occurrences of 'arg'
    """
    assert isinstance(arg, ContentModel)
    arg.quant = ContentModel.QUANT_REP
    return arg


# special match that matches nothing
empty = ContentModel(ContentModel.TYPE_NAME, EMPTY, ContentModel.QUANT_OPT,
                     label='/empty/',
                     doc="`empty` is the content model for childless elements")

text = ContentModel(ContentModel.TYPE_NAME, TEXT_NODE,
                    ContentModel.QUANT_REP,
                    label="#PCDATA",
                    doc="`text` is the content model for text content")

result_elements = ContentModel(ContentModel.TYPE_NAME, RESULT_ELEMENT,
                               ContentModel.QUANT_REP,
                               label='/result-elements/',
                               doc=("`result_elements` is the set of elements "
                                    " not declared in the XSL namespace"))

instructions = (qname(XSL_NAMESPACE, 'xsl:apply-templates'),
                qname(XSL_NAMESPACE, 'xsl:call-template'),
                qname(XSL_NAMESPACE, 'xsl:apply-imports'),
                qname(XSL_NAMESPACE, 'xsl:for-each'),
                qname(XSL_NAMESPACE, 'xsl:value-of'),
                qname(XSL_NAMESPACE, 'xsl:copy-of'),
                qname(XSL_NAMESPACE, 'xsl:number'),
                qname(XSL_NAMESPACE, 'xsl:choose'),
                qname(XSL_NAMESPACE, 'xsl:if'),
                qname(XSL_NAMESPACE, 'xsl:text'),
                qname(XSL_NAMESPACE, 'xsl:copy'),
                qname(XSL_NAMESPACE, 'xsl:variable'),
                qname(XSL_NAMESPACE, 'xsl:message'),
                qname(XSL_NAMESPACE, 'xsl:fallback'),
                qname(XSL_NAMESPACE, 'xsl:processing-instruction'),
                qname(XSL_NAMESPACE, 'xsl:comment'),
                qname(XSL_NAMESPACE, 'xsl:element'),
                qname(XSL_NAMESPACE, 'xsl:attribute'))
instructions = ContentModel(ContentModel.TYPE_ALT, instructions,
                            ContentModel.QUANT_REP, label='/instructions/',
                            doc=("`instructions` is the set of elements which"
                                 " have a category of instruction"))

template = ContentModel(ContentModel.TYPE_ALT,
                        (text, instructions, result_elements),
                        ContentModel.QUANT_REP, label='/template/',
                        doc=("`template` is the set of `text`, `instructions`"
                             " or `result-elements`"))

top_level_elements = (qname(XSL_NAMESPACE, 'xsl:include'),
                      qname(XSL_NAMESPACE, 'xsl:strip-space'),
                      qname(XSL_NAMESPACE, 'xsl:preserve-space'),
                      qname(XSL_NAMESPACE, 'xsl:output'),
                      qname(XSL_NAMESPACE, 'xsl:key'),
                      qname(XSL_NAMESPACE, 'xsl:decimal-format'),
                      qname(XSL_NAMESPACE, 'xsl:attribute-set'),
                      qname(XSL_NAMESPACE, 'xsl:variable'),
                      qname(XSL_NAMESPACE, 'xsl:param'),
                      qname(XSL_NAMESPACE, 'xsl:template'),
                      qname(XSL_NAMESPACE, 'xsl:namespace-alias'),
                      result_elements)
top_level_elements = ContentModel(ContentModel.TYPE_ALT, top_level_elements,
                                  ContentModel.QUANT_REP,
                                  label='/top-level-elements/',
                                  doc=("`toplevelelements` is the set of "
                                       "elements which have a category of "
                                       "`top-level-element` or are a "
                                       "`result-element`."))
