#!/usr/bin/env python
from amara import tree
from amara.lib import testsupport
from amara.xpath import context, datatypes
from amara.xpath.locationpaths import relative_location_path, location_step
from amara.xpath.locationpaths.axisspecifiers import axis_specifier as axis
from amara.xpath.locationpaths.nodetests import node_type, name_test
from amara.xpath.locationpaths.predicates import predicates, predicate

from test_expressions import (
    test_expression,
    DOC, ROOT, CHILD1, CHILD2, CHILD3, LANG, GCHILDREN1, GCHILDREN2, LCHILDREN
    )

CONTEXT_ROOT = context(ROOT, 1, 1)
CONTEXT_CHILD1 = context(CHILD1, 1, 3)

CHILD_STEP = location_step(axis('child'), name_test('*'))

class test_locationpaths(test_expression):
    module_name = 'amara.xpath.locationpaths'
    evaluate_method = 'evaluate_as_nodeset'
    return_type = datatypes.nodeset


class test_absolute_location_path(test_locationpaths):
    class_name = 'absolute_location_path'
    test_cases = [
        # /
        ([], datatypes.nodeset([DOC]), CONTEXT_CHILD1),
        # /child::*
        ([relative_location_path(CHILD_STEP)],
         datatypes.nodeset([ROOT]), CONTEXT_CHILD1),
        # /descendant::*
        ([relative_location_path(location_step(axis('descendant'),
                                 name_test('*')))],
         datatypes.nodeset([ROOT, CHILD1] + GCHILDREN1 + [CHILD2] +
                           GCHILDREN2 + [CHILD3, LANG] + LCHILDREN),
         CONTEXT_CHILD1),
        ]

class test_relative_location_path(test_locationpaths):
    class_name = 'relative_location_path'
    test_cases = [
        # <CHILD1>/ancestor::*
        ([location_step(axis('ancestor'), name_test('*'))],
         datatypes.nodeset([ROOT]), CONTEXT_CHILD1),
        # <CHILD1>/ancestor-or-self::*
        ([location_step(axis('ancestor-or-self'), name_test('*'))],
         datatypes.nodeset([ROOT, CHILD1]), CONTEXT_CHILD1),
        # <ROOT>/descendant-or-self::GCHILD
        ([location_step(axis('descendant-or-self'), name_test('GCHILD'))],
         datatypes.nodeset(GCHILDREN1 + GCHILDREN2), CONTEXT_ROOT),
        # <CHILD1>/child::GCHILD
        ([location_step(axis('child'), name_test('GCHILD'))],
         datatypes.nodeset(GCHILDREN1), CONTEXT_CHILD1),
        ]


class test_abbreviated_absolute_location_path(test_locationpaths):
    class_name = 'abbreviated_absolute_location_path'
    test_cases = [
        # //child::*
        ([relative_location_path(CHILD_STEP)],
         datatypes.nodeset([ROOT, CHILD1] + GCHILDREN1 + [CHILD2] +
                           GCHILDREN2 + [CHILD3, LANG] + LCHILDREN),
         CONTEXT_CHILD1),
        ]


class test_abbreviated_relative_location_path(test_locationpaths):
    class_name = 'abbreviated_relative_location_path'
    test_cases = [
        # child::*//child::*
        ([relative_location_path(CHILD_STEP), CHILD_STEP],
         datatypes.nodeset(GCHILDREN1 + GCHILDREN2 + LCHILDREN),
         CONTEXT_ROOT),
        ]


if __name__ == '__main__':
    testsupport.test_main()