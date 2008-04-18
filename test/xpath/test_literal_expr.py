import unittest
from amara.lib import testsupport

class test_literal_expressions(unittest.TestCase):

    def assertEqual(self, first, second, msg=None):
        if isinstance(first, float) and isinstance(second, float):
            from amara.xpath.datatypes import number
            if number(first).isnan():
                first = 'NaN'
            if number(second).isnan():
                second = 'NaN'
        return unittest.TestCase.assertEqual(self, first, second, msg)

    def setUp(self):
        from amara._domlette import Document
        from amara.xpath import datatypes
        from amara.xpath.expressions.basics import \
            string_literal, number_literal
        from amara.xpath.context import xpathcontext

        # fmt: (<token>, <expected>)
        tests = [
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
            ]
        self.string_tests = [ (string_literal(src), datatypes.string(dst))
                              for src, dst in tests ]

        # fmt: (<token>, <expected>)
        tests = [
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
            ]
        self.number_tests = [ (number_literal(src), datatypes.number(dst))
                              for src, dst in tests ]

        self.context = xpathcontext(Document(), 1, 1)
        return

    def test_string_literals(self):
        for expr, expected in self.string_tests:
            self.assertEqual(expr.evaluate(self.context), expected, str(expr))
        return
        
    def test_number_literals(self):
        for expr, expected in self.number_tests:
            self.assertEqual(expr.evaluate(self.context), expected, str(expr))
        return

if __name__ == '__main__':
    testsupport.test_main()