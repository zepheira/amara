#!/usr/bin/env python

import sys
import unittest
import itertools
from xml.dom import Node
from amara.lib import inputsource, testsupport
from amara import tree
from amara.xpath import context, datatypes
from amara.xpath.expressions import expression
from amara.xpath.expressions.basics import string_literal, number_literal

########################################################################
# Literal expressions for testing expression results

# Create an independent "literal" base class as to not confuse the isinstance()
# checks throughout the compilation phase. The XPath parser cannot emit
# boolean or node-set literals!
class test_literal(expression):
    def __init__(self, literal):
        self._literal = self.return_value(literal)

    def compile_as_boolean(self, compiler):
        value = self._literal and datatypes.TRUE or datatypes.FALSE
        compiler.emit('LOAD_CONST', value)
        return

    def compile_as_number(self, compiler):
        try:
            value = datatypes.number(self._literal)
        except ValueError:
            value = datatypes.NOT_A_NUMBER
        compiler.emit('LOAD_CONST', value)
        return

    def compile_as_string(self, compiler):
        try:
            value = datatypes.string(self._literal)
        except ValueError:
            value = datatypes.EMPTY_STRING
        compiler.emit('LOAD_CONST', value)
        return

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)


class boolean_literal(test_literal):
    return_value = datatypes.boolean

    compile = test_literal.compile_as_boolean

    def __str__(self):
        return self._literal and 'true()' or 'false()'
TRUE = boolean_literal(True)
FALSE = boolean_literal(False)


class nodeset_literal(test_literal):
    return_value = datatypes.nodeset

    def compile_iterable(self, compiler):
        compiler.emit(# discard the context node
                      'POP_TOP',
                      # return the iterator directly
                      'LOAD_CONST', iter(self._literal))

    def compile_as_nodeset(self, compiler):
        compiler.emit('LOAD_CONST', datatypes.nodeset,
                      'LOAD_CONST', tuple(self._literal),
                      'CALL_FUNCTION', 1,
                      )
    compile = compile_as_nodeset

    def __str__(self):
        def nodestr(node):
            if isinstance(node, tree.Document):
                return '#document'
            if isinstance(node, (tree.Text, tree.Comment)):
                data = node.nodeValue
                if len(data) > 20:
                    data = data[:15] + '...' + data[-3:]
                return '(%s: %s)' % (node.nodeName, data)
            if isinstance(node, tree.Element):
                return '<%s>' % node.tagName
            if isinstance(node, tree.Attr):
                return '@%s' % node.name
        nodes = ', '.join(map(nodestr, self._literal))
        return '{%s}' % (nodes,)
EMPTY_NODESET = nodeset_literal([])


# Create IEEE 754 special numbers only possible from computations
class number_constant(number_literal):
    def __init__(self, name, literal):
        self._name = name
        number_literal.__init__(self, literal)
    def __str__(self):
        return self._name
NOT_A_NUMBER = number_constant('NaN', datatypes.NOT_A_NUMBER)
POSITIVE_INFINITY = number_constant('Infinity', datatypes.POSITIVE_INFINITY)
NEGATIVE_INFINITY = number_constant('-Infinity', datatypes.NEGATIVE_INFINITY)


# Node constants
src = inputsource("""<?xml version='1.0' encoding='ISO-8859-1'?>
<!DOCTYPE ROOT [
  <!ELEMENT CHILD2 (#PCDATA|GCHILD)*>
  <!ATTLIST CHILD2 attr1 CDATA #IMPLIED
                   CODE ID #REQUIRED>
]>
<?xml-stylesheet "Data" ?>
<ROOT>
  <!-- Test Comment -->
  <CHILD1 attr1="val1" attr31="31">
    <GCHILD name="GCHILD11"/>
    <GCHILD name="GCHILD12"/>
    Text1
  </CHILD1>
  <CHILD2 attr1="val2" CODE="1">
    <GCHILD name="GCHILD21"/>
    <GCHILD name="GCHILD22"/>
  </CHILD2>
  <foo:CHILD3 xmlns:foo="http://foo.com" foo:name="mike"/>
  <lang xml:lang="en">
    <foo xml:lang=""/>
    <foo/>
    <f\xf6\xf8/>
  </lang>
</ROOT>
<?no-data ?>
""", 'urn:domlette-test-tree')
DOC = tree.parse(src)

def children(node, type=Node.ELEMENT_NODE):
    return [ child for child in node if child.nodeType == type ]

