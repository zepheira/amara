########################################################################
# amara/xslt/expressions/avt.py
"""
Implementation of XSLT attribute value templates
"""

from amara.xpath import datatypes
from amara.xpath.expressions import expression
from amara.xslt import XsltError
from amara.xslt.expressions import _avt

_parse_avt = _avt.parser().parse

class avt_expression(expression):
    __slots__ = ('_format', '_args')
    def __init__(self, value):
        try:
            # parts is a list of unicode and/or parsed XPath
            parts = _parse_avt(value)
        except _avt.error, error:
            raise XsltError(XsltError.AVT_SYNTAX)
        self._args = args = []
        for pos, part in enumerate(parts):
            if isinstance(part, unicode):
                if '%' in part:
                    parts[pos] = part.replace('%', '%%')
            else:
                parts[pos] = u'%s'
                args.append(part)
        self._format = u''.join(parts)
        if not self._args:
            # use empty format args to force '%%' replacement
            self._format = datatypes.string(self._format % ())
        return

    def evaluate_as_string(self, context):
        if not self._args:
            return self._format
        result = self._format % tuple(arg.evaluate_as_string(context)
                                      for arg in self._args)
        return datatypes.string(result)
    evaluate = evaluate_as_string

    def __str__(self):
        return '{' + self._format % tuple(self._args) + '}'
