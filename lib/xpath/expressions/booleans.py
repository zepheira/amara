########################################################################
# amara/xpath/expressions/booleans.py
"""
XPath expression nodes that evaluate as booleans.
"""

from amara.xpath import datatypes
from amara.xpath.expressions import expression

__all__ = ('boolean_expression', 
           'or_expr', 'and_expr', 'equality_expr', 'relational_expr')

class boolean_expression(expression):

    return_type = datatypes.boolean

    def compile_as_boolean(self, compiler):
        raise NotImplementedError

class _logical_expr(boolean_expression):

    def __init__(self, left, op, right):
        self._left = left
        self._right = right

    def compile_as_boolean(self, compiler):
        end = compiler.new_block()
        self._left.compile_as_boolean(compiler)
        compiler.emit(self._opcode, end)
        compiler.next_block()
        compiler.emit('POP_TOP') # discard last result
        self._right.compile_as_boolean(compiler)
        compiler.next_block(end)
        return
    compile = compile_as_boolean

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)
        self._left.pprint(indent + '  ', stream)
        self._right.pprint(indent + '  ', stream)

    def __str__(self):
        return '%s %s %s' % (self._left, self._op, self._right)

        
class or_expr(_logical_expr):
    """
    An object representing an or expression
    (XPath 1.0 grammar production 21: OrExpr)
    """
    _op = 'or'
    _opcode = 'JUMP_IF_TRUE'

    
class and_expr(_logical_expr):
    """
    An object representing an and expression
    (XPath 1.0 grammar production 22: AndExpr)
    """
    _op = 'and'
    _opcode = 'JUMP_IF_FALSE'

    
class _comparison_expr(boolean_expression):

    def __init__(self, left, op, right):
        self._left = left
        self._op = op
        self._right = right

    def compile_as_boolean(self, compiler):
        self._left.compile(compiler)
        self._right.compile(compiler)
        # Convert XPath equals (=) into Python equals (==)
        op = self._op == '=' and '==' or self._op
        compiler.emit('COMPARE_OP', op)
        return
    compile = compile_as_boolean

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)
        self._left.pprint(indent + '  ', stream)
        self._right.pprint(indent + '  ', stream)

    def __str__(self):
        return '%s %s %s' % (self._left, self._op, self._right)

        
class equality_expr(_comparison_expr):
    """
    An object representing an equality expression
    (XPath 1.0 grammar production 23: EqualityExpr)
    """
    pass

    
class relational_expr(_comparison_expr):
    """
    An object representing a relational expression
    (XPath 1.0 grammar production 24: RelationalExpr)
    """
    pass