# `#document` nodes
PI, PI2 = children(DOC, Node.PROCESSING_INSTRUCTION_NODE)
ROOT = DOC.documentElement
# `ROOT` nodes
COMMENT = children(ROOT, Node.COMMENT_NODE)[0]
CHILDREN = CHILD1, CHILD2, CHILD3, LANG = children(ROOT)
# `CHILD1` nodes
ATTR1 = CHILD1.getAttributeNodeNS(None, 'attr1')
ATTR31 = CHILD1.getAttributeNodeNS(None, 'attr31')
GCHILDREN1 = GCHILD11, GCHILD12 = children(CHILD1)
TEXT1 = CHILD1.lastChild
# `CHILD2` nodes
ATTR2 = CHILD2.getAttributeNodeNS(None, 'attr1')
IDATTR2 = CHILD2.getAttributeNodeNS(None, 'CODE')
GCHILDREN2 = GCHILD21, GCHILD22 = children(CHILD2)
# `CHILD3` nodes
ATTR3 = CHILD3.getAttributeNodeNS('http://foo.com', 'name')
# `lang` nodes
LCHILDREN = LCHILD1, LCHILD2, NONASCIIQNAME = children(LANG)


########################################################################
# unittest support

def _argstr(arg):
    #if isinstance(arg, unicode):
    #    return arg.encode('unicode_escape')
    # This is correct, we do want an exact type check
    if type(arg) in (tuple, list):
        return '(%s)' % ', '.join(_argstr(arg) for arg in arg)
    else:
        return unicode(arg)

class test_metaclass(type):
    # The name of module where the class to be tested is defined
    module_name = None
    # The name of the class to be tested
    class_name = None
    # The return type of the expression class' evaluate method
    return_type = None
    # list of test cases to add; item is a 2-item tuple of (args, expected)
    test_cases = ()

    def __init__(cls, name, bases, namespace):
        # load the expression factory
        if cls.module_name and cls.class_name:
            module = __import__(cls.module_name, {}, {}, [cls.class_name])
            factory = getattr(module, cls.class_name)
        # create the test methods
        digits = len(str(len(cls.test_cases)))
        for count, test in enumerate(cls.test_cases):
            args, expected, extra = cls.unpack_test_case(*test)
            if cls.return_type is not None:
                if not isinstance(expected, cls.return_type):
                    expected = cls.return_type(expected)
            test_method = cls.new_test_method(expected, factory, args, *extra)
            # build the docstring
            test_method.__doc__ = cls.class_name + _argstr(args)
            method_name = 'test_%s_%0*d' % (cls.class_name, digits, count)
            setattr(cls, method_name, test_method)

    def unpack_test_case(cls, args, expected, *extras):
        return args, expected, extras

    def new_test_method(cls, factory, args, expected, *extras):
        raise NotImplementedError


class test_xpath(unittest.TestCase, object):
    __metaclass__ = test_metaclass

    def assertIsInstance(self, obj, cls):
        if isinstance(cls, tuple):
            expected = ' or '.join(cls.__name__ for cls in cls)
        else:
            expected = cls.__name__
        msg = "expected %s, not %s" % (expected, type(obj).__name__)
        self.assertTrue(isinstance(obj, cls), msg)

    def assertEquals(self, first, second, msg=None):
        if msg is None:
            msg = '%r == %r' % (first, second)
        # convert nan's to strings to prevent IEEE 754-style compares
        if isinstance(first, float) and isinstance(second, float):
            if datatypes.number(first).isnan():
                first = 'NaN'
            if datatypes.number(second).isnan():
                second = 'NaN'
        # convert nodesets to lists to prevent XPath-style nodeset compares
        elif isinstance(first, list) and isinstance(second, list):
            first, second = list(first), list(second)
        return unittest.TestCase.assertEquals(self, first, second, msg)
    # update aliases as well
    assertEqual = failUnlessEqual = assertEquals


class test_expression(test_xpath):
    # The typed evaluate method (aka, evaluate_as_XXX())
    evaluate_method = None
    test_methods = ('evaluate',)

    class __metaclass__(test_metaclass):
        def __new__(cls, name, bases, namespace):
            if 'test_methods' not in namespace:
                if 'evaluate_method' in namespace:
                    test_methods = ('evaluate', namespace['evaluate_method'])
                    namespace['test_methods'] = test_methods
            return test_metaclass.__new__(cls, name, bases, namespace)

        def new_test_method(cls, expected, factory, args, *test_args):
            if not test_args:
                test_args = (context(DOC, 1, 1),)
            def test_method(self):
                expr = factory(*args)
                for method_name in self.test_methods:
                    result = getattr(expr, method_name)(*test_args)
                    self.assertIsInstance(result, type(expected))
                    self.assertEquals(result, expected)
            return test_method

if __name__ == '__main__':
    testsupport.test_main(
        # list of module names to test
        'test_basic_expr',      # basic expressions
        'test_function_calls',  # basic expressions
        'test_nodeset_expr',    # basic expressions
        'test_boolean_expr',    # number expressions
        'test_number_expr',     # number expressions
        )
