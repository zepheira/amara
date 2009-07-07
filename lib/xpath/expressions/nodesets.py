########################################################################
# amara/xpath/expressions/nodesets.py
"""
XPath expression nodes that evaluate as nodesets.
"""

from amara.xpath import datatypes, expressions

__all__ = ('nodeset_expression', 
           'union_expr', 'path_expr', 'filter_expr')

class nodeset_expression(expressions.expression):

    return_type = datatypes.nodeset

    def _make_block(self, compiler):
        compiler.emit(
            # Push the context state onto the stack
            'LOAD_FAST', 'context',
            'LOAD_ATTR', 'node',
            'LOAD_FAST', 'context',
            'LOAD_ATTR', 'position',
            'LOAD_FAST', 'context',
            'LOAD_ATTR', 'size',
            )

        # Yield control back to the caller to allow writing of the body.
        yield None

        compiler.emit(
            # Move the result 4 places down the stack (past the context state).
            'ROT_FOUR',
            # Restore context values in reverse order of above!
            'LOAD_FAST', 'context',
            'STORE_ATTR', 'size',
            'LOAD_FAST', 'context',
            'STORE_ATTR', 'position',
            'LOAD_FAST', 'context',
            'STORE_ATTR', 'node',
            )
        return

    def _make_loop(self, compiler, foundops, emptyops):
        for block in self._make_block(compiler):
            end_block = compiler.new_block()
            else_block = compiler.new_block()
            compiler.emit(
                'LOAD_FAST', 'context',
                'LOAD_ATTR', 'node',
                'BUILD_TUPLE', 1,
                )
            self.compile_iterable(compiler)
            compiler.emit(
                'GET_ITER',
                # Set the loop to jump to the `else` block when `iter` is empty
                'FOR_ITER', else_block,
                )
            # Emit the instructions for a successful match
            compiler.emit(*foundops)
            compiler.emit(
                # Remove `iter` from the stack
                'ROT_TWO',
                'POP_TOP',
                # Jump to the end of the `else` block
                'JUMP_FORWARD', end_block,
                )
            # Begin the `else` block
            compiler.next_block(else_block)
            # Emit the instructions to use for no match
            compiler.emit(*emptyops)
            compiler.next_block(end_block)
        return

    def compile_as_boolean(self, compiler):
        found = ('POP_TOP', # discard context node from the stack
                 'LOAD_CONST', datatypes.boolean.TRUE)
        empty = ('LOAD_CONST', datatypes.boolean.FALSE)
        return self._make_loop(compiler, found, empty)

    def compile_as_number(self, compiler):
        # Call number() on the matched object
        found = ('LOAD_CONST', datatypes.number,
                 'ROT_TWO',
                 'CALL_FUNCTION', 1)
        # Use number.NaN as the result. We cannot use this value directly
        # as the assembler needs to be able to use equality testing.
        empty = ('LOAD_CONST', datatypes.number,
                 'LOAD_ATTR', 'NaN')
        return self._make_loop(compiler, found, empty)

    def compile_as_string(self, compiler):
        # Call string() on the matched object
        found = ('LOAD_CONST', datatypes.string,
                 'ROT_TWO',
                 'CALL_FUNCTION', 1)
        empty = ('LOAD_CONST', datatypes.string.EMPTY)
        return self._make_loop(compiler, found, empty)

    def compile_as_nodeset(self, compiler):
        for block in self._make_block(compiler):
            compiler.emit('LOAD_CONST', datatypes.nodeset,
                          # add context node to the stack
                          'LOAD_FAST', 'context',
                          'LOAD_ATTR', 'node',
                          'BUILD_TUPLE', 1,
                          )
            self.compile_iterable(compiler)
            compiler.emit('CALL_FUNCTION', 1)
        return
    compile = compile_as_nodeset

    def compile_iterable(self, compiler):
        raise NotImplementedError(self.__class__.__name__)

    def select(self, context, nodes=None):
        raise NotImplementedError(self.__class__.__name__)


class union_expr(nodeset_expression):
    """
    An object representing a union expression
    (XPath 1.0 grammar production 18: UnionExpr)
    """
    def __init__(self, left, right):
        if isinstance(left, union_expr):
            self._paths = left._paths
            self._paths.append(right)
        else:
            self._paths = [left, right]
        return

    def compile_iterable(self, compiler):
        from amara.xpath.locationpaths import _paths
        emit = compiler.emit
        tmpname = compiler.tmpname()
        emit(# store the current context node
             'STORE_FAST', tmpname,
             # begin the UnionIter function call construction
             'LOAD_CONST', _paths.unioniter,
             )
        # build the arguments for the function call
        for path in self._paths:
            # restore the context node
            emit('LOAD_FAST', tmpname)
            path.compile_iterable(compiler)
        emit('CALL_FUNCTION', len(self._paths),
             # clear stored context node
             'DELETE_FAST', tmpname,
             )
        return

    def compile_as_boolean(self, compiler):
        end = compiler.new_block()
        for path in self._paths[:-1]:
            path.compile_as_boolean(compiler)
            compiler.emit('JUMP_IF_TRUE', end)
            compiler.next_block()
            compiler.emit('POP_TOP')
        self._paths[-1].compile_as_boolean(compiler)
        compiler.next_block(end)
        return

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)
        for path in self._paths:
            path.pprint(indent + '  ', stream)

    def __str__(self):
        return ' | '.join(map(str, self._paths))


class path_expr(nodeset_expression):
    """
    An object representing a path expression
    (XPath 1.0 grammar production 19: PathExpr)
    """
    def __init__(self, expression, sep, path):
        if sep == '//':
            from amara.xpath.locationpaths import \
                relative_location_path, location_step
            from amara.xpath.locationpaths.axisspecifiers import axis_specifier
            from amara.xpath.locationpaths.nodetests import node_type
            assert isinstance(path, relative_location_path), repr(path)
            step = location_step(axis_specifier('descendant-or-self'), 
                                 node_type('node'))
            path._steps.insert(0, step)
        self._expression = expression
        self._path = path
        return

    def compile_iterable(self, compiler):
        if isinstance(self._expression, nodeset_expression):
            self._expression.compile_iterable(compiler)
        else:
            # discard context node from the stack
            compiler.emit('POP_TOP')
            self._expression.compile_as_nodeset(compiler)
        self._path.compile_iterable(compiler)
        return

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)
        self._expression.pprint(indent + '  ', stream)
        self._path.pprint(indent + '  ', stream)

    def __str__(self):
        return '%s/%s' % (self._expression, self._path)


class filter_expr(nodeset_expression):
    """
    An object representing a filter expression
    (XPath 1.0 grammar production 20: FilterExpr)
    """
    def __init__(self, expression, predicates):
        self._expression = expression
        self._predicates = predicates
        return

    def compile_iterable(self, compiler):
        # discard context node from the stack
        from amara.xpath.locationpaths import _paths
        compiler.emit('POP_TOP')
        self._expression.compile_as_nodeset(compiler)
        if self._predicates:
            predicates = _paths.pathiter(p.select for p in self._predicates)
            compiler.emit('LOAD_CONST', predicates.select,
                          'LOAD_FAST', 'context',
                          # stack is now [context, select, nodes]
                          'ROT_THREE',
                          # stack is now [select, nodes, context]
                          'ROT_THREE',
                          # stack is now [nodes, context, select]
                          'CALL_FUNCTION', 2,
                          )
        return

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)
        self._expression.pprint(indent + '  ', stream)
        self._predicates.pprint(indent + '  ', stream)

    def __str__(self):
        return '%s%s' % (self._expression, self._predicates)
