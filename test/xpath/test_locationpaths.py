#!/usr/bin/env python
from amara import tree
from amara.lib import testsupport
from amara.xpath import context, datatypes
from amara.xpath.locationpaths import (absolute_location_path, relative_location_path,
                                       location_step, abbreviated_absolute_location_path,
                                       abbreviated_relative_location_path)
from amara.xpath.locationpaths.axisspecifiers import axis_specifier as axis
from amara.xpath.locationpaths.nodetests import name_test

from test_expressions import (
    base_expression,
    DOC, ROOT, CHILD1, CHILD2, CHILD3, LANG, GCHILDREN1, GCHILDREN2, LCHILDREN
    )

CONTEXT_ROOT = context(ROOT, 1, 1)
CONTEXT_CHILD1 = context(CHILD1, 1, 3)

CHILD_STEP = location_step(axis('child'), name_test('*'))


def test_absolute_location_path():
    for args, expected in (
        ([], datatypes.nodeset([DOC])),
        # /child::*
        ([relative_location_path(CHILD_STEP)], datatypes.nodeset([ROOT])),
        # /descendant::*
        ([relative_location_path(location_step(axis('descendant'), name_test('*')))],
         datatypes.nodeset([ROOT, CHILD1] + GCHILDREN1 + [CHILD2] +
                           GCHILDREN2 + [CHILD3, LANG] + LCHILDREN)),
        ):
        result = absolute_location_path(*args).evaluate_as_nodeset(CONTEXT_CHILD1)
        assert isinstance(result, datatypes.nodeset)
        assert result == expected, (result, expected)

def test_relative_location_path():
    for args, expected, ctx in (
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
        ):
        result = relative_location_path(*args).evaluate_as_nodeset(ctx)
        assert isinstance(result, datatypes.nodeset)
        assert result == expected, (result, expected)

def test_abbreviated_absolute_location_path():
    # //child::*
    result = abbreviated_absolute_location_path(relative_location_path(CHILD_STEP)
                                                ).evaluate_as_nodeset(CONTEXT_CHILD1)
    assert isinstance(result, datatypes.nodeset)
    expected = datatypes.nodeset([ROOT, CHILD1] + GCHILDREN1 + [CHILD2] +
                                 GCHILDREN2 + [CHILD3, LANG] + LCHILDREN)
    assert result == expected, (result, expected)


def test_abbreviated_relative_location_path():
    # child::*//child::*
    result = abbreviated_relative_location_path(relative_location_path(CHILD_STEP), CHILD_STEP
                                                ).evaluate_as_nodeset(CONTEXT_ROOT)
    assert isinstance(result, datatypes.nodeset)
    expected = datatypes.nodeset(GCHILDREN1 + GCHILDREN2 + LCHILDREN)
    assert result == expected, (result, expected)

if __name__ == '__main__':
    raise SystemExit('Use nosetests')
