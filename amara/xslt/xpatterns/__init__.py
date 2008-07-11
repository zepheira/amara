########################################################################
# amara/xslt/xpatterns/__init__.py
"""
Implement Patterns according to the XSLT spec

Copyright 1999-2004 Fourthought, Inc. (USA).
Detailed license and copyright information: http://4suite.org/COPYRIGHT
Project home, documentation, distributions: http://4suite.org/
"""

from xml.dom import Node

ChildAxis = Node.ELEMENT_NODE
AttributeAxis = Node.ATTRIBUTE_NODE

class patterns:
    def __init__(self, patterns):
        self.patterns = patterns

    def getShortcuts(self, namespaces):
        return [ (pattern.getShortcut(), pattern.getQuickKey(namespaces))
                 for pattern in self.patterns ]

    def match(self, context, node):
        for pattern in self.patterns:
            if pattern.match(context, node):
                return 1
        return 0

    def pprint(self, indent=''):
        print indent + str(self)
        for pattern in self.patterns:
            pattern.pprint(indent + '  ')
        return

    def __str__(self):
        return '<Patterns at %x: %s>' % (id(self), repr(self))

    def __repr__(self):
        result = repr(self.patterns[0])
        for pattern in self.patterns[1:]:
            result = result + ' | ' + repr(pattern)
        return result

class pattern:
    def __init__(self, steps):
        # The steps are already in reverse order
        self.steps = steps
        self.priority = 0.5
        return

    def getShortcut(self):
        #FIXME: what's up with this description?
        # A shortcut is (pattern, (pattern, extra_arg))
        if len(self.steps) == 1:
            (axis_type, node_test, ancestor) = self.steps[0]
            shortcut = (node_test, axis_type)
        else:
            shortcut = (self, None)
        return shortcut

    def getQuickKey(self, namespaces):
        (axis_type, node_test, ancestor) = self.steps[0]
        (node_type, expanded_name) = node_test.getQuickKey(namespaces)
        if axis_type == Node.ATTRIBUTE_NODE:
            node_type = axis_type
        return (node_type, expanded_name)

    def match(self, context, node, dummy=None):
        (axis_type, node_test, ancestor) = self.steps[0]
        if not node_test.match(context, node, axis_type):
            return 0
        for (axis_type, node_test, ancestor) in self.steps[1:]:
            # Move up the tree
            if axis_type == Node.ATTRIBUTE_NODE:
                node = node.ownerElement
            else:
                node = node.parentNode
            if ancestor:
                while node:
                    if node_test.match(context, node, axis_type):
                        break
                    if axis_type == Node.ATTRIBUTE_NODE:
                        node = node.ownerElement
                    else:
                        node = node.parentNode
                else:
                    # We made it to the document without a match
                    return 0
            elif node is None: return 0
            elif not node_test.match(context, node, axis_type):
                return 0
        return 1

    def pprint(self, indent=''):
        print indent + str(self)

    def __str__(self):
        return '<Pattern at %x: %s>' % (id(self), repr(self))
    
    def __repr__(self):
        result = ''
        for (axis, test, ancestor) in self.steps:
            if axis == Node.ATTRIBUTE_NODE:
                step = '@' + repr(test)
            else:
                step = repr(test)
            result = step + (ancestor and '//' or '/') + result
        # remove trailing slash
        return result[:-1]


class predicated_node_test:
    def __init__(self, nodeTest, predicateList):
        self.nodeTest = nodeTest
        self.predicates = predicateList
        self.priority = 0.5
        return

    def getQuickKey(self, namespaces):
        return self.nodeTest.getQuickKey(namespaces)

    def match(self, context, node, principalType):
        if principalType == Node.ATTRIBUTE_NODE:
            node_set = node.ownerElement.attributes.values()
        elif node.parentNode:
            node_set = node.parentNode.childNodes
        else:
            # Must be a document
            return 0

        # Pass through the NodeTest
        node_set = [ n for n in node_set if self.nodeTest.match(context, n, principalType) ]

        # Child and attribute axes are forward only
        node_set = self.predicates.filter(node_set, context, reverse=0)
        return node in node_set

    def __str__(self):
        return '<%s at %x: %s>' % (
            self.__class__.__name__,
            id(self),
            repr(self))

    def __repr__(self):
        return repr(self.nodeTest) + repr(self.predicates)

class document_node_test:
    def __init__(self):
        self.priority = 0.5

    def getQuickKey(self, namespaces):
        return (Node.DOCUMENT_NODE, None)

    def match(self, context, node, principalType):
        return node.nodeType == Node.DOCUMENT_NODE

    def __str__(self):
        return '<%s at %x: %s>' % (
            self.__class__.__name__,
            id(self),
            repr(self))

    def __repr__(self):
        return '/'

class id_key_node_test:
    def __init__(self, idOrKey):
        self.priority = 0.5
        self.idOrKey = idOrKey

    def getQuickKey(self, namespaces):
        return (None, None)

    def match(self, context, node, principalType):
        return node in self.idOrKey.evaluate(context)

    def __str__(self):
        return '<%s at %x: %s>' % (
            self.__class__.__name__,
            id(self),
            repr(self))

    def __repr__(self):
        return repr(self.idOrKey)


def parse(string):
    return