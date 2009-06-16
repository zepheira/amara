#!/usr/bin/env python
from amara import tree
from amara.xpath import datatypes
from amara.xpath.expressions.basics import string_literal, number_literal
from amara.xpath.expressions.booleans import and_expr, or_expr, equality_expr, relational_expr

from test_expressions import (
    base_expression,
    # boolean literals
    TRUE, FALSE,
    # number literals (for special values)
    NOT_A_NUMBER, POSITIVE_INFINITY, NEGATIVE_INFINITY,
    # nodeset literals
    nodeset_literal, EMPTY_NODESET,
    )

from amara.xpath import context
from test_expressions import DOC
default_context = context(DOC, 1, 1)


EGG1 = tree.element(None, 'egg1')
EGG1.xml_append(tree.text('egg1'))
EGG2 = tree.element(None, 'egg2')
EGG2.xml_append(tree.text('egg2'))

NUM = tree.element(None, 'num')
NUM0 = tree.attribute(None, 'num0', '0')
NUM.xml_attributes.setnode(NUM0)
NUM2 = tree.attribute(None, 'num2', '2')
NUM.xml_attributes.setnode(NUM0)
NUM4 = tree.attribute(None, 'num4', '4')
NUM.xml_attributes.setnode(NUM0)
NUM31 = tree.attribute(None, 'num31', '31')
NUM.xml_attributes.setnode(NUM0)

def test_or_expr():
    for (left, right), expected in (
        ((FALSE, FALSE), datatypes.FALSE),
        ((TRUE, FALSE), datatypes.TRUE),
        ((FALSE, TRUE), datatypes.TRUE),
        ((TRUE, TRUE), datatypes.TRUE),
        ):
        node = or_expr(left, 'or', right)
        result = node.evaluate_as_boolean(default_context)
        assert isinstance(result, datatypes.boolean), result
        assert result == expected, (result, expected)

def test_and_expr():
    for (left, right), expected in (
        ((FALSE, FALSE), datatypes.FALSE),
        ((TRUE, FALSE), datatypes.FALSE),
        ((FALSE, TRUE), datatypes.FALSE),
        ((TRUE, TRUE), datatypes.TRUE),
        ):
        node = and_expr(left, 'and', right)
        result = node.evaluate_as_boolean(default_context)
        assert isinstance(result, datatypes.boolean), result
        assert result == expected, (result, expected)

def test_equality_expr():
    for (left, right), expected in (
        # `=` tests
        ((number_literal('5'), number_literal('5')), datatypes.TRUE),
        ((number_literal('5'), number_literal('-5')), datatypes.FALSE),
        ((number_literal('-5'), number_literal('-5')), datatypes.TRUE),
        ((number_literal('0'), number_literal('0')), datatypes.TRUE),
        ((POSITIVE_INFINITY, POSITIVE_INFINITY), datatypes.TRUE),
        ((POSITIVE_INFINITY, NEGATIVE_INFINITY), datatypes.FALSE),
        ((NEGATIVE_INFINITY, POSITIVE_INFINITY), datatypes.FALSE),
        ((NEGATIVE_INFINITY, NEGATIVE_INFINITY), datatypes.TRUE),
        ((number_literal('5'), POSITIVE_INFINITY), datatypes.FALSE),
        ((number_literal('5'), NOT_A_NUMBER), datatypes.FALSE),
        ((NOT_A_NUMBER, NOT_A_NUMBER), datatypes.FALSE),
        ((number_literal('5'), nodeset_literal([NUM31])), datatypes.FALSE),
        ((string_literal('5'), string_literal('5')), datatypes.TRUE),
        ((string_literal('5'), string_literal('-5')), datatypes.FALSE),
        ((string_literal('-5'), string_literal('-5')), datatypes.TRUE),
        ((string_literal('0'), string_literal('0')), datatypes.TRUE),
        ((string_literal('Hi'), string_literal('Hi')), datatypes.TRUE),
        ((string_literal('5'), string_literal('Hi')), datatypes.FALSE),
        ((string_literal('5'), string_literal('NaN')), datatypes.FALSE),
        ((string_literal('NaN'), string_literal('NaN')), datatypes.TRUE),
        ((string_literal('5'), nodeset_literal([NUM31])), datatypes.FALSE),
        ((EMPTY_NODESET, TRUE), datatypes.FALSE),
        ((EMPTY_NODESET, FALSE), datatypes.TRUE),
        ((EMPTY_NODESET, nodeset_literal([EGG1])), datatypes.FALSE),
        ((nodeset_literal([EGG1]), EMPTY_NODESET), datatypes.FALSE),
        ((nodeset_literal([EGG1]), nodeset_literal([EGG1])), datatypes.TRUE),
        ((string_literal('egg1'), nodeset_literal([EGG1])), datatypes.TRUE),
        ((string_literal('egg2'), nodeset_literal([EGG1])), datatypes.FALSE),
        ((string_literal('egg1'),  nodeset_literal([EGG1, EGG2])), datatypes.TRUE),
        ):
        node = equality_expr(left, '=', right)
        result = node.evaluate_as_boolean(default_context)
        assert isinstance(result, datatypes.boolean), result
        assert result == expected, (result, expected)

