#!/usr/bin/env python
from amara.lib import testsupport
from amara.domlette import Node, Namespace
from amara.xpath import context
from amara.xpath.compiler import xpathcompiler
from amara.xpath.locationpaths.axisspecifiers import axis_specifier

from test_expressions import (
    test_xpath,
    # nodeset literals
    DOC, ROOT, CHILD1, CHILD3, PI, PI2, TEXT1, COMMENT
    )

NAMESPACES = {'bar': 'http://foo.com'}

class test_nodetests(test_xpath):
    module_name = 'amara.xpath.locationpaths.nodetests'

    @classmethod
    def new_test_method(cls, expected, factory, args, node,
                        principal_type=Node.ELEMENT_NODE):
        ctx = context(node, namespaces=NAMESPACES)
        compiler = xpathcompiler(ctx)
        # apply node-test using the default axis, 'child'
        nodes = iter(node)
        def test_method(self):
            node_test = factory(*args)
            node_filter = node_test.get_filter(compiler, principal_type)
            if node_filter:
                result = node_filter.select(ctx, nodes)
            else:
                result = nodes
            self.assertEquals(expected, list(result))
        return test_method


class test_name_test(test_nodetests):
    class_name = 'name_test'
    test_cases = [
        # (arg, ...), expected, context-node)
        (('*',), [ROOT], DOC),
        (('CHILD3',), [], CHILD3),
        (('bar:CHILD3',), [CHILD3], ROOT),
        (('bar:*',), [CHILD3], ROOT),
        ]


class test_node_type(test_nodetests):
    class_name = 'node_type'
    test_cases = [
        # (arg, ...), expected, context-node)
        (('node',), [PI, ROOT, PI2], DOC),
        (('text',), [TEXT1], CHILD1),
        (('comment',), [COMMENT], ROOT),
        (('processing-instruction',), [PI, PI2], DOC),
        (('processing-instruction', '"xml-stylesheet"'), [PI], DOC),
        ]

if __name__ == '__main__':
    testsupport.test_main()
