########################################################################
# amara/xpath/compiler/__init__.py
"""
XPath expression compiler.
"""
from __future__ import absolute_import
import new

from .assembler import assembler

__all__ = ['xpathcompiler']

class xpathcompiler(object):

    _nasts = 0
    _nlocals = 0

    def __init__(self, context=None):
        if context is not None:
            self.namespaces = context.namespaces
            self.variables = context.variables
            self.functions = context.functions
        else:
            self.namespaces = {}
            self.variables = {}
            self.functions = {}

        self._graph = assembler()
        self.emit = self._graph.emit
        self.new_block = self._graph.new_block
        self.next_block = self._graph.next_block
        return

    def compile(self, name, args=None, docstring=None, filename=None,
                firstlineno=0):
        # Generate the code object
        if args is None:
            args = ('context',)
        if filename is None:
            filename = '<ast-%d>' % xpathcompiler._nasts
            xpathcompiler._nasts += 1
        code = self._graph.assemble(name, args, docstring, filename,
                                    firstlineno)
        # Make the function
        if 0: #Compiler._nasts == 200:
            print '--',code.co_name,'-'*(60 - len(code.co_name))
            import dis
            dis.dis(code)
            return new.function(code, {'__lltrace__': 1})
        return new.function(code, {})

    def tmpname(self):
        self._nlocals += 1
        return '$%d' % self._nlocals

    # For documentation purposes only; replaced in the constructor
    def emit(self, *instructions):
        return self._graph.emit(*instructions)

    # For documentation purposes only; replaced in the constructor
    def new_block(self):
        return self._graph.new_block()

    # For documentation purposes only; replaced in the constructor
    def next_block(self):
        return self._graph.next_block()

    def emitRootNodeSet(self):
        self.emit('LOAD_FAST', 'context',
                  'LOAD_ATTR', 'node',
                  'LOAD_ATTR', 'xml_root',
                  'BUILD_TUPLE', 1,
                  )
        return

    def emitContextNodeSet(self):
        self.emit('LOAD_FAST', 'context',
                  'LOAD_ATTR', 'node',
                  'BUILD_TUPLE', 1,
                  )
        return
