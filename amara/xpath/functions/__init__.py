#######################################################################
# amara/xpath/functions/__init__.py
"""
XPath expression nodes that evaluate function calls.
"""

from amara.xpath import XPathError
from amara.xpath import datatypes
from amara.xpath.expressions.functioncalls import function_call

__all__ = ['builtin_function', 'extension_function']

class builtin_function(function_call):
    """
    An object representing a function call of a core function.
    (XPath 1.0 grammar production 16: FunctionCall
     and XPath 1.0 section 4: Core Function Library)
    """

    name = None
    return_type = datatypes.xpathobject
    arguments = (Ellipsis,)
    defaults = ()

    class __metaclass__(function_call.__metaclass__):
        if __debug__:
            def __new__(cls, name, bases, namespace):
                assert 'name' in namespace
                assert 'return_type' in namespace
                assert 'arguments' in namespace
                assert isinstance(namespace['arguments'], tuple)
                assert isinstance(namespace.get('defaults', ()), tuple)
                return type.__new__(cls, name, bases, namespace)

        def __init__(cls, name, bases, namespace):
            function_call._builtins[cls.name] = cls

    def __init__(self, name, args):
        args = tuple(args)
        argcount = len(args)
        maxargs = len(self.arguments)
        if maxargs and self.arguments[-1] is Ellipsis:
            varargs = True
            maxargs -= 1
        else:
            varargs = False
        minargs = maxargs - len(self.defaults)
        if argcount > maxargs and not varargs:
            if maxargs == 0:
                raise XpathError(XPathError.ARGCOUNT_NONE,
                                 function=name, total=argcount)
            elif self.defaults:
                raise XPathError(XPathError.ARGCOUNT_ATMOST,
                                 function=name, count=maxargs,
                                 total=argcount)
            else:
                raise XPathError(XPathError.ARGCOUNT_EXACT,
                                 function=name, count=maxargs,
                                 total=argcount)
        elif argcount < minargs:
            if self.defaults or varargs:
                raise XPathError(XPathError.ARGCOUNT_ATLEAST,
                                 function=name, count=minargs,
                                 total=argcount)
            else:
                raise XPathError(XPathError.ARGCOUNT_EXACT,
                                 function=name, count=minargs,
                                 total=argcount)
        # Add default argument values, if needed
        if argcount < maxargs:
            args += self.defaults[:(maxargs - argcount)]
        self._name = (None, self.name)
        self._args = args
        return


class function_callN(function_call):

    _func = None

    def __getstate__(self):
        state = vars(self).copy()
        del state['_func']
        return state

    def _get_function(self, context):
        prefix, local = self._name
        if prefix:
            try:
                expanded = (context.processorNss[prefix], local)
            except KeyError:
                raise XPathError(XPathError.UNDEFINED_PREFIX, prefix=prefix)
        else:
            expanded = self._name
        try:
            func = context.functions[expanded]
        except KeyError:
            func_name = prefix and u':'.join(self._name) or local
            func_name = func_name.encode('unicode_escape')
            raise XPathError(XPathError.UNDEFINED_FUNCTION, name=func_name)
        if 'nocache' not in func.__dict__ or not func.nocache:
            self._func = func
        return func

    def _argument_error(self):
        if not inspect.isfunction(self._func):
            # We can only check for argument errors with Python functions
            return

        func_name = self._name[0] and u':'.join(self._name) or self._name[1]
        func_name = func_name.encode('unicode_escape')
        argcount = len(self._args)

        args, vararg, kwarg = inspect.getargs(self._func.func_code)
        defaults = self._func.func_defaults or ()

        # Don't count the context parameter in argument count
        maxargs = len(args) - 1
        minargs = maxargs - len(defaults)

        if argcount > maxargs and not varargs:
            if maxargs == 0:
                raise XpathError(XPathError.ARGCOUNT_NONE,
                                 function=func_name, total=argcount)
            elif defaults:
                raise XPathError(XPathError.ARGCOUNT_ATMOST,
                                 function=func_name, count=maxargs,
                                 total=argcount)
            else:
                raise XPathError(XPathError.ARGCOUNT_EXACT,
                                 function=func_name, count=maxargs,
                                 total=argcount)
        elif argcount < minargs:
            if defaults or varargs:
                raise XPathError(XPathError.ARGCOUNT_ATLEAST,
                                 function=func_name, count=minargs,
                                 total=argcount)
            else:
                raise XPathError(XPathError.ARGCOUNT_EXACT,
                                 function=func_name, count=minargs,
                                 total=argcount)
        # Not an error with arg counts for this function, use current error
        return

    def evaluate(self, context):
        """Returns the result of calling the function"""
        args = [ arg.evaluate(context) for arg in self._args ]
        func = self._func or self._get_function(context)
        try:
            result = func(context, *args)
        except TypeError:
            self._argument_error()
            # use existing exception (empty raise keeps existing backtrace)
            raise

        #Expensive assert contributed by Adam Souzis.
        #No effect on Python running in optimized mode,
        #But would mean significant slowdown for developers, so disabled by default
        #assert not isinstance(result, list) or len(result) == len(Set.Unique(result))
        return result

    def evaluate_as_nodeset(self, context):
        nodes = self.evaluate(context)
        try:
            nodes.sort()
        except AttributeError:
            raise TypeError("%r must be a nodeset, not %s" %
                            (self._expression, type(nodes).__name__))
        return nodes


# Load the built-in functions
def __bootstrap__(namespace):
    global __bootstrap__
    from amara.xpath.functions import nodesets, strings, booleans, numbers
    for module in (nodesets, strings, booleans, numbers):
        for name in getattr(module, '__all__', ()):
            namespace[name] = getattr(module, name)
            # Add the functions to this module's exported objects
            __all__.append(name)
    del __bootstrap__
__bootstrap__(locals())