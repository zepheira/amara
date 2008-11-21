#######################################################################
# amara/xpath/functioncalls.py
"""
XPath expression nodes that evaluate function calls.
"""

import inspect

from amara.xpath import XPathError
from amara.xpath import datatypes
from amara.xpath.expressions import expression

class function_call(expression):
    """
    An object representing a function call expression
    (XPath 1.0 grammar production 16: FunctionCall)
    """
    _builtins = {}

    _name = None
    _args = None

    def __new__(cls, name, args):
        if name in cls._builtins:
            cls = cls._builtins[name]
        elif 1:
            cls = extension_function
        elif not args:
            cls = function_call0
        else:
            nargs = len(args)
            if nargs == 1:
                cls = function_call1
            elif nargs == 2:
                cls = function_call2
            elif nargs == 3:
                cls = function_call3
            else:
                cls = function_callN
        return object.__new__(cls)

    def compile(self, compiler):
        # Load the callable object
        compiler.emit('LOAD_CONST', self)
        compiler.emit('LOAD_ATTR', 'evaluate')
        # Build the argument(s)
        compiler.emit('LOAD_FAST', 'context')
        # Call it!
        compiler.emit('CALL_FUNCTION', 1)
        return

    def compile_as_boolean(self, compiler):
        # Load the callable object
        compiler.emit('LOAD_CONST', self)
        compiler.emit('LOAD_ATTR', 'evaluate_as_boolean')
        # Build the argument(s)
        compiler.emit('LOAD_FAST', 'context')
        # Call it!
        compiler.emit('CALL_FUNCTION', 1)
        return

    def compile_as_number(self, compiler):
        # Load the callable object
        compiler.emit('LOAD_CONST', self)
        compiler.emit('LOAD_ATTR', 'evaluate_as_number')
        # Build the argument(s)
        compiler.emit('LOAD_FAST', 'context')
        # Call it!
        compiler.emit('CALL_FUNCTION', 1)
        return

    def compile_as_string(self, compiler):
        # Load the callable object
        compiler.emit('LOAD_CONST', self)
        compiler.emit('LOAD_ATTR', 'evaluate_as_string')
        # Build the argument(s)
        compiler.emit('LOAD_FAST', 'context')
        # Call it!
        compiler.emit('CALL_FUNCTION', 1)
        return

    def compile_as_nodeset(self, compiler):
        # Load the callable object
        compiler.emit('LOAD_CONST', self)
        compiler.emit('LOAD_ATTR', 'evaluate_as_nodeset')
        # Build the argument(s)
        compiler.emit('LOAD_FAST', 'context')
        # Call it!
        compiler.emit('CALL_FUNCTION', 1)
        return

    def evaluate_as_boolean(self, context):
        return datatypes.boolean(self.evaluate(context))

    def evaluate_as_number(self, context):
        return datatypes.number(self.evaluate(context))

    def evaluate_as_string(self, context):
        return datatypes.string(self.evaluate(context))

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)
        for arg in self._args:
            arg.pprint(indent + '  ', stream)

    def __str__(self):
        func_name = self._name[0] and u':'.join(self._name) or self._name[1]
        func_name = func_name.encode('unicode_escape')
        arg_spec = ', '.join(map(str, self._args))
        return '%s(%s)' % (func_name, arg_spec)


class extension_function(function_call):

    _func = None

    def __init__(self, name, args):
        assert ':' in name, 'Extension functions must have a prefix'
        self._name = name.split(':', 1)
        self._args = tuple(args)

    def compile(self, compiler):
        prefix, local = self._name
        try:
            expanded = (compiler.namespaces[prefix], local)
        except KeyError:
            raise XPathError(XPathError.UNDEFINED_PREFIX, prefix=prefix)
        try:
            func = compiler.functions[expanded]
        except KeyError:
            raise XPathError(XPathError.UNDEFINED_FUNCTION,
                             function=u':'.join(self._name))

        # If this is a Python function, we can verify the arguments. If it is
        # just any callable, no verification will happen and TypeErrors will
        # bubble up to the user as-is.
        if inspect.isfunction(func):
            args, varargs, kwarg = inspect.getargs(func.func_code)
            argcount = len(self._args)
            maxargs = len(args) - 1 # don't count the `context` argument
            if func.func_defaults:
                minargs = maxargs - len(func.func_defaults)
            else:
                minargs = maxargs
            if argcount > maxargs and not varargs:
                if maxargs == 0:
                    name = u':'.join(self._name).encode('unicode_escape')
                    raise XPathError(XPathError.ARGCOUNT_NONE,
                                     function=name, total=argcount)
                elif func.func_defaults:
                    name = u':'.join(self._name).encode('unicode_escape')
                    raise XPathError(XPathError.ARGCOUNT_ATMOST,
                                     function=name, count=maxargs,
                                     total=argcount)
                else:
                    name = u':'.join(self._name).encode('unicode_escape')
                    raise XPathError(XPathError.ARGCOUNT_EXACT,
                                     function=name, count=maxargs,
                                     total=argcount)
            elif argcount < minargs:
                if varargs or func.func_defaults:
                    name = u':'.join(self._name).encode('unicode_escape')
                    raise XPathError(XPathError.ARGCOUNT_ATLEAST,
                                     function=name, count=minargs,
                                     total=argcount)
                else:
                    name = u':'.join(self._name).encode('unicode_escape')
                    raise XPathError(XPathError.ARGCOUNT_EXACT,
                                     function=name, count=minargs,
                                     total=argcount)
        
        # Load the function
        if getattr(func, 'nocache', False):
            if __debug__:
                name = u':'.join(self._name).encode('unicode_escape')
                def dynamic_function(context):
                    try:
                        return context.functions[expanded]
                    except KeyError:
                        raise XPathError(XPathError.UNDEFINED_FUNCTION, 
                                         name=name)
                compiler.emit('LOAD_CONST', dynamic_function,
                              'LOAD_FAST', 'context',
                              'CALL_FUNCTION', 1)
            else:
                # Note, this assumes that the function will not be *deleted* 
                # from the function mapping, just replaced.
                compiler.emit('LOAD_FAST', 'context',
                              'LOAD_ATTR', 'functions',
                              'LOAD_CONST', expanded,
                              'BINARY_SUBSCRIPT')
        else:
            compiler.emit('LOAD_CONST', func)
        # Build the argument(s)
        compiler.emit('LOAD_FAST', 'context')
        for arg in self._args:
            compiler.emit('LOAD_CONST', arg)
        # Call it!
        compiler.emit('CALL_FUNCTION', 1 + len(self._args))
        return

    def evaluate_as_nodeset(self, context):
        nodes = self.evaluate(context)
        try:
            nodes.sort()
        except AttributeError:
            raise TypeError("%r must be a nodeset, not %s" %
                            (self._expression, type(nodes).__name__))
        return nodes

    def __getstate__(self):
        state = vars(self).copy()
        del state['_func']
        return state
