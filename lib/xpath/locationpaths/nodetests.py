########################################################################
# amara/xpath/locationpaths/nodetests.py
"""
A parsed token that represents a node test.
"""

from xml.dom import Node

from amara import tree
from amara.xpath import XPathError
from amara.xpath.locationpaths import _nodetests

__all__ = ('node_test', 'name_test')

class node_test(object):

    priority = -0.5
    node_type = None
    # By specifing a name_key of None, this test will fall into the 'general'
    # category for the principal type
    name_key = None

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)

    def __repr__(self):
        ptr = id(self)
        if ptr < 0: ptr += 0x100000000L
        return '<%s at 0x%x: %s>' % (self.__class__.__name__, ptr, self)

# -- NodeType classes -------------------------------------------------

class node_type(node_test):

    _classmap = {}

    class __metaclass__(type):
        def __init__(cls, name, bases, namespace):
            if 'name' in namespace:
                cls._classmap[cls.name] = cls

    def __new__(cls, name, *args):
        return object.__new__(cls._classmap[name])

    def get_filter(self, compiler, principal_type):
        return _nodetests.nodefilter(self.node_type)

    def match(self, context, node, principal_type=tree.element):
        """
        The principalType is discussed in section [2.3 Node Tests]
        of the XPath 1.0 spec.  Only attribute and namespace axes
        differ from the default of elements.
        """
        return isinstance(node, self.node_type)

    def __str__(self):
        return self.name + '()'


class any_node_test(node_type):
    name = 'node'
    node_type = tree.node

    def get_filter(self, compiler, principal_type):
        return None


class comment_test(node_type):
    name = 'comment'
    node_type = tree.comment


class text_test(node_type):
    name = 'text'
    node_type = tree.text


class processing_instruction_test(node_type):
    name = 'processing-instruction'
    node_type = tree.processing_instruction

    def __init__(self, name, target=None):
        if target:
            self.priority = 0
            if target[:1] not in ('"', "'"):
                raise SyntaxError("Invalid literal: %r" % target)
            self._target = target[1:-1]
        else:
            self.priority = -0.5
            self._target = None

    def get_filter(self, compiler, principal_type):
        return _nodetests.nodefilter(self.node_type, self._target)

    def match(self, context, node, principal_type=tree.element):
        if isinstance(node, principal_type):
            if self._target:
                return node.target == self._target
            return True
        return False

    def __str__(self):
        if self._target:
            target = self._target.encode('unicode_escape')
            return '%s("%s")' % (self.name, target.replace('"', '\\"'))
        return node_type.__str__(self)

# -- NameTest classes -------------------------------------------------

class name_test(node_test):

    node_type = tree.element

    def __new__(cls, name):
        if name[-1:] == '*':
            if ':' in name:
                cls = namespace_test
            else:
                cls = principal_type_test
        elif ':' in name:
            cls = qualified_name_test
        else:
            cls = local_name_test
        return object.__new__(cls)


class principal_type_test(name_test):

    def get_filter(self, compiler, principal_type):
        return _nodetests.nodefilter(principal_type)

    def match(self, context, node, principal_type=tree.element):
        return isinstance(node, principal_type)

    def __str__(self):
        return '*'


class local_name_test(name_test):

    priority = 0

    def __init__(self, name):
        self._name = name
        self.name_key = (None, name)

    def get_filter(self, compiler, principal_type):
        return _nodetests.nodefilter(principal_type, None, self._name)

    def match(self, context, node, principal_type=tree.element):
        # NameTests do not use the default namespace, just as attributes
        if isinstance(node, principal_type) and not node.xml_namespace:
            return node.xml_local == self._name
        return 0

    def __str__(self):
        return self._name


class namespace_test(name_test):

    priority = -0.25

    def __init__(self, name):
        self._prefix = name[:name.index(':')]

    def get_filter(self, compiler, principal_type):
        try:
            namespace = compiler.namespaces[self._prefix]
        except KeyError:
            raise XPathError(XPathError.UNDEFINED_PREFIX, prefix=self._prefix)
        return _nodetests.nodefilter(principal_type, namespace, None)

    def match(self, context, node, principal_type=tree.element):
        if not isinstance(node, principal_type):
            return False
        try:
            return node.xml_namespace == context.namespaces[self._prefix]
        except KeyError:
            raise RuntimeException(RuntimeException.UNDEFINED_PREFIX,
                                   prefix=self._prefix)

    def __str__(self):
        return self._prefix + ':*'


class qualified_name_test(name_test):

    priority = 0

    def __init__(self, name):
        self.name_key = name.split(':', 1)

    def get_filter(self, compiler, principal_type):
        prefix, local_name = self.name_key
        try:
            namespace = compiler.namespaces[prefix]
        except KeyError:
            raise XPathError(XPathError.UNDEFINED_PREFIX, prefix=prefix)
        return _nodetests.nodefilter(principal_type, namespace, local_name)

    def match(self, context, node, principal_type=tree.element):
        if isinstance(node, principal_type):
            prefix, local_name = self.name_key
            if node.xml_local == local_name:
                try:
                    return node.xml_namespace == context.namespaces[prefix]
                except KeyError:
                    raise RuntimeException(RuntimeException.UNDEFINED_PREFIX,
                                           prefix=prefix)
        return 0

    def __str__(self):
        return ':'.join(self.name_key)
