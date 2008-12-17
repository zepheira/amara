########################################################################
# amara/xslt/xpatterns/__init__.py
"""
Implement Patterns according to the XSLT spec
"""

from amara import tree
from amara.xpath.locationpaths import nodetests
from amara.xslt import XsltError

child_axis = tree.element
attribute_axis = tree.attribute

class patterns(tuple):

    def match(self, context, node):
        for pattern in self:
            if pattern.match(context, node):
                return True
        return False

    def pprint(self, indent=''):
        print indent + repr(self)
        for pattern in patterns:
            pattern.pprint(indent + '  ')
        return

    def __str__(self):
        return ' | '.join(map(str, self))

    def __repr__(self):
        return '<Patterns at %x: %s>' % (id(self), str(self))


class pattern(nodetests.node_test):
    def __init__(self, steps):
        # The steps are already in reverse order
        self.steps = steps
        self.priority = 0.5
        axis_type, node_test, ancestor = steps[0]
        if axis_type == attribute_axis:
            node_type = axis_type
        else:
            node_type = node_test.node_type
        self.node_type = node_type
        if len(steps) > 1:
            node_test, axis_type = self, None
            self.name_key = node_test.name_key
        self.node_test = node_test
        self.axis_type = axis_type
        return

    def match(self, context, node, principal_type=None):
        (axis_type, node_test, ancestor) = self.steps[0]
        if not node_test.match(context, node, axis_type):
            return 0
        for (axis_type, node_test, ancestor) in self.steps[1:]:
            # Move up the tree
            node = node.xml_parent
            if ancestor:
                while node:
                    if node_test.match(context, node, axis_type):
                        break
                    node = node.xml_parent
                else:
                    # We made it to the document without a match
                    return 0
            elif node is None: return 0
            elif not node_test.match(context, node, axis_type):
                return 0
        return 1

    def pprint(self, indent=''):
        print indent + repr(self)

    def __str__(self):
        result = ''
        for (axis, test, ancestor) in self.steps:
            if axis == attribute_axis:
                step = '@' + str(test)
            else:
                step = str(test)
            result = step + (ancestor and '//' or '/') + result
        # remove trailing slash
        return result[:-1]


class predicated_test(nodetests.node_test):

    priority = 0.5

    def __init__(self, node_test, predicates):
        self._node_test = node_test
        self._predicates = predicates
        self.name_key = node_test.name_key
        self.node_type = node_test.node_type
        return

    def match(self, context, node, principal_type):
        parent = node.xml_parent
        if principal_type == tree.attribute:
            nodes = parent.xml_attributes.nodes()
        elif not parent:
            # Must be a document
            return False
        else:
            # Amara nodes are iterable (over their children)
            nodes = parent

        # Pass through the NodeTest (genexp)
        nodes = ( node for node in nodes
                  if self._node_test.match(context, node, principal_type) )

        # Child and attribute axes are forward only
        nodes = self._predicates.filter(nodes, context, reverse=0)
        return node in nodes

    def __str__(self):
        return str(self._node_test) + str(self._predicates)


class document_test(nodetests.node_test):

    priority = 0.5
    node_type = tree.entity

    def match(self, context, node, principal_type):
        return isinstance(node, self.node_type)

    def __str__(self):
        return '/'


class id_key_test(nodetests.node_test):

    priority = 0.5
    node_type = tree.node

    def __init__(self, function):
        self._function = function

    def match(self, context, node, principal_type):
        return node in self._function.evaluate(context)

    def __str__(self):
        return str(self._function)


import _parser as _xpatternparser
class parser(_xpatternparser.parser):

    _parse = _xpatternparser.parser.parse

    def parse(self, expr):
        """Parses the string `expr` into an AST"""
        try:
            return self._parse(expr)
        except _xpatternparser.error, error:
            raise XsltError(XsltError.INVALID_PATTERN, line=error.lineno,
                            column=error.offset, text=error.msg)

_parser = parser()
_parse = _parser._parse
parse = _parser.parse

if __name__ == '__main__':
    import sys
    sys.exit(_xpatternparser.console().cmdloop())
