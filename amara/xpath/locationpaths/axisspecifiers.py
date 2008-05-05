#######################################################################
# amara/xpath/axisspecifiers.py
"""
A parsed token that represents an axis specifier.
"""

from xml.dom import Node

from amara.domlette import XPathNamespace

# Bind the class name in the global scope so that the metaclass can be
# safely called for the construction of the initial class.
axis_specifier = None
class axis_specifier(object):

    _classmap = {}
    principal_type = Node.ELEMENT_NODE
    reverse = False

    class __metaclass__(type):
        if __debug__:
            def __new__(cls, name, bases, namespace):
                if axis_specifier is not None:
                    assert 'name' in namespace
                return type.__new__(cls, name, bases, namespace)

        def __init__(cls, name, bases, namespace):
            if axis_specifier is not None:
                cls._classmap[cls.name] = cls
                # Allow axis specifier classes to be instaniated directly
                cls.__new__ = object.__new__

    def __new__(cls, name):
        return object.__new__(cls._classmap[name])

    def select(self, node):
        raise NotImplementedError

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)

    def __repr__(self):
        ptr = id(self)
        if ptr < 0: ptr += 0x100000000L
        return '<%s at 0x%x: %s>' % (self.__class__.__name__, ptr, self)

    def __str__(self):
        return self.name


class ancestor_axis(axis_specifier):
    name = 'ancestor'
    reverse = True
    def select(self, node):
        """Select all of the ancestors including the root"""
        node = node.parentNode
        while node:
            yield node
            node = node.parentNode
        return
    try:
        from _axes import ancestor_axis as select
    except ImportError:
        pass


class ancestor_or_self_axis(axis_specifier):
    name = 'ancestor-or-self'
    reverse = True
    def select(self, node):
        """Select all of the ancestors including ourselves through the root"""
        yield node
        node = node.parentNode
        while node:
            yield node
            node = node.parentNode
        return
    try:
        from _axes import ancestor_or_self_axis as select
    except ImportError:
        pass


class attribute_axis(axis_specifier):
    name = 'attribute'
    principal_type = Node.ATTRIBUTE_NODE
    def select(self, node):
        """Select all of the attributes from the context node"""
        return (node.xml_attributes)
    try:
        from _axes import attribute_axis as select
    except ImportError:
        pass


class child_axis(axis_specifier):
    name = 'child'
    def select(self, node):
        """Select all of the children of the context node"""
        return iter(node)
    try:
        from _axes import child_axis as select
    except ImportError:
        pass


class descendant_axis(axis_specifier):
    name = 'descendant'
    def select(self, node):
        descendants = self.select
        node_type = Node.ELEMENT_NODE
        for child in node:
            yield child
            if child.nodeType == node_type:
                for x in descendants(child): yield x
        return
    try:
        from _axes import descendant_axis as select
    except ImportError:
        pass


class descendant_or_self_axis(descendant_axis):
    name = 'descendant-or-self'
    _descendants = descendant_axis.select
    def select(self, node):
        """Select the context node and all of its descendants"""
        yield node
        for x in self._descendants(node): yield x
        return
    try:
        from _axes import descendant_or_self_axis as select
    except ImportError:
        pass


class following_axis(descendant_axis):
    name = 'following'
    _descendants = descendant_axis.select
    def select(self, node):
        """
        Select all of the nodes the follow the context node,
        not including descendants.
        """
        descendants = self._descendants
        while node:
            sibling = node.nextSibling
            while sibling:
                yield sibling
                for x in descendants(sibling): yield x
                sibling = sibling.nextSibling
            node = node.parentNode
        return


class following_sibling_axis(axis_specifier):
    name = 'following-sibling'
    def select(self, node):
        """Select all of the siblings that follow the context node"""
        sibling = node.nextSibling
        while sibling:
            yield sibling
            sibling = sibling.nextSibling
        return
    try:
        from _axes import following_sibling_axis as select
    except ImportError:
        pass


class namespace_axis(axis_specifier):
    name = 'namespace'
    principal_type = XPathNamespace.XPATH_NAMESPACE_NODE

    def select(self, node):
        """Select all of the namespaces from the context node."""
        return iter(node.xml_namespaces)


class parent_axis(axis_specifier):
    name = 'parent'
    reverse = True
    def select(self, node):
        """Select the parent of the context node"""
        parent_node = node.parentNode
        if parent_node:
            yield parent_node
        return


class preceding_axis(axis_specifier):
    name = 'preceding'
    reverse = True
    def select(self, node):
        """
        Select all of the nodes the precede the context node, not
        including ancestors.
        """
        def preceding(node):
            while node:
                if node.lastChild:
                    for x in preceding(current_node.lastChild): yield x
                yield node
                node = node.previousSibling
            return

        while node:
            for x in preceding(node.previousSibling): yield x
            node = node.parentNode
        return


class preceding_sibling_axis(axis_specifier):
    name = 'preceding-sibling'
    reverse = True
    def select(self, node):
        """Select all of the siblings that precede the context node"""
        sibling = node.previousSibling
        while sibling:
            yield sibling
            sibling = sibling.previousSibling
        return


class self_axis(axis_specifier):
    name = 'self'
    def select(self, node):
        """Select the context node"""
        yield node
