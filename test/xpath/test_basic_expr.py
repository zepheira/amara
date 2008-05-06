#!/usr/bin/env python
from amara.lib import testsupport
from amara.xpath import datatypes

from test_expressions import test_expression

class test_basic_expr(test_expression):
    module_name = 'amara.xpath.expressions.basics'


class test_string_literal(test_basic_expr):
    class_name = 'string_literal'
    evaluate_method = 'evaluate_as_string'
    return_type = datatypes.string
    test_cases = [
        ((u'""',), u''),
        ((u'"Hi"',), u'Hi'),
        ((u'"NaN"',), u'NaN'),
        ((u'"\u2022 = middle dot"',), u'\u2022 = middle dot'),
        ((u'"0"',), u'0'),
        ((u'"1"',), u'1'),
        ((u'"2"',), u'2'),
        ((u'"3"',), u'3'),
        ((u'"4"',), u'4'),
        ((u'"5"',), u'5'),
        ((u'"31"',), u'31'),
        ((u'"-1"',), u'-1'),
        ((u'"-2"',), u'-2'),
        ((u'"-3"',), u'-3'),
        ((u'"-4"',), u'-4'),
        ((u'"-5"',), u'-5'),
        ((u'"3.1415926535"',), u'3.1415926535'),
        ]

    
class test_number_literal(test_basic_expr):
    class_name = 'number_literal'
    evaluate_method = 'evaluate_as_number'
    return_type = datatypes.number
    test_cases = [
        (('0',), 0.0),
        (('0.5',), 0.5),
        (('-0.5',), -0.5),
        (('1',), 1.0),
        (('-1',), -1.0),
        (('1.5',), 1.5),
        (('-1.5',), -1.5),
        (('2',), 2.0),
        (('-2',), -2.0),
        (('2.6',), 2.6),
        (('-2.6',), -2.6),
        (('3',), 3.0),
        (('-3.0',), -3.0),
        (('31',), 31.0),
        (('4',), 4.0),
        (('-4',), -4.0),
        (('4.5',), 4.5),
        (('-4.5',), -4.5),
        (('5',), 5.0),
        (('-5',), -5.0),
        (('-42',), -42.0),
        # Not normal tokens, but need to be handled internally
        ((datatypes.NOT_A_NUMBER,), datatypes.NOT_A_NUMBER),
        ((datatypes.POSITIVE_INFINITY,), datatypes.POSITIVE_INFINITY),
        ((datatypes.NEGATIVE_INFINITY,), datatypes.NEGATIVE_INFINITY),
        ]


if __name__ == '__main__':
    testsupport.test_main()
