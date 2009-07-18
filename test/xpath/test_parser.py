#!/usr/bin/env python
from amara import tree
from amara.xpath import context, datatypes, XPathError

from test_expressions import (
    # expression TestCase
    base_expression,
    # nodeset literals
    DOC, PI, PI2, ROOT, CHILDREN, CHILD1, ATTR1, GCHILDREN1, GCHILD11,
    GCHILD12, TEXT1, CHILD2, ATTR2, IDATTR2, GCHILDREN2, GCHILD21, CHILD3,
    LANG, LCHILDREN, NONASCIIQNAME, TEXT_WS1, TEXT_WS2
    )

CONTEXT_DOC = context(DOC, 1, 1)
CONTEXT_ROOT = context(ROOT, 1, 1,
                       variables={(None, 'foo'): datatypes.nodeset([ROOT])})
CONTEXT_CHILD1 = context(CHILD1, 1, 2,
                         namespaces={'x': 'http://spam.com'})
CONTEXT_CHILD2 = context(CHILD2, 2, 2)
CONTEXT_CHILD3 = context(CHILD3, 1, 1)
CONTEXT_TEXT = context(TEXT1, 3, 3)
CONTEXT_GCHILD11 = context(GCHILD11, 1, 2)
CONTEXT_LANG = context(LANG, 1, 1)

# <elements>
#   <element>
#     <x>
#       <y>a</y>
#     </x>
#   </element>
#   <element>
#     <x>
#       <y>z</y>
#     </x>
#   </element>
# </elements>
ELEMENTS = tree.entity().xml_append(tree.element(None, 'elements'))
for cdata in ('a', 'z'):
    node = ELEMENTS.xml_append(tree.element(None, 'element'))
    node = node.xml_append(tree.element(None, 'x'))
    node = node.xml_append(tree.element(None, 'y'))
    node.xml_append(tree.text(cdata))
del node, cdata
CONTEXT_ELEMENT = context(ELEMENTS, 1, 1)
ELEMENT1, ELEMENT2 = ELEMENTS

from amara.xpath.parser import parse


def _run_parser_pass(test_cases):
    for args, expected, ctx in test_cases:
        result = parse(*args).evaluate(ctx)
        if hasattr(expected, "isnan") and expected.isnan():
            assert result.isnan()
            continue
        if isinstance(expected, list):
            # convert nodesets to lists to prevent XPath-style nodeset compares
            result = list(result)
            expected = list(expected)
        assert result == expected, (args, result, expected)

