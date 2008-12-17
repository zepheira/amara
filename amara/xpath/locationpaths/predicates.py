########################################################################
# amara/xpath/locationpaths/predicates.py
"""
A parsed token that represents a predicate list.
"""
from __future__ import absolute_import
from itertools import count, izip

from amara.xpath import datatypes
from amara.xpath.expressions.basics import literal, variable_reference
from amara.xpath.expressions.booleans import equality_expr, relational_expr
from amara.xpath.functions import position_function

from ._nodetests import positionfilter
from ._paths import pathiter

__all__ = ['predicates', 'predicate']

class predicates(tuple):
    def __init__(self, *args):
        self.select = pathiter(pred.select for pred in self).select
        return

    def filter(self, nodes, context, reverse):
        if self:
            state = context.node, context.position, context.size
            for predicate in self:
                nodes = datatypes.nodeset(predicate.select(context, nodes))
            context.node, context.position, context.size = state
        else:
            nodes = datatypes.nodeset(nodes)
        if reverse:
            nodes.reverse()
        return nodes

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)
        for pred in self:
            pred.pprint(indent + '  ', stream)

    def __repr__(self):
        ptr = id(self)
        if ptr < 0: ptr += 0x100000000L
        return '<%s at 0x%x: %s>' % (self.__class__.__name__, ptr, self)

    def __str__(self):
        return ''.join(map(str, self))


class predicate:
    def __init__(self, expression):
        self._expr = expression
        # Check for just "Number"
        if isinstance(expression, literal):
            const = datatypes.number(expression._literal)
            index = int(const)
            if index == const and index >= 1:
                self.select = positionfilter(index)
            else:
                # FIXME: add warning that expression will not select anything
                self.select = izip()
            return

        # Check for "position() = Expr"
        if isinstance(expression, equality_expr) and expression._op == '=':
            if isinstance(expression._left, position_function):
                expression = expression._right
                if isinstance(expression, literal):
                    const = datatypes.number(expression._literal)
                    index = int(const)
                    if index == const and index >= 1:
                        self.select = positionfilter(index)
                    else:
                        self.select = izip()
                else:
                    self.select = self._number
                return
            elif isinstance(expression._right, position_function):
                expression = expression._left
                if isinstance(expression, literal):
                    const = datatypes.number(expression._literal)
                    index = int(const)
                    if index == const and index >= 1:
                        self.select = positionfilter(index)
                    else:
                        self.select = izip()
                else:
                    self.select = self._number
                return

        # Check for "position() [>,>=] Expr" or "Expr [<,<=] position()"
        # FIXME - do full slice-type notation
        if isinstance(expression, relational_expr):
            op = expression._op
            if (isinstance(expression._left, position_function) and
                isinstance(expression._right, (literal, variable_reference)) 
                and op in ('>', '>=')):
                self._start = expression._right
                self._position = (op == '>')
                self.select = self._slice
                return
            elif (isinstance(expression._left, (literal, variable_reference)) 
                  and isinstance(expression._right, Position)
                  and op in ('<', '<=')):
                self._start = expression._left
                self._position = (op == '<')
                self.select = self._slice
                return

        if issubclass(expression.return_type, datatypes.number):
            self.select = self._number
        elif not issubclass(expression.return_type, datatypes.xpathobject):
            self.select = self._boolean
        return

    def _slice(self, context, nodes):
        start = self._start.evaluate_as_number(context)
        position = self._position
        if position > start:
            return nodes
        position += 1
        nodes = iter(nodes)
        for node in nodes:
            if position > start:
                break
            position += 1
        return nodes

    def _number(self, context, nodes):
        expr = self._expr
        position = 1
        for node in nodes:
            context.node, context.position = node, position
            if expr.evaluate_as_number(context) == position:
                yield node
            position += 1
        return

    def _boolean(self, context, nodes):
        expr = self._expr
        position = 1
        for node in nodes:
            context.node, context.position = node, position
            if expr.evaluate_as_boolean(context):
                yield node
            position += 1
        return

    def select(self, context, nodes):
        expr = self._expr
        position = 1
        for node in nodes:
            context.node, context.position = node, position
            result = expr.evaluate(context)
            if isinstance(result, datatypes.number):
                # This must be separate to prevent falling into
                # the boolean check.
                if result == position:
                    yield node
            elif result:
                yield node
            position += 1
        return

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)
        self._expr.pprint(indent + '  ', stream)

    def __repr__(self):
        ptr = id(self)
        if ptr < 0: ptr += 0x100000000L
        return '<%s at 0x%x: %s>' % (self.__class__.__name__, ptr, self)

    def __str__(self):
        return '[%s]' % self._expr
