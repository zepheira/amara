#!/usr/bin/env python

from amara.lib import inputsource
from amara import tree
from amara.test import test_main
from amara.test.xpath import test_xpath, test_metaclass
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
            if isinstance(node, tree.entity):
                return '#document'
            if isinstance(node, (tree.text, tree.comment)):
                data = node.xml_value
                if len(data) > 20:
                    data = data[:15] + '...' + data[-3:]
                return '(#%s: %s)' % (node.xml_type, data)
            if isinstance(node, tree.element):
                return '<%s>' % node.xml_qname
            if isinstance(node, tree.attribute):
                return '@%s' % node.xml_qname
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

def children(node, type=tree.element):
    return [ child for child in node if isinstance(child, type) ]

# `#document` nodes
PI, PI2 = children(DOC, tree.processing_instruction)
ROOT = children(DOC, tree.element)[0]
# `ROOT` nodes
COMMENT = children(ROOT, tree.comment)[0]
CHILDREN = CHILD1, CHILD2, CHILD3, LANG = children(ROOT)
# `CHILD1` nodes
ATTR1 = CHILD1.xml_attributes.getnode(None, 'attr1')
ATTR31 = CHILD1.xml_attributes.getnode(None, 'attr31')
GCHILDREN1 = GCHILD11, GCHILD12 = children(CHILD1)
TEXT1 = CHILD1.xml_children[-1]
# `CHILD2` nodes
ATTR2 = CHILD2.xml_attributes.getnode(None, 'attr1')
IDATTR2 = CHILD2.xml_attributes.getnode(None, 'CODE')
GCHILDREN2 = GCHILD21, GCHILD22 = children(CHILD2)
# `CHILD3` nodes
ATTR3 = CHILD3.xml_attributes.getnode('http://foo.com', 'name')
# `lang` nodes
LCHILDREN = LCHILD1, LCHILD2, NONASCIIQNAME = children(LANG)


########################################################################
# unittest support

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
    test_main(# list of module names to test
              'test_basic_expr',        # basic expressions
              'test_function_calls',    # basic expressions
              'test_nodeset_expr',      # basic expressions
              'test_boolean_expr',      # number expressions
              'test_number_expr',       # number expressions
              )
