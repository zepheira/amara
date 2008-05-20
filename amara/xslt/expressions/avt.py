########################################################################
# amara/xslt/expressions/avt.py
"""
Implementation of XSLT attribute value templates
"""

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
        return

    def evaluate_as_string(self, context):
        if self._args:
            return self._format % tuple(arg.evaluate_as_string(context)
                                        for arg in self._args)
        else:
            # use empty format args to force '%%' replacement
            return self._format % ()

class attribute_value_template:

    def __init__(self, source, validator=None, element=None):
        self.source = source
        self.validator = validator
        self.element = element

        try:
            # parts is a list of unicode and/or parsed XPath
            parts = _AvtParser.parse(source)
        except SyntaxError, exc:
            raise XsltError(XsltError.AVT_SYNTAX)

        self._resultFormat = u""
        self._parsedParts = parsed_parts = []
        for part in parts:
            if isinstance(part, unicode):
                if '%' in part:
                    part = part.replace('%', '%%')
                self._resultFormat += part
            else:
                self._resultFormat += u"%s"
                parsed_parts.append(part)
        return

    def isConstant(self):
        return not self._parsedParts

    def evaluate(self, context):
        if not self.element and hasattr(context, 'currentInstruction'):
            self.element = context.currentInstruction

        result = self._resultFormat % tuple([ convert(x.evaluate(context))
                                              for x in self._parsedParts ])
        if self.validator:
            return self.validator.reprocess(self.element, result)
        else:
            return result

    def __nonzero__(self):
        return self.source is not None
