#!/usr/bin/env python
from amara.xpath import context, datatypes
from amara.xpath.locationpaths.predicates import predicates, predicate
from amara.xpath.expressions.nodesets import union_expr, path_expr, filter_expr

from test_expressions import (
    base_expression,
    # boolean literals
    TRUE, FALSE,
    # nodeset literals
    nodeset_literal, ROOT, CHILD1, CHILD2, CHILD3
    )

CONTEXT = context(CHILD1, 1, 1)


def _check_nodeset_result(result, expected):
    assert isinstance(result, datatypes.nodeset)
    result = list(result)
    expected = list(expected)
    assert result == expected, (result, expected)

def test_union_exr_new():
    result = union_expr(nodeset_literal([ROOT, CHILD1]), nodeset_literal([ROOT])
                        ).evaluate_as_nodeset(CONTEXT)
    _check_nodeset_result(result, datatypes.nodeset([ROOT, CHILD1]))


def test_path_exr():
    result = path_expr(nodeset_literal([ROOT, CHILD1]), '/', nodeset_literal([ROOT])
                       ).evaluate_as_nodeset(CONTEXT)
    _check_nodeset_result(result, datatypes.nodeset([ROOT]))


def test_filter_exr():
    result = filter_expr(nodeset_literal([ROOT, CHILD1]), predicates([predicate(TRUE)])
                         ).evaluate_as_nodeset(CONTEXT)
    _check_nodeset_result(result, datatypes.nodeset([ROOT, CHILD1]))

    result = filter_expr(nodeset_literal([ROOT, CHILD1]), predicates([predicate(FALSE)])
                         ).evaluate_as_nodeset(CONTEXT)
    _check_nodeset_result(result, datatypes.nodeset())

if __name__ == '__main__':
    raise SystemExit("use nosetests")