def test_parser_pass():
    test_cases = [
        (['child::*'], datatypes.nodeset(CHILDREN), CONTEXT_ROOT),
        (['/child::*'], datatypes.nodeset([ROOT]), CONTEXT_CHILD1),
        (['/*/*'], datatypes.nodeset(CHILDREN), CONTEXT_CHILD1),
        (['/child::*/*/child::GCHILD'],
         datatypes.nodeset(GCHILDREN1 + GCHILDREN2),
         CONTEXT_CHILD1),
        (['//*'], datatypes.nodeset([ROOT, CHILD1] + GCHILDREN1 +
                                    [CHILD2] + GCHILDREN2 + [CHILD3, LANG] +
                                    LCHILDREN),
         CONTEXT_CHILD1),
        (['//GCHILD'], datatypes.nodeset(GCHILDREN1 + GCHILDREN2),
         CONTEXT_CHILD1),
        (['//@attr1'], datatypes.nodeset([ATTR1, ATTR2]), CONTEXT_CHILD1),
        (['x:GCHILD'], datatypes.nodeset(), CONTEXT_CHILD1),
        (['.//GCHILD'], datatypes.nodeset(GCHILDREN2), CONTEXT_CHILD2),
        (['.//GCHILD'], datatypes.nodeset(GCHILDREN1 + GCHILDREN2),
         CONTEXT_ROOT),
        (['/'], datatypes.nodeset([DOC]), CONTEXT_TEXT),
        (['//CHILD1/..'], datatypes.nodeset([ROOT]), CONTEXT_CHILD1),
        (['CHILD1 | CHILD2'], datatypes.nodeset([CHILD1, CHILD2]),
         CONTEXT_ROOT),
        (['descendant::GCHILD[3]'], datatypes.nodeset([GCHILD21]),
         CONTEXT_ROOT),
        (['descendant::GCHILD[parent::CHILD1]'], datatypes.nodeset(GCHILDREN1),
         CONTEXT_ROOT),
        (['descendant::GCHILD[position() > 1]'],
         datatypes.nodeset([GCHILD12] + GCHILDREN2),
         CONTEXT_ROOT),
        (['CHILD2/@CODE'], datatypes.nodeset([IDATTR2]), CONTEXT_ROOT),
        (['CHILD2/@CODE * 0'], datatypes.number(0), CONTEXT_ROOT),
        ([u'f\xf6\xf8'], datatypes.nodeset([NONASCIIQNAME]), CONTEXT_LANG),
        (['@attr1[.="val1"]'], datatypes.nodeset([ATTR1]), CONTEXT_CHILD1),
        (["processing-instruction()"], datatypes.nodeset([PI, PI2]),
         CONTEXT_DOC),
        (["processing-instruction('no-data')"], datatypes.nodeset([PI2]),
         CONTEXT_DOC),
        (["processing-instruction('f')"], datatypes.nodeset(), CONTEXT_DOC),

        (['1'], datatypes.number(1), CONTEXT_ROOT),
        (['00200'], datatypes.number(200), CONTEXT_ROOT),
        (['3+4*7'], datatypes.number(31), CONTEXT_ROOT),
        (['3-4*1'], datatypes.number(-1), CONTEXT_ROOT),
        (['. * 0'], datatypes.NOT_A_NUMBER, CONTEXT_CHILD1),
        (['.. * 1'], datatypes.NOT_A_NUMBER, CONTEXT_CHILD1),
        #(['@attr31 * 1'], datatypes.NOT_A_NUMBER, CONTEXT_CHILD1), # TODO: Why is this commented out?

        (["string('1')"], datatypes.string("1"), CONTEXT_ROOT),
        (["concat('1', '2')"], datatypes.string("12"), CONTEXT_ROOT),

        (['true()'], datatypes.TRUE, CONTEXT_ROOT),
        (['false()'], datatypes.FALSE, CONTEXT_ROOT),
        (['1=3<4'], datatypes.TRUE, CONTEXT_ROOT),
        (['1 or 2 and 3'], datatypes.TRUE, CONTEXT_ROOT),
        (['1 and 2 = 3'], datatypes.FALSE, CONTEXT_ROOT),
        (['-1 or 2'], datatypes.TRUE, CONTEXT_ROOT),
        (['. or *'], datatypes.TRUE, CONTEXT_ROOT),

        (['$foo[1]'], datatypes.nodeset([ROOT]), CONTEXT_ROOT),
        (['$foo[1]/CHILD1'], datatypes.nodeset([CHILD1]), CONTEXT_ROOT),
        (['$foo[1]//GCHILD'], datatypes.nodeset(GCHILDREN1 + GCHILDREN2),
         CONTEXT_ROOT),
        (['$foo[1][3]'], datatypes.nodeset(), CONTEXT_ROOT),

        (['(child::*)'], datatypes.nodeset(CHILDREN), CONTEXT_ROOT),
        (['//element[descendant::y[.="z"]]'], datatypes.nodeset([ELEMENT2]),
         CONTEXT_ELEMENT),
        (['//element[descendant::y[.="z"]][1]'], datatypes.nodeset([ELEMENT2]),
         CONTEXT_ELEMENT),
        (['//element[descendant::y[.="z"]][2]'], datatypes.nodeset(),
         CONTEXT_ELEMENT),
        (["text()"], datatypes.nodeset(), CONTEXT_CHILD3),
        (["text()"], datatypes.nodeset([TEXT_WS1, TEXT_WS2, TEXT1]), CONTEXT_CHILD1),
        ]

    _run_parser_pass(test_cases)

def test_parser_errors_new():
    test_cases = (
        (['\\'], XPathError.SYNTAX, CONTEXT_ROOT),
        (['.//foo:*'], XPathError.UNDEFINED_PREFIX, CONTEXT_CHILD3),
        (['$foo'], XPathError.UNDEFINED_VARIABLE, CONTEXT_CHILD1),
        )
    for args, expected_error_code, ctx in test_cases:
        try:
            _run_parser_pass([(args, None, ctx)])
        except XPathError, error:
            assert error.code == expected_error_code, (error, error.code, expected_error_code)
        else:
            raise AssertionError("Expected XPathError code %r" % (expected_error_code,))

if __name__ == '__main__':
    raise SystemExit("Use nosetests")