def test_inequality_expr():
    for (left, right), expected in (
        # `!=` tests
        ((number_literal('5'), number_literal('5')), datatypes.FALSE),
        ((number_literal('5'), number_literal('-5')), datatypes.TRUE),
        ((number_literal('-5'), number_literal('-5')), datatypes.FALSE),
        ((number_literal('0'), number_literal('0')), datatypes.FALSE),
        ((POSITIVE_INFINITY, POSITIVE_INFINITY), datatypes.FALSE),
        ((POSITIVE_INFINITY, NEGATIVE_INFINITY), datatypes.TRUE),
        ((NEGATIVE_INFINITY, POSITIVE_INFINITY), datatypes.TRUE),
        ((NEGATIVE_INFINITY, NEGATIVE_INFINITY), datatypes.FALSE),
        ((number_literal('5'), POSITIVE_INFINITY), datatypes.TRUE),
        ((number_literal('5'), NOT_A_NUMBER), datatypes.TRUE),
        ((NOT_A_NUMBER, NOT_A_NUMBER), datatypes.TRUE),
        ((number_literal('5'), nodeset_literal([NUM31])), datatypes.TRUE),
        ((string_literal('5'), string_literal('5')), datatypes.FALSE),
        ((string_literal('5'), string_literal('-5')), datatypes.TRUE),
        ((string_literal('-5'), string_literal('-5')), datatypes.FALSE),
        ((string_literal('0'), string_literal('0')), datatypes.FALSE),
        ((string_literal('5'), string_literal('Hi')), datatypes.TRUE),
        ((string_literal('5'), string_literal('NaN')), datatypes.TRUE),
        ((string_literal('NaN'), string_literal('NaN')), datatypes.FALSE),
        ((string_literal('5'), nodeset_literal([NUM31])), datatypes.TRUE),
        ((EMPTY_NODESET, TRUE), datatypes.TRUE),
        ((EMPTY_NODESET, FALSE), datatypes.FALSE),
        ((EMPTY_NODESET, nodeset_literal([EGG1])), datatypes.FALSE),
        ((nodeset_literal([EGG1]), EMPTY_NODESET), datatypes.FALSE),
        ((nodeset_literal([EGG1]), nodeset_literal([EGG1])), datatypes.FALSE),
        ((string_literal('egg1'), nodeset_literal([EGG1])), datatypes.FALSE),
        ((string_literal('egg2'), nodeset_literal([EGG1])), datatypes.TRUE),
        # Yeah, non-intuitive, but datatypes.TRUE acc to XPath spec 3.4
        ((string_literal('egg1'), nodeset_literal([EGG1, EGG2])), datatypes.TRUE),
        ):
        node = equality_expr(left, '!=', right)
        result = node.evaluate_as_boolean(default_context)
        assert isinstance(result, datatypes.boolean), result
        assert result == expected, (result, expected)


