#!/usr/bin/env python

# nodeset literals
from test_expressions import (
    DOC, ROOT, CHILD1, CHILD2, CHILD3, LANG, PI2
    )

from amara.xpath.locationpaths.axisspecifiers import axis_specifier

def test_ancestor_axis():
    assert list(axis_specifier('ancestor').select(CHILD1)) == [ROOT, DOC]

def test_ancestor_or_self_axis():
    assert list(axis_specifier('ancestor-or-self').select(CHILD1)) == [CHILD1, ROOT, DOC]

def test_descendant_axis():
    assert list(axis_specifier('descendant').select(CHILD1)) == list(CHILD1)

def test_descendant_or_self_axis():
    assert list(axis_specifier('descendant-or-self').select(CHILD1)) == [CHILD1] + list(CHILD1)

def test_child_axis():
    assert list(axis_specifier('child').select(CHILD2)) == list(CHILD2)

def test_following_axis():
    assert list(axis_specifier('following').select(CHILD3)) == (
        [CHILD3.xml_following_sibling, LANG] + list(LANG) + [LANG.xml_following_sibling, PI2])


if __name__ == '__main__':
    raise SystemExit("Run using 'nosetests'")
