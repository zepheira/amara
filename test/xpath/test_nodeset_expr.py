#!/usr/bin/env python
from amara import domlette
from amara.xpath import datatypes
from amara.xpath.locationpaths.predicates import predicates, predicate

from test_expressions import (
    test_expr,
    # boolean literals
    TRUE, FALSE,
    # nodeset literals
    nodeset_literal, ROOT, CHILD1, CHILD2, CHILD3
    )

class test_nodeset_expr(test_expr):
    module_name = 'amara.xpath.expressions.nodesets'
    evaluate_method = 'evaluate_as_nodeset'
    return_type = datatypes.nodeset

    def new_context(self):
        return test_expr.new_context(self, CHILD1)


class test_union_exr(test_nodeset_expr):
    class_name = 'union_expr'
    test_cases = [
        ([nodeset_literal([ROOT, CHILD1]), nodeset_literal([ROOT])],
         datatypes.nodeset([ROOT, CHILD1])),
        ]


class test_path_exr(test_nodeset_expr):
    class_name = 'path_expr'
    test_cases = [
        ([nodeset_literal([ROOT, CHILD1]), '/', nodeset_literal([ROOT])],
         datatypes.nodeset([ROOT])),
        ]


class test_filter_exr(test_nodeset_expr):
    class_name = 'filter_expr'
    test_cases = [
        ([nodeset_literal([ROOT, CHILD1]), predicates([predicate(TRUE)])],
         datatypes.nodeset([ROOT, CHILD1])),
        ([nodeset_literal([ROOT, CHILD1]), predicates([predicate(FALSE)])],
         datatypes.nodeset()),
        ]


if __name__ == '__main__':
    testsupport.test_main()
