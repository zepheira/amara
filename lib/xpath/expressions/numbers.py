########################################################################
# amara/xpath/expressions/numbers.py
"""
XPath expression nodes that evaluate as numbers.
"""

from amara.xpath import expressions, datatypes

__all__ = ('number_expression', 
           'additive_expr', 'multiplicative_expr', 'unary_expr')

class number_expression(expressions.expression):

    return_type = datatypes.number

    def compile_as_number(self, compiler):
        raise NotImplementedError


class _binary_expr(number_expression):
    _opmap = {
        '+' : 'BINARY_ADD',
        '-' : 'BINARY_SUBTRACT',
        '*' : 'BINARY_MULTIPLY',
        'div' : 'BINARY_DIVIDE',
        'mod' : 'BINARY_MODULO',
        }

    def __init__(self, left, op, right):
        self._left = left
        self._op = op
        self._right = right

    def compile_as_number(self, compiler):
        self._left.compile_as_number(compiler)
        self._right.compile_as_number(compiler)
        compiler.emit(self._opmap[self._op])
        return
    compile = compile_as_number

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)
        self._left.pprint(indent + '  ', stream)
        self._right.pprint(indent + '  ', stream)

    def __str__(self):
        return '%s %s %s' % (self._left, self._op, self._right)


class additive_expr(_binary_expr):
    """
    An object representing an additive expression
    (XPath 1.0 grammar production 25: AdditiveExpr)
    """
    pass


class multiplicative_expr(_binary_expr):
    """
    An object representing an multiplicative expression
    (XPath 1.0 grammar production 26: MultiplicativeExpr)
    """
    pass


class unary_expr(number_expression):
    """
    An object representing a unary expression
    (XPath 1.0 grammar production 27: UnaryExpr)
    """
    def __init__(self, expr):
        self._expr = expr

    def compile_as_number(self, compiler):
        self._expr.compile_as_number(compiler)
        compiler.emit('UNARY_NEGATIVE')
        return
    compile = compile_as_number

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)
        self._expr.pprint(indent + '  ', stream)

    def __str__(self):
        return '-%s' % self._expr
