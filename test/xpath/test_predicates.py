#!/usr/bin/env python
from amara.lib import testsupport
from amara.xpath import context, datatypes
from amara.xpath.expressions.basics import number_literal, string_literal
from amara.xpath.expressions.booleans import and_expr, or_expr

from test_expressions import (
    # expression TestCase
    test_xpath,
    # boolean literals
    TRUE, FALSE,
    # IEEE 754 "special" numbers as expressions
    NOT_A_NUMBER, POSITIVE_INFINITY, NEGATIVE_INFINITY,
    # nodeset literals
    nodeset_literal, ROOT
    )


class test_predicate_expr(test_xpath):
    module_name = 'amara.xpath.locationpaths.predicates'

    @classmethod
    def new_test_method(cls, expected, factory, args, nodes):
        ctx = context(nodes[0], 1, len(nodes))
        def test_method(self):
            predicate = factory(*args)
            result = predicate.select(ctx, nodes)
            self.assertEquals(expected, list(result))
        return test_method


class test_predicate(test_predicate_expr):
    class_name = 'predicate'
    test_cases = [
        # FIXME: test literal optimization
        # FIXME: test `position() = Expr` optimization
        # FIXME: test `position() [>,>=] Expr` optimization
        # FIXME: test `Expr [<,<=] position()` optimization
        # FIXME: test numeric-type expression
        # test boolean-type expression
        ([and_expr(TRUE, 'and', FALSE)], [], [ROOT]),
        ([or_expr(TRUE, 'or', FALSE)], [ROOT], [ROOT]),
        # FIXME: test object-type expression
        ]

if __name__ == '__main__':
    testsupport.test_main()
