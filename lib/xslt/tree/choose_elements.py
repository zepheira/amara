########################################################################
# amara/xslt/tree/choose_element.py
"""
Implementation of `xsl:choose`, `xsl:when` and `xsl:otherwise` elements.
"""

from amara.namespaces import XSL_NAMESPACE
from amara.xslt import XsltError
from amara.xslt.tree import xslt_element, content_model, attribute_types

__all__ = ('choose_element', 'when_element', 'otherwise_element')


class when_element(xslt_element):
    content_model = content_model.template
    attribute_types = {
        'test': attribute_types.boolean_expression(required=True),
        }


class otherwise_element(xslt_element):
    content_model = content_model.template
    attribute_types = {}


class choose_element(xslt_element):
    content_model = content_model.seq(
        content_model.rep1(content_model.qname(XSL_NAMESPACE, 'xsl:when')),
        content_model.opt(content_model.qname(XSL_NAMESPACE, 'xsl:otherwise')),
        )
    attribute_types = {}

    def setup(self):
        choices = self.children
        if isinstance(choices[-1], otherwise_element):
            self._otherwise = choices[-1]
            choices = choices[:-1]
        else:
            self._otherwise = None
        self._choices = [ (child, child._test) for child in choices ]
        return

    def instantiate(self, context):
        for child, test in self._choices:
            context.instruction, context.namespaces = child, child.namespaces
            if test.evaluate_as_boolean(context):
                chosen = child
                break
        else:
            # xsl:otherwise
            chosen = self._otherwise
            if not chosen:
                return
        return chosen.process_children(context)

    #def __getstate__(self):
    #    del self._choices
    #    return xslt_element.__getstate__(self)

    #def __setstate__(self, state):
    #    xslt_element.__setstate__(self, state)
    #    if self._otherwise:
    #        choices = self.children[:-1]
    #    else:
    #        choices = self.children
    #    self._choices = [ (child, child._test.evaluate_as_boolean)
    #                      for child in choices ]
    #    return
