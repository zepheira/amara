########################################################################
# amara/xslt/xpatterns/__init__.py
"""
Implement Patterns according to the XSLT spec
"""

from xml.dom import Node
from amara.xpath.locationpaths import nodetests

child_axis = Node.ELEMENT_NODE
attribute_axis = Node.ATTRIBUTE_NODE

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
        if axis_type == Node.ATTRIBUTE_NODE:
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

    def match(self, context, node, principalType=None):
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
            if axis == Node.ATTRIBUTE_NODE:
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
        self._predicates = _predicates
        self.name_key = node_test.name_key
        return

    def match(self, context, node, principalType):
        
        if principalType == Node.ATTRIBUTE_NODE:
            nodes = node.xml_parent.xml_attributes.nodes()
        elif node.parentNode:
            nodes = node.xml_parent.xml_children
        else:
            # Must be a document
            return False

        # Pass through the NodeTest (genexp)
        nodes = ( node for node in nodes
                  if self._node_test.match(context, node, principalType) )

        # Child and attribute axes are forward only
        nodes = self._predicates.filter(nodes, context, reverse=0)
        return node in nodes

    def __str__(self):
        return str(self._node_test) + str(self._predicates)


class document_test(nodetests.node_test):

    priority = 0.5
    node_type = Node.DOCUMENT_NODE

    def match(self, context, node, principalType):
        return node.xml_node_type == Node.DOCUMENT_NODE

    def __str__(self):
        return '/'


class id_key_test(nodetests.node_test):

    priority = 0.5

    def __init__(self, function):
        self._function = function

    def match(self, context, node, principalType):
        return node in self._function.evaluate(context)

    def __str__(self):
        return str(self._function)


import _parser
class parser(_parser.parser):

    _parse = _parser.parser.parse

    def parse(self, expr):
        """Parses the string `expr` into an AST"""
        try:
            return self._parse(expr)
        except _parser.error, error:
            raise XsltError(XsltError.INVALID_PATTERN, line=error.lineno,
                            column=error.offset, text=error.msg)


parse = parser().parse

if __name__ == '__main__':
    import sys
    sys.exit(_parser.console().cmdloop())
