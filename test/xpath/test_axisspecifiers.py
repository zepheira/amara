#!/usr/bin/env python
from amara.lib import testsupport

from test_expressions import (
    test_xpath,
    # nodeset literals
    DOC, ROOT, CHILD1, CHILD2, CHILD3, LANG, PI2
    )


class test_axisspecifier(test_xpath):
    module_name = 'amara.xpath.locationpaths.axisspecifiers'
    class_name = 'axis_specifier'

    @classmethod
    def new_test_method(cls, expected, factory, args, node):
        def test_method(self):
            axis = factory(*args)
            result = list(axis.select(node))
            self.assertEquals(expected, result)
        return test_method


class test_ancestor_axis(test_axisspecifier):
    test_cases = [
        (['ancestor'], [ROOT, DOC], CHILD1),
        ]


class test_ancestor_or_self_axis(test_axisspecifier):
    test_cases = [
        (['ancestor-or-self'], [CHILD1, ROOT, DOC], CHILD1),
        ]


class test_descendant_axis(test_axisspecifier):
    test_cases = [
        (['descendant'], list(CHILD1), CHILD1),
        ]


class test_descendant_or_self_axis(test_axisspecifier):
    test_cases = [
        (['descendant-or-self'], [CHILD1]+list(CHILD1), CHILD1),
        ]


class test_child_axis(test_axisspecifier):
    test_cases = [
        (['child'], list(CHILD2), CHILD2),
        ]


class test_following_axis(test_axisspecifier):
    test_cases = [
        (['following'],
         [CHILD3.xml_following_sibling, LANG] + list(LANG) +
         [LANG.xml_following_sibling, PI2], CHILD3),
        ]


if __name__ == '__main__':
    testsupport.test_main()
