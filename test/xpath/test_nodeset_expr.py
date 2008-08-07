#!/usr/bin/env python
from amara import tree
from amara.xpath import context, datatypes
from amara.xpath.locationpaths.predicates import predicates, predicate

from test_expressions import (
    test_expression,
    # boolean literals
    TRUE, FALSE,
    # nodeset literals
    nodeset_literal, ROOT, CHILD1, CHILD2, CHILD3
    )

CONTEXT = context(CHILD1, 1, 1)

class test_nodeset_expr(test_expression):
    module_name = 'amara.xpath.expressions.nodesets'
    evaluate_method = 'evaluate_as_nodeset'
    return_type = datatypes.nodeset


class test_union_exr(test_nodeset_expr):
    class_name = 'union_expr'
    test_cases = [
        ([nodeset_literal([ROOT, CHILD1]), nodeset_literal([ROOT])],
         datatypes.nodeset([ROOT, CHILD1]), CONTEXT),
        ]


class test_path_exr(test_nodeset_expr):
    class_name = 'path_expr'
    test_cases = [
        ([nodeset_literal([ROOT, CHILD1]), '/', nodeset_literal([ROOT])],
         datatypes.nodeset([ROOT]), CONTEXT),
        ]


class test_filter_exr(test_nodeset_expr):
    class_name = 'filter_expr'
    test_cases = [
        ([nodeset_literal([ROOT, CHILD1]), predicates([predicate(TRUE)])],
         datatypes.nodeset([ROOT, CHILD1]), CONTEXT),
        ([nodeset_literal([ROOT, CHILD1]), predicates([predicate(FALSE)])],
         datatypes.nodeset(), CONTEXT),
        ]


if __name__ == '__main__':
    from amara.lib import testsupport
    testsupport.test_main()
