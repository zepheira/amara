########################################################################
# amara/xupdate/__init__.py
"""
XUpdate expression wrappers
"""

from amara import XML_NAMESPACE, XMLNS_NAMESPACE
from amara._xmlstring import IsQName, IsNCName
#from amara.xslt.expressions.avt import avt_expression
from amara.xpdate import XUpdateError

__all__ = ['qname_avt', 'namespace_avt', 'ncname_avt']

# proof-of-concept for XSLT attribute value template
from amara.xpath.expressions import expression
class avt_expression(expression):
    __slots__ = ('_name', '_format', '_args')
    def __init__(self, name, value):
        # used by sub-classes
        self._name = name
        try:
            # parts is a list of unicode and/or parsed XPath
            parts = _AvtParser.parse(value)
        except AvtError, error:
            raise XUpdateError(XUpdateError.SYNTAX_ERROR,
                               expression=value, text=str(error))
        self._args = args = []
        for pos, part in enumerate(parts):
            if isinstance(part, unicode):
                if '%' in part:
                    parts[pos] = part.replace('%', '%%')
            else:
                parts[pos] = u'%s'
                args.append(part)
        self._format = u''.join(parts)
        return

    def evaluate_as_string(self, context):
        if self._args:
            return self._format % tuple(arg.evaluate_as_string(context)
                                        for arg in self._args)
        else:
            return self._format


class qname_avt(avt_expression):
    _evaluate = avt_expression.evaluate_as_string
    def evaluate_as_string(self, context):
        result = self._evaluate(context)
        if not IsQName(result):
            raise XUpdateError(XUpdateError.INVALID_QNAME_ATTR,
                               attribute=self._name, value=result)
        return result


class namespace_avt(avt_expression):
    _evaluate = avt_expression.evaluate_as_string
    def evaluate_as_string(self, context):
        result = self._evaluate(context)
        if result in (XML_NAMESPACE, XMLNS_NAMESPACE):
            raise XUpdateError(XUpdateError.INVALID_NSURI_ATTR,
                               attribute=self._name, value=result)
        return result


class ncname_avt(avt_expression):
    _evaluate = avt_expression.evaluate_as_string
    def evaluate_as_string(self, context):
        result = self._evaluate(context)
        if not IsNCName(result):
            raise XUpdateError(XUpdateError.INVALID_NCNAME_ATTR,
                               attribute=self._name, value=result)
        return result
