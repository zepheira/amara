########################################################################
# amara/xupdate/elements.py
"""
XUpdate element wrappers
"""

from amara import XML_NAMESPACE, XMLNS_NAMESPACE
from amara._xmlstring import IsQName, IsNCName
from amara.xslt import XsltError
from amara.xslt.expressions.avt import avt_expression
from amara.xupdate import XUpdateError

__all__ = ['qname_avt', 'namespace_avt', 'ncname_avt']

class xupdate_avt(avt_expression):
    __slots__ = ('_name',)

    def __init__(self, name, value):
        self._name = name
        try:
            avt_expression.__init__(self, value)
        except XsltError, error:
            raise XUpdateError(XUpdateError.SYNTAX_ERROR,
                               expression=value, text=str(error))

    _evaluate = avt_expression.evaluate_as_string


class qname_avt(xupdate_avt):
    def evaluate_as_string(self, context):
        result = self._evaluate(context)
        if not IsQName(result):
            raise XUpdateError(XUpdateError.INVALID_QNAME_ATTR,
                               attribute=self._name, value=result)
        return result


class namespace_avt(xupdate_avt):
    def evaluate_as_string(self, context):
        result = self._evaluate(context)
        if result in (XML_NAMESPACE, XMLNS_NAMESPACE):
            raise XUpdateError(XUpdateError.INVALID_NSURI_ATTR,
                               attribute=self._name, value=result)
        return result


class ncname_avt(xupdate_avt):
    def evaluate_as_string(self, context):
        result = self._evaluate(context)
        if not IsNCName(result):
            raise XUpdateError(XUpdateError.INVALID_NCNAME_ATTR,
                               attribute=self._name, value=result)
        return result
