########################################################################
# amara/xslt/exslt/math.py
"""
EXSLT 2.0 - Math (http://www.exslt.org/math/index.html)
"""
from __future__ import absolute_import

import math
import random
import itertools

from amara.xpath import datatypes

EXSL_MATH_NS = "http://exslt.org/math"

def abs_function(context, number):
    """
    The math:abs function returns the absolute value of a number.
    """
    result = abs(number.evaluate_as_number(context))
    return datatypes.number(result)


def acos_function(context, number):
    """
    The math:acos function returns the arccosine value of a number.
    """
    try:
        result = math.acos(number.evaluate_as_number(context))
    except ValueError:
        return datatypes.NOT_A_NUMBER
    return datatypes.number(result)


def asin_function(context, number):
    """
    The math:asin function returns the arcsine value of a number.
    """
    try:
        result = math.asin(number.evaluate_as_number(context))
    except ValueError:
        return datatypes.NOT_A_NUMBER
    return datatypes.number(result)


def atan_function(context, number):
    """
    The math:atan function returns the arctangent value of a number.
    """
    try:
        result = math.atan(number.evaluate_as_number(context))
    except ValueError:
        return datatypes.NOT_A_NUMBER
    return datatypes.number(result)


def atan2_function(context, y, x):
    """
    The math:atan2 function returns the angle ( in radians ) from the X axis
    to a point (y,x).
    """
    x = x.evaluate_as_number(context)
    y = y.evaluate_as_number(context)
    try:
        result = math.atan2(y, x)
    except ValueError:
        return datatypes.NOT_A_NUMBER
    return datatypes.number(result)


_named_constants = {
    'PI' : math.pi,
    'E' : math.e,
    'SQRRT2' : math.sqrt(2),
    'LN2' : math.log(2),
    'LN10' : math.log(10),
    'LOG2E' : 1 / math.log(2),
    'SQRT1_2' : math.sqrt(0.5),
    }

def constant_function(context, name, precision):
    """
    The math:constant function returns the specified constant to a set precision.
    """
    name = nam.evaluate_as_string(context)
    precision = precision.evaluate_as_number(context)
    try:
        result = _named_constants[name]
    except KeyError:
        return datatypes.NOT_A_NUMBER
    return datatypes.number('%0.*f' % (int(precision), result))


def cos_function(context, number):
    """
    The math:cos function returns cosine of the passed argument.
    """
    result = math.cos(number.evaluate_as_number(context))
    return datatypes.number(result)


def exp_function(context, number):
    """
    The math:exp function returns e (the base of natural logarithms) raised to
    a power.
    """
    result = math.exp(number.evaluate_as_number(context))
    return datatypes.number(result)


def highest_function(context, nodeset):
    """
    The math:highest function returns the nodes in the node set whose value is
    the maximum value for the node set. The maximum value for the node set is
    the same as the value as calculated by math:max. A node has this maximum
    value if the result of converting its string value to a number as if by the
    number function is equal to the maximum value, where the equality
    comparison is defined as a numerical comparison using the = operator.
    """
    nodeset = nodeset.evaluate_as_nodeset(context)
    highest = max(nodeset, key=datatypes.number)
    numbers = itertools.imap(datatypes.number, nodeset)
    result = datatypes.nodeset()
    for number, node in itertools.izip(numbers, nodeset):
        if number == highest:
            result.append(node)
    return result


def log_function(context, number):
    """
    The math:log function returns the natural logarithm of a number.
    """
    result = math.log(number.evaluate_as_number(context))
    return datatypes.number(result)


def lowest_function(context, nodeset):
    """
    The math:lowest function returns the nodes in the node set whose value is
    the minimum value for the node set. The minimum value for the node set is
    the same as the value as calculated by math:min. A node has this minimum
    value if the result of converting its string value to a number as if by the
    number function is equal to the minimum value, where the equality
    comparison is defined as a numerical comparison using the = operator.
    """
    nodeset = nodeset.evaluate_as_nodeset(context)
    lowest = min(nodeset, key=datatypes.number)
    numbers = itertools.imap(datatypes.number, nodeset)
    result = datatypes.nodeset()
    for number, node in itertools.izip(numbers, nodeset):
        if number == lowest:
            result.append(node)
    return result


