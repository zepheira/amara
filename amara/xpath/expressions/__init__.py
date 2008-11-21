########################################################################
# amara/xpath/expressions/__init__.py
"""
The implementation of parsed XPath expression tokens.
"""

from amara.xpath import datatypes
from amara.xpath.compiler import xpathcompiler

__all__ = ['expression']

class expression(object):

    return_type = datatypes.xpathobject

    class __metaclass__(type):
        pass

    def compile(self, compiler):
        raise NotImplementedError('%s.compile' % (self.__class__.__name__,))

    def compile_as_boolean(self, compiler):
        """Compiles the expression into a boolean result."""
        # Load the callable object
        compiler.emit('LOAD_CONST', datatypes.boolean)
        # Build the argument(s)
        self.compile(compiler)
        compiler.emit('CALL_FUNCTION', 1)
        return

    def compile_as_number(self, compiler):
        """Compiles the expression into a number result."""
        # Load the callable object
        compiler.emit('LOAD_CONST', datatypes.number)
        # Build the argument(s)
        self.compile(compiler)
        compiler.emit('CALL_FUNCTION', 1)

    def compile_as_string(self, compiler):
        """Compiles the expression into a string result."""
        # Load the callable object
        compiler.emit('LOAD_CONST', datatypes.string)
        # Build the argument(s)
        self.compile(compiler)
        compiler.emit('CALL_FUNCTION', 1)

    def compile_as_nodeset(self, compiler):
        """Compiles the expression into a nodeset result. 
        By default, this is an error.
        """
        raise TypeError('cannot convert to a nodeset')

    def compile_iterable(self, compiler):
        """Compiles the expression into an iterable. 
        By default, this is an error.
        """
        raise TypeError('cannot convert to a nodeset')

    def evaluate(self, context):
        # Lazily generate the Python function for the expression.
        compiler = xpathcompiler(context)
        self.compile(compiler)
        self.evaluate = compiler.compile('evaluate',
                                         docstring=unicode(self))
        return self.evaluate(context)

    def evaluate_as_boolean(self, context):
        # Lazily generate the Python function for the expression.
        compiler = xpathcompiler(context)
        self.compile_as_boolean(compiler)
        self.evaluate_as_boolean = compiler.compile('evaluate_as_boolean',
                                                    docstring=unicode(self))
        return self.evaluate_as_boolean(context)

    def evaluate_as_number(self, context):
        # Lazily generate the Python function for the expression.
        compiler = xpathcompiler(context)
        self.compile_as_number(compiler)
        self.evaluate_as_number = compiler.compile('evaluate_as_number',
                                                   docstring=unicode(self))
        return self.evaluate_as_number(context)

    def evaluate_as_string(self, context):
        # Lazily generate the Python function for the expression.
        compiler = xpathcompiler(context)
        self.compile_as_string(compiler)
        self.evaluate_as_string = compiler.compile('evaluate_as_string',
                                                   docstring=unicode(self))
        return self.evaluate_as_string(context)

    def evaluate_as_nodeset(self, context):
        # Lazily generate the Python function for the expression.
        compiler = xpathcompiler(context)
        self.compile_as_nodeset(compiler)
        self.evaluate_as_nodeset = compiler.compile('evaluate_as_nodeset',
                                                    docstring=unicode(self))
        return self.evaluate_as_nodeset(context)

    def __str__(self):
        raise NotImplementedError('subclass %r must override' %
                                  self.__class__.__name__)

    def __repr__(self):
        ptr = id(self)
        if ptr < 0: ptr += 0x100000000L
        return '<%s at 0x%x: %s>' % (self.__class__.__name__, ptr, self)
