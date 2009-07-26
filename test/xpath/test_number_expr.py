#!/usr/bin/env python
from amara.xpath import datatypes, context
from amara.xpath.expressions.basics import number_literal, string_literal
from amara.xpath.expressions.numbers import additive_expr, multiplicative_expr, unary_expr

from test_expressions import (
    # expression TestCase
    base_expression,
    # IEEE 754 "special" numbers as expressions
    NOT_A_NUMBER, POSITIVE_INFINITY, NEGATIVE_INFINITY,

    # for the context
    DOC,
    )

default_context = context(DOC, 1, 1)


def _run_test(args, result, expected):
    assert isinstance(result, datatypes.number), (args, result, expected)
    if hasattr(expected, "isnan") and expected.isnan():
        assert result.isnan()
        return
    assert result == expected, (args, result, expected)

def test_additive_expr():
    for args, expected in (
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
        ):
        result = additive_expr(*args).evaluate_as_number(default_context)
        _run_test(args, result, expected)

def test_multiplicative_expr():
    for args, expected in (
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
        ):
        result = multiplicative_expr(*args).evaluate_as_number(default_context)
        _run_test(args, result, expected)


def test_unary_expr():
    for args, expected in (
        ((number_literal('5'),), -5.0),
        ((number_literal('-2'),), 2.0),
        ((string_literal('5'),), -5.0),
        ((string_literal('-2'),), 2.0),
        ):
        result = unary_expr(*args).evaluate_as_number(default_context)
        _run_test(args, result, expected)

    

if __name__ == '__main__':
    raise SystemExit("Use nosetests")
