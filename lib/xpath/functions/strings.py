########################################################################
# amara/xpath/functions/strings.py
"""
The implementation of the core sting functions from XPath 1.0.
"""
import itertools

from amara.xpath import datatypes
from amara.xpath.functions import builtin_function

__all__ = (
    'string_function', 'concat_function', 'starts_with_function',
    'contains_function', 'substring_before_function', 
    'substring_after_function', 'substring_function', 
    'string_length_function', 'normalize_space_function',
    'translate_function',
    )

class string_function(builtin_function):
    """Function: <string> string(<object>?)"""
    name = 'string'
    arguments = (datatypes.xpathobject,)
    defaults = (None,)
    return_type = datatypes.string

    def evaluate_as_string(self, context):
        arg0, = self._args
        if arg0 is None:
            return datatypes.string(context.node)
        return arg0.evaluate_as_string(context)
    evaluate = evaluate_as_string


class concat_function(builtin_function):
    """Function: <string> concat(<string>, <string>, ...)"""
    name = 'concat'
    arguments = (datatypes.string, datatypes.string, Ellipsis)
    return_type = datatypes.string

    def evaluate_as_string(self, context):
        args = (arg.evaluate_as_string(context) for arg in self._args)
        return datatypes.string(u''.join(args))
    evaluate = evaluate_as_string


class starts_with_function(builtin_function):
    """Function: <boolean> starts-with(<string>, <string>)"""
    name = 'starts-with'
    arguments = (datatypes.string, datatypes.string)
    return_type = datatypes.boolean

    def evaluate_as_boolean(self, context):
        outer, inner = self._args
        outer = outer.evaluate_as_string(context)
        inner = inner.evaluate_as_string(context)
        if not inner or outer[:len(inner)] == inner:
            return datatypes.TRUE
        return datatypes.FALSE
    evaluate = evaluate_as_boolean


class contains_function(builtin_function):
    """Function: <boolean> contains(<string>, <string>)"""
    name = 'contains'
    arguments = (datatypes.string, datatypes.string)
    return_type = datatypes.boolean

    def evaluate_as_boolean(self, context):
        outer, inner = self._args
        outer = outer.evaluate_as_string(context)
        inner = inner.evaluate_as_string(context)
        return datatypes.TRUE if inner in outer else datatypes.FALSE
    evaluate = evaluate_as_boolean


class substring_before_function(builtin_function):
    """Function: <string> substring-before(<string>, <string>)"""
    name = 'substring-before'
    arguments = (datatypes.string, datatypes.string)
    return_type = datatypes.string

    def evaluate_as_string(self, context):
        outer, inner = self._args
        outer = outer.evaluate_as_string(context)
        inner = inner.evaluate_as_string(context)
        index = outer.find(inner)
        if index == -1:
            return datatypes.EMPTY_STRING
        return datatypes.string(outer[:index])
    evaluate = evaluate_as_string


class substring_after_function(builtin_function):
    """Function: <string> substring-after(<string>, <string>)"""
    name = 'substring-after'
    arguments = (datatypes.string, datatypes.string)
    return_type = datatypes.string

    def evaluate_as_string(self, context):
        outer, inner = self._args
        outer = outer.evaluate_as_string(context)
        inner = inner.evaluate_as_string(context)
        if not inner:
            return datatypes.EMPTY_STRING
        index = outer.find(inner)
        if index == -1:
            return datatypes.EMPTY_STRING
        return datatypes.string(outer[index+len(inner):])
    evaluate = evaluate_as_string


class substring_function(builtin_function):
    """Function: <string> substring(<string>, <number>, <number>?)"""
    name = 'substring'
    arguments = (datatypes.string, datatypes.number, datatypes.number)
    defaults = (None,)
    return_type = datatypes.string

    def evaluate_as_string(self, context):
        string, start, length = self._args
        string = string.evaluate_as_string(context)
        start = start.evaluate_as_number(context)

        # start == NaN: spec doesn't say; assume no substring to return
        # start == +Inf or -Inf: no substring to return
        if not start.isfinite():
            return datatypes.EMPTY_STRING

        # start is finite, safe for int() and round().
        start = int(round(start))
        # convert to 0-based index for python string slice
        if start < 1:
            startidx = 0
        else:
            startidx = start - 1

        # length undefined: return chars startidx to end
        if length is None:
            return datatypes.string(string[startidx:])

        length = length.evaluate_as_number(context)
        if not length.isfinite():
            # length == +Inf: return chars startidx to end
            if length > 0:
                assert length.isinf()
                return datatypes.string(string[startidx:])
            # length == NaN: spec doesn't say; assume no substring to return
            # length == -Inf: no substring to return
            return datatypes.EMPTY_STRING

        # length is finite, safe for int() and round().
        length = int(round(length))

        # return value must end before position (start+length)
        # which is (start+length-1) in 0-based index
        endidx = start + length - 1
        if endidx < startidx:
            return datatypes.EMPTY_STRING
        return datatypes.string(string[startidx:endidx])
    evaluate = evaluate_as_string


class string_length_function(builtin_function):
    """Function: <number> string-length(<string>?)"""
    name = 'string-length'
    arguments = (datatypes.string,)
    defaults = (None,)
    return_type = datatypes.number

    def evaluate_as_number(self, context):
        arg0, = self._args
        if arg0 is None:
            string = datatypes.string(context.node)
        else:
            string = arg0.evaluate_as_string(context)
        return datatypes.number(len(string))
    evaluate = evaluate_as_number


class normalize_space_function(builtin_function):
    """Function: <string> normalize-space(<string>?)"""
    name = 'normalize-space'
    arguments = (datatypes.string,)
    defaults = (None,)
    return_type = datatypes.string

    def evaluate_as_string(self, context):
        arg0, = self._args
        if arg0 is None:
            string = datatypes.string(context.node)
        else:
            string = arg0.evaluate_as_string(context)
        return datatypes.string(u' '.join(string.split()))
    evaluate = evaluate_as_string


class translate_function(builtin_function):
    """Function: <string> translate(<string>, <string>, <string>)"""
    name = 'translate'
    arguments = (datatypes.string, datatypes.string, datatypes.string)
    return_type = datatypes.string

    def evaluate_as_string(self, context):
        arg0, arg1, arg2 = self._args
        source = arg0.evaluate_as_string(context)
        fromchars = arg1.evaluate_as_string(context)
        tochars = arg2.evaluate_as_string(context)
        tochars = itertools.chain(tochars, itertools.repeat(u''))
 
        transmap = {}
        for src, dst in itertools.izip(fromchars, tochars):
            if src not in transmap:
                transmap[src] = dst
        chars = list(source)
        for idx, ch in enumerate(chars):
            if ch in transmap:
                chars[idx] = transmap[ch]
        return datatypes.string(u''.join(chars))
    evaluate = evaluate_as_string