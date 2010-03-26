#!/usr/bin/env python

from amara.xpath import datatypes
from amara.xpath.expressions.basics import string_literal, number_literal
from amara.xpath import context
from test_expressions import DOC

default_context = context(DOC, 1, 1)

def test_string_literal():
    for input, expected in (        
        (u'""', u''),
        (u'"Hi"', u'Hi'),
        (u'"NaN"', u'NaN'),
        (u'"\u2022 = middle dot"', u'\u2022 = middle dot'),
        (u'"0"', u'0'),
        (u'"1"', u'1'),
        (u'"2"', u'2'),
        (u'"3"', u'3'),
        (u'"4"', u'4'),
        (u'"5"', u'5'),
        (u'"31"', u'31'),
        (u'"-1"', u'-1'),
        (u'"-2"', u'-2'),
        (u'"-3"', u'-3'),
        (u'"-4"', u'-4'),
        (u'"-5"', u'-5'),
        (u'"3.1415926535"', u'3.1415926535'),
        ):
        node = string_literal(input)
        result = node.evaluate_as_string(default_context)
        assert isinstance(result, datatypes.string), result
        assert result == expected, (result, expected)

def test_number_literal():
    for input, expected in (
        ('0', 0.0),
        ('0.5', 0.5),
        ('-0.5', -0.5),
        ('1', 1.0),
        ('-1', -1.0),
        ('1.5', 1.5),
        ('-1.5', -1.5),
        ('2', 2.0),
        ('-2', -2.0),
        ('2.6', 2.6),
        ('-2.6', -2.6),
        ('3', 3.0),
        ('-3.0', -3.0),
        ('31', 31.0),
        ('4', 4.0),
        ('-4', -4.0),
        ('4.5', 4.5),
        ('-4.5', -4.5),
        ('5', 5.0),
        ('-5', -5.0),
        ('-42', -42.0),
        # Not normal tokens, but need to be handled internally
        (datatypes.NOT_A_NUMBER, datatypes.NOT_A_NUMBER),
        (datatypes.POSITIVE_INFINITY, datatypes.POSITIVE_INFINITY),
        (datatypes.NEGATIVE_INFINITY, datatypes.NEGATIVE_INFINITY),
        ):
        node = number_literal(input)
        result = node.evaluate_as_number(default_context)
        assert isinstance(result, datatypes.number), result
        if hasattr(expected, "isnan") and expected.isnan():
            assert result.isnan(), result
        else:
            assert result == expected, (result, expected)

if __name__ == '__main__':
    raise SystemExit("Use nosetests")
