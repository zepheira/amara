#!/usr/bin/env python
from amara.lib import testsupport
from amara.xpath import datatypes
from amara.xpath.expressions.basics import number_literal, string_literal

from test_expressions import (
    # expression TestCase
    test_expression,
    # IEEE 754 "special" numbers as expressions
    NOT_A_NUMBER, POSITIVE_INFINITY, NEGATIVE_INFINITY
    )


class test_number_expr(test_expression):
    module_name = 'amara.xpath.expressions.numbers'
    evaluate_method = 'evaluate_as_number'
    return_type = datatypes.number


class test_additive_expr(test_number_expr):
    class_name = 'additive_expr'
    test_cases = [
        ((number_literal('5'), '+', number_literal('2')), 7.0),
        ((number_literal('3'), '+', number_literal('-2')), 1.0),
        ((string_literal('5'), '+', string_literal('2')), 7.0),
        ((string_literal('3'), '+', string_literal('-2')), 1.0),
        ((number_literal('5'), '-', number_literal('2')), 3.0),
        ((number_literal('3'), '-', number_literal('-2')), 5.0),
        ((string_literal('5'), '-', string_literal('2')), 3.0),
        ((string_literal('3'), '-', string_literal('-2')), 5.0),
        # IEEE 754 says:
        #   Infinity + Infinity = Infinity
        #   Infinity - Infinity = NaN
        ((POSITIVE_INFINITY, '+', POSITIVE_INFINITY), datatypes.POSITIVE_INFINITY),
        ((POSITIVE_INFINITY, '-', POSITIVE_INFINITY), datatypes.NOT_A_NUMBER),
        ]


class test_multiplicative_expr(test_number_expr):
    class_name = 'multiplicative_expr'
    test_cases = [
        ((number_literal('-5'), '*', number_literal('2')), -10.0),
        ((number_literal('-4'), '*', number_literal('-2')), 8.0),
        ((number_literal('0'), '*', number_literal('2')), 0.0),
        ((string_literal('-5'), '*', string_literal('2')), -10.0),
        ((string_literal('-4'), '*', string_literal('-2')), 8.0),
        ((string_literal('0'), '*', string_literal('2')), 0.0),
        ((string_literal('1'), '*', string_literal('1')), 1.0),
        ((string_literal('3.1415926535'), '*', string_literal('1')), 3.1415926535),
        ((string_literal(''), '*', string_literal('1')), datatypes.NOT_A_NUMBER),
        ((string_literal('hi'), '*', string_literal('1')), datatypes.NOT_A_NUMBER),
        ((string_literal('inf'), '*', string_literal('1')), datatypes.NOT_A_NUMBER),
        ((string_literal(u'\u2022 = middle dot'), '*', string_literal('1')), datatypes.NOT_A_NUMBER),
        ((number_literal('0'), 'div', number_literal('2')), 0.0),
        ((number_literal('-5'), 'div', number_literal('2')), -2.5),
        ((number_literal('-4'), 'div', number_literal('-2')), 2.0),
        ((string_literal('0'), 'div', string_literal('2')), 0.0),
        ((string_literal('1'), 'div', string_literal('1')), 1.0),
        ((string_literal('-5'), 'div', string_literal('2')), -2.5),
        ((string_literal('-4'), 'div', string_literal('-2')), 2.0),
        ((string_literal('0'), 'div', string_literal('0')), datatypes.NOT_A_NUMBER),
        ((string_literal('1'), 'div', string_literal('0')), datatypes.POSITIVE_INFINITY),
        ((string_literal('-1'), 'div', string_literal('0')), datatypes.NEGATIVE_INFINITY),
        ((number_literal('0'), 'mod', number_literal('2')), 0.0),
        ((number_literal('5'), 'mod', number_literal('2')), 1.0),
        ((number_literal('5'), 'mod', number_literal('-2')), -1.0),
        ((number_literal('-5'), 'mod', number_literal('2')), 1.0),
        ((number_literal('-5'), 'mod', number_literal('-2')), -1.0),
        ((string_literal('0'), 'mod', string_literal('2')), 0.0),
        ((string_literal('5'), 'mod', string_literal('2')), 1.0),
        ((string_literal('5'), 'mod', string_literal('-2')), -1.0),
        ((string_literal('-5'), 'mod', string_literal('2')), 1.0),
        ((string_literal('-5'), 'mod', string_literal('-2')), -1.0),
        # IEEE 754 says:
        #   +-Infinity * +-Infinity = +-Infinity
        #   +-Infinity * 0 = NaN
        #   n div +-Infinity = 0
        #   +-nonzero div 0 = +-Infinity
        #   +-Infinity div +-Infinity = NaN
        #   +-0 div +-0 = NaN
        ((POSITIVE_INFINITY, '*', POSITIVE_INFINITY), datatypes.POSITIVE_INFINITY),
        ((NEGATIVE_INFINITY, '*', NEGATIVE_INFINITY), datatypes.POSITIVE_INFINITY),
        ((POSITIVE_INFINITY, '*', NEGATIVE_INFINITY), datatypes.NEGATIVE_INFINITY),
        ((POSITIVE_INFINITY, '*', number_literal('0')), datatypes.NOT_A_NUMBER),
        ((NEGATIVE_INFINITY, '*', number_literal('0')), datatypes.NOT_A_NUMBER),
        ((number_literal('0'), 'div', number_literal('0')), datatypes.NOT_A_NUMBER),
        ((number_literal('1'), 'div', number_literal('0')), datatypes.POSITIVE_INFINITY),
        ((number_literal('-1'), 'div', number_literal('0')), datatypes.NEGATIVE_INFINITY),
        ((number_literal('0'), 'div', POSITIVE_INFINITY), 0.0),
        ((number_literal('1'), 'div', POSITIVE_INFINITY), 0.0),
        ((number_literal('-1'), 'div', POSITIVE_INFINITY), 0.0),
        ((number_literal('0'), 'div', NEGATIVE_INFINITY), 0.0),
        ((number_literal('1'), 'div', NEGATIVE_INFINITY), 0.0),
        ((number_literal('-1'), 'div', NEGATIVE_INFINITY), 0.0),
        ((POSITIVE_INFINITY, 'div', POSITIVE_INFINITY), datatypes.NOT_A_NUMBER),
        ((POSITIVE_INFINITY, 'div', NEGATIVE_INFINITY), datatypes.NOT_A_NUMBER),
        ((NEGATIVE_INFINITY, 'div', NEGATIVE_INFINITY), datatypes.NOT_A_NUMBER),
        ((NEGATIVE_INFINITY, 'div', POSITIVE_INFINITY), datatypes.NOT_A_NUMBER),
        ]


class test_unary_expr(test_number_expr):
    class_name = 'unary_expr'
    test_cases = [
        ((number_literal('5'),), -5.0),
        ((number_literal('-2'),), 2.0),
        ((string_literal('5'),), -5.0),
        ((string_literal('-2'),), 2.0),
        ]
    

if __name__ == '__main__':
    testsupport.test_main()

