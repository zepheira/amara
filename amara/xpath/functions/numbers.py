########################################################################
# amara/xpath/functions/numbers.py
"""
The implementation of the core numeric functions from XPath 1.0.
"""
import math

from amara.xpath import datatypes
from amara.xpath.functions import builtin_function

__all__ = ('number_function', 'sum_function', 'floor_function', 
           'ceiling_function', 'round_function')


class number_function(builtin_function):
    """Function: <number> number(<object>?)"""
    name = 'number'
    arguments = (datatypes.xpathobject,)
    defaults = (None,)
    return_type = datatypes.number

    def evaluate_as_number(self, context):
        arg0, = self._args
        if arg0 is None:
            return datatypes.number(context.node)
        return arg0.evaluate_as_number(context)
    evaluate = evaluate_as_number


class sum_function(builtin_function):
    """Function: <number> sum(<node-set>)"""
    name = 'sum'
    arguments = (datatypes.nodeset,)
    return_type = datatypes.number

    def evaluate_as_number(self, context):
        arg0, = self._args
        arg0 = arg0.evaluate_as_nodeset(context)
        return datatypes.number(sum(map(datatypes.number, arg0)))
    evaluate = evaluate_as_number


class floor_function(builtin_function):
    """Function: <number> floor(<number>)"""
    name = 'floor'
    arguments = (datatypes.number,)
    return_type = datatypes.number

    def evaluate_as_number(self, context):
        arg0, = self._args
        arg0 = arg0.evaluate_as_number(context)
        # a "normal" number is neither zero, NaN, nor infinity
        if arg0.isnormal():
            return datatypes.number(math.floor(arg0))
        return arg0
    evaluate = evaluate_as_number


class ceiling_function(builtin_function):
    """Function: <number> ceiling(<number>)"""
    name = 'ceiling'
    arguments = (datatypes.number,)
    return_type = datatypes.number

    def evaluate_as_number(self, context):
        arg0, = self._args
        arg0 = arg0.evaluate_as_number(context)
        # a "normal" number is neither zero, NaN, nor infinity
        if arg0.isnormal():
            return datatypes.number(math.ceil(arg0))
        return arg0
    evaluate = evaluate_as_number


class round_function(builtin_function):
    """Function: <number> round(<number>)"""
    name = 'round'
    arguments = (datatypes.number,)
    return_type = datatypes.number

    def evaluate_as_number(self, context):
        arg0, = self._args
        arg0 = arg0.evaluate_as_number(context)
        # a "normal" number is neither zero, NaN, nor infinity
        if arg0.isnormal():
            # Round towards positive infinity when there are two possibilities
            if arg0 % 1.0 == 0.5:
                round = math.ceil
            else:
                round = math.floor
            return datatypes.number(round(arg0))
        return arg0
    evaluate = evaluate_as_number