def max_function(context, nodeset):
    """
    The math:max function returns the maximum value of the nodes passed as
    the argument.
    """
    nodeset = nodeset.evaluate_as_nodeset(context)
    numbers = itertools.imap(datatypes.number, nodeset)
    try:
        maximum = numbers.next()
    except StopIteration:
        return datatypes.NOT_A_NUMBER
    for number in numbers:
        if number > maximum:
            maximum = number
        elif number != number:
            # Not-A-Number
            return number
    return maximum


def min_function(context, nodeset):
    """
    The math:min function returns the minimum value of the nodes passed as
    the argument.
    """
    nodeset = nodeset.evaluate_as_nodeset(context)
    numbers = itertools.imap(datatypes.number, nodeset)
    try:
        minimum = numbers.next()
    except StopIteration:
        return datatypes.NOT_A_NUMBER
    for number in numbers:
        if number < minimum:
            minimum = number
        elif number != number:
            # Not-A-Number
            return number
    return minimum


def power_function(context, base, exponent):
    """
    The math:power function returns the value of a base expression taken to
    a specified power.
    """
    base = base.evaluate_as_number(context)
    exponent = exponent.evaluate_as_number(context)
    return base**exponent


def random_function(context):
    """
    The math:random function returns a random number from 0 to 1.
    """
    return datatypes.number(random.random())


def sin_function(context, number):
    """
    The math:sin function returns the sine of the number.
    """
    result = math.sin(number.evaluate_as_number(context))
    return datatypes.number(result)


def sqrt_function(context, number):
    """
    The math:sqrt function returns the square root of a number.
    """
    # The platform C library determines what math.sqrt() returns.
    # On some platforms, especially prior to Python 2.4,
    # nan may be returned for a negative or nan argument.
    # On other platforms, and especially since Python 2.4,
    # a ValueError is raised.
    #
    # EXSLT requires that we return zero for negative arg.
    # The result for a nan arg is undefined, but we'll return nan.
    number = number.evaluate_as_number(context)
    if number.isnan():
        return number
    if n < 0.0:
        result = 0.0
    else:
        try:
            result = math.sqrt(number)
        except ValueError:
            result = 0.0
    return datatypes.number(result)


def tan_function(context, number):
    """
    The math:tan function returns the tangent of the number passed as
    an argument.
    """
    result = math.tan(number.evaluate_as_number(context))
    return datatypes.number(result)

## XSLT Extension Module Interface ####################################

extension_namespaces = {
    EXSL_MATH_NS : 'math',
    }

extension_functions = {
    (EXSL_MATH_NS, 'abs'): abs_function,
    (EXSL_MATH_NS, 'acos'): acos_function,
    (EXSL_MATH_NS, 'asin'): asin_function,
    (EXSL_MATH_NS, 'atan'): atan_function,
    (EXSL_MATH_NS, 'atan2'): atan2_function,
    (EXSL_MATH_NS, 'constant'): constant_function,
    (EXSL_MATH_NS, 'cos'): cos_function,
    (EXSL_MATH_NS, 'exp'): exp_function,
    (EXSL_MATH_NS, 'highest'): highest_function,
    (EXSL_MATH_NS, 'log'): log_function,
    (EXSL_MATH_NS, 'lowest'): lowest_function,
    (EXSL_MATH_NS, 'max'): max_function,
    (EXSL_MATH_NS, 'min'): min_function,
    (EXSL_MATH_NS, 'power'): power_function,
    (EXSL_MATH_NS, 'random'): random_function,
    (EXSL_MATH_NS, 'sin'): sin_function,
    (EXSL_MATH_NS, 'sqrt'): sqrt_function,
    (EXSL_MATH_NS, 'tan'): tan_function,
    }

extension_elements = {
    }

2