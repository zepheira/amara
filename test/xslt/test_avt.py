########################################################################
# test/xslt/test_avt.py
from amara.test.xpath.test_expressions import DOC
from amara.xpath import datatypes, context
from amara.xslt import XsltError

from amara.xslt.expressions.avt import avt_expression

DEFAULT_CONTEXT = context(DOC, 1, 1)

def test_avt():
    for arg, expected in (
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
        ):
        result = avt_expression(arg).evaluate_as_string(DEFAULT_CONTEXT)
        assert isinstance(result, datatypes.string)
        assert result == expected, (result, expected)


def test_avt_errors():
    for arg, in (
        ('{}',),                # no expression is error
        ('{-{{"literal"}',),    # '-{"literal"' is invalid Expr
        ('{"literal"}}-}',),    # '{"literal"} is expr; '}-}' is error
        ('{{node()}',),         # '{{node()' is literal, trailing '}' is error
        ('{node()}}',),         # '{node()}' is expr; trailing '}' is error
        ('(id(@ref)/title}',),  # missing leading '{'
        ('{(id(@ref)/title',),  # missing trailing '{'
        ):
        try:
            avt_expression(arg)
            raise AssertionError("should not have allowed %r" % (arg,))
        except XsltError:
            pass
if __name__ == '__main__':
    raise SystemExit("use nosetests")