def test_relational_expr():
    for (left, op, right), expected in (
        ((number_literal('5'), '<',  number_literal('5')), datatypes.FALSE),
        ((number_literal('5'), '<=', number_literal('5')), datatypes.TRUE),
        ((number_literal('5'), '>',  number_literal('5')), datatypes.FALSE),
        ((number_literal('5'), '>=', number_literal('5')), datatypes.TRUE),
        ((number_literal('5'), '<',  number_literal('-5')), datatypes.FALSE),
        ((number_literal('5'), '<=', number_literal('-5')), datatypes.FALSE),
        ((number_literal('5'), '>',  number_literal('-5')), datatypes.TRUE),
        ((number_literal('5'), '>=', number_literal('-5')), datatypes.TRUE),
        ((number_literal('5'), '<',  number_literal('0')), datatypes.FALSE),
        ((number_literal('5'), '<=', number_literal('0')), datatypes.FALSE),
        ((number_literal('5'), '>',  number_literal('0')), datatypes.TRUE),
        ((number_literal('5'), '>=', number_literal('0')), datatypes.TRUE),
        ((number_literal('5'), '<',  POSITIVE_INFINITY), datatypes.TRUE),
        ((number_literal('5'), '<=', POSITIVE_INFINITY), datatypes.TRUE),
        ((number_literal('5'), '>',  POSITIVE_INFINITY), datatypes.FALSE),
        ((number_literal('5'), '>=', POSITIVE_INFINITY), datatypes.FALSE),
        ((number_literal('5'), '<',  NEGATIVE_INFINITY), datatypes.FALSE),
        ((number_literal('5'), '<=', NEGATIVE_INFINITY), datatypes.FALSE),
        ((number_literal('5'), '>',  NEGATIVE_INFINITY), datatypes.TRUE),
        ((number_literal('5'), '>=', NEGATIVE_INFINITY), datatypes.TRUE),
        ((number_literal('5'), '<',  NOT_A_NUMBER), datatypes.FALSE),
        ((number_literal('5'), '<=', NOT_A_NUMBER), datatypes.FALSE),
        ((number_literal('5'), '>',  NOT_A_NUMBER), datatypes.FALSE),
        ((number_literal('5'), '>=', NOT_A_NUMBER), datatypes.FALSE),
        ((number_literal('5'), '<',  nodeset_literal([NUM31])), datatypes.TRUE),
        ((number_literal('5'), '<=', nodeset_literal([NUM31])), datatypes.TRUE),
        ((number_literal('5'), '>',  nodeset_literal([NUM31])), datatypes.FALSE),
        ((number_literal('5'), '>=', nodeset_literal([NUM31])), datatypes.FALSE),
        ((number_literal('5'), '<',  string_literal('5')), datatypes.FALSE),
        ((number_literal('5'), '<=', string_literal('5')), datatypes.TRUE),
        ((number_literal('5'), '>',  string_literal('5')), datatypes.FALSE),
        ((number_literal('5'), '>=', string_literal('5')), datatypes.TRUE),
        ((number_literal('31'), '<',  string_literal('5')), datatypes.FALSE),
        ((number_literal('31'), '<=', string_literal('5')), datatypes.FALSE),
        ((number_literal('31'), '>',  string_literal('5')), datatypes.TRUE),
        ((number_literal('31'), '>=', string_literal('5')), datatypes.TRUE),
        ((string_literal('5'), '<',  string_literal('5')), datatypes.FALSE),
        ((string_literal('5'), '<=', string_literal('5')), datatypes.TRUE),
        ((string_literal('5'), '>',  string_literal('5')), datatypes.FALSE),
        ((string_literal('5'), '>=', string_literal('5')), datatypes.TRUE),
        ((string_literal('31'), '<',  string_literal('5')), datatypes.FALSE),
        ((string_literal('31'), '<=', string_literal('5')), datatypes.FALSE),
        ((string_literal('31'), '>',  string_literal('5')), datatypes.TRUE),
        ((string_literal('31'), '>=', string_literal('5')), datatypes.TRUE),
        ((number_literal('5'), '<',  string_literal('-5')), datatypes.FALSE),
        ((number_literal('5'), '<=', string_literal('-5')), datatypes.FALSE),
        ((number_literal('5'), '>',  string_literal('-5')), datatypes.TRUE),
        ((number_literal('5'), '>=', string_literal('-5')), datatypes.TRUE),
        ((number_literal('31'), '<',  string_literal('-5')), datatypes.FALSE),
        ((number_literal('31'), '<=', string_literal('-5')), datatypes.FALSE),
        ((number_literal('31'), '>',  string_literal('-5')), datatypes.TRUE),
        ((number_literal('31'), '>=', string_literal('-5')), datatypes.TRUE),
        ((string_literal('5'), '<',  string_literal('-5')), datatypes.FALSE),
        ((string_literal('5'), '<=', string_literal('-5')), datatypes.FALSE),
        ((string_literal('5'), '>',  string_literal('-5')), datatypes.TRUE),
        ((string_literal('5'), '>=', string_literal('-5')), datatypes.TRUE),
        ((string_literal('31'), '<',  string_literal('-5')), datatypes.FALSE),
        ((string_literal('31'), '<=', string_literal('-5')), datatypes.FALSE),
        ((string_literal('31'), '>',  string_literal('-5')), datatypes.TRUE),
        ((string_literal('31'), '>=', string_literal('-5')), datatypes.TRUE),
        ((string_literal('5'), '<',  string_literal('Hi')), datatypes.FALSE),
        ((string_literal('5'), '<=', string_literal('Hi')), datatypes.FALSE),
        ((string_literal('5'), '>',  string_literal('Hi')), datatypes.FALSE),
        ((string_literal('5'), '>=', string_literal('Hi')), datatypes.FALSE),
        ((string_literal('5'), '<',  nodeset_literal([NUM31])), datatypes.TRUE),
        ((string_literal('5'), '<=', nodeset_literal([NUM31])), datatypes.TRUE),
        ((string_literal('5'), '>',  nodeset_literal([NUM31])), datatypes.FALSE),
        ((string_literal('5'), '>=', nodeset_literal([NUM31])), datatypes.FALSE),
        ((nodeset_literal([NUM2]), '<',  nodeset_literal([NUM2])), datatypes.FALSE),
        ((nodeset_literal([NUM2]), '<=', nodeset_literal([NUM2])), datatypes.TRUE),
        ((nodeset_literal([NUM2]), '>',  nodeset_literal([NUM2])), datatypes.FALSE),
        ((nodeset_literal([NUM2]), '>=', nodeset_literal([NUM2])), datatypes.TRUE),
        ((nodeset_literal([NUM0]), '<',  nodeset_literal([NUM2])), datatypes.TRUE),
        ((nodeset_literal([NUM0]), '<=', nodeset_literal([NUM2])), datatypes.TRUE),
        ((nodeset_literal([NUM0]), '>',  nodeset_literal([NUM2])), datatypes.FALSE),
        ((nodeset_literal([NUM0]), '>=', nodeset_literal([NUM2])), datatypes.FALSE),
        ((nodeset_literal([NUM4]), '<',  nodeset_literal([NUM2])), datatypes.FALSE),
        ((nodeset_literal([NUM4]), '<=', nodeset_literal([NUM2])), datatypes.FALSE),
        ((nodeset_literal([NUM4]), '>',  nodeset_literal([NUM2])), datatypes.TRUE),
        ((nodeset_literal([NUM4]), '>=', nodeset_literal([NUM2])), datatypes.TRUE),
        ):
        
        node = relational_expr(left, op, right)
        result = node.evaluate_as_boolean(default_context)
        assert isinstance(result, datatypes.boolean), result
        assert result == expected, (result, expected)


if __name__ == '__main__':
    raise SystemExit("Use nosetests")
