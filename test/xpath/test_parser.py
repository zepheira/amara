#!/usr/bin/env python
from amara.lib import testsupport
from amara import tree
from amara.xpath import context, datatypes, XPathError

from test_expressions import (
    # expression TestCase
    test_expression,
    # nodeset literals
    DOC, PI, PI2, ROOT, CHILDREN, CHILD1, ATTR1, GCHILDREN1, GCHILD11,
    GCHILD12, TEXT1, CHILD2, ATTR2, IDATTR2, GCHILDREN2, GCHILD21, CHILD3,
    LANG, LCHILDREN, NONASCIIQNAME,
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


class test_parser(test_expression):
    module_name = 'amara.xpath.parser'
    class_name = 'parse'


class test_parser_pass(test_parser):
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
        (["text()"], datatypes.nodeset([TEXT1]), CONTEXT_CHILD1),
        (["text()"], datatypes.nodeset(), CONTEXT_CHILD2),
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
        #(['@attr31 * 1'], datatypes.NOT_A_NUMBER, CONTEXT_CHILD1),

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
        ]


class test_parser_errors(test_parser):

    @classmethod
    def new_test_method(cls, expected, factory, args, context):
        def get_error_string(code):
            for attr, value in vars(XPathError).iteritems():
                if value == code:
                    return 'XPathError.' + attr
            return 'XPathError(%s)' % (code,)
        expected = get_error_string(expected)
        def test_method(self):
            try:
                expr = factory(*args)
            except XPathError, error:
                self.assertEquals(expected, get_error_string(error.code))
            else:
                try:
                    result = expr.evaluate(context)
                except XPathError, error:
                    self.assertEquals(expected, get_error_string(error.code))
                else:
                    self.fail('%s not raised' % expected)
        return test_method

    test_cases = [
        (['\\'], XPathError.SYNTAX, CONTEXT_ROOT),
        (['.//foo:*'], XPathError.UNDEFINED_PREFIX, CONTEXT_CHILD3),
        (['$foo'], XPathError.UNDEFINED_VARIABLE, CONTEXT_CHILD1),
        ]

if __name__ == '__main__':
    testsupport.test_main()
