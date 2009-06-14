########################################################################
# test/xslt/test_avt.py
from amara.test.xpath.test_expressions import base_expression
from amara.xpath import datatypes
from amara.xslt import XsltError

class test_avt(base_expression):
    module_name = 'amara.xslt.expressions.avt'
    class_name = "avt_expression"
    evaluate_method = 'evaluate_as_string'
    return_type = datatypes.string
    test_cases = [
        ('', ''),
        ('Senatus{{populisque}}romae', 'Senatus{populisque}romae'),
        ('Senatus{{{"populisque}}"}romae', 'Senatus{populisque}}romae'),
        ('{"{literal}"}', '{literal}'),
        ('{"{literal"}', '{literal'),
        ('{"literal}"}', 'literal}'),
        ('{"{{literal}}"}', '{{literal}}'),
        ('{"{{literal"}', '{{literal'),
        ('{"literal}}"}', 'literal}}'),
        ('{{{"literal"}', '{literal'),
        ('{{-{"literal"}', '{-literal'),
        ('{"literal"}}}', 'literal}'),
        ('{"literal"}-}}', 'literal-}'),
        ('{"100"}% {100}% {90+10}% 100% {"%"}1{0}0 %100', '100% 100% 100% 100% %100 %100'),
        ]

    @classmethod
    def unpack_tst_case(cls, source, expected=None, *extras):
        return (source,), expected, extras


class test_avt_errors(test_avt):
    test_cases = [
        ('{}',),                # no expression is error
        ('{-{{"literal"}',),    # '-{"literal"' is invalid Expr
        ('{"literal"}}-}',),    # '{"literal"} is expr; '}-}' is error
        ('{{node()}',),         # '{{node()' is literal, trailing '}' is error
        ('{node()}}',),         # '{node()}' is expr; trailing '}' is error
        ('(id(@ref)/title}',),  # missing leading '{'
        ('{(id(@ref)/title',),  # missing trailing '{'
        ]

    @classmethod
    def new_tst_method(*q):
        # work around some strange metaclass interacation with nose
        if len(q) == 1:
            return
        cls, expected, factory, args = q
        def test_method(self):
            self.assertRaises(XsltError, factory, *args)
        return test_method


if __name__ == '__main__':
    from amara.test import test_main
    test_main()
