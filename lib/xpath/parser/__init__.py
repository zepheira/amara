from amara.xpath import XPathError
from amara.xpath.parser import _xpathparser

__all__ = ['xpathparser', 'parse']

class xpathparser(_xpathparser.parser):

    _parse = _xpathparser.parser.parse

    def parse(self, expr):
        """Parses the string `expr` into an AST"""
        try:
            return self._parse(expr)
        except _xpathparser.error, error:
            raise XPathError(XPathError.SYNTAX, line=error.lineno, 
                             column=error.offset, text=error.msg)

_parser = xpathparser()
_parse = _parser._parse
parse = _parser.parse

if __name__ == '__main__':
    import sys
    sys.exit(_xpathparser.console().cmdloop())
