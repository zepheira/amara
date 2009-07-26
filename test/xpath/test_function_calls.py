#!/usr/bin/env python
from amara import tree
from amara.xpath import context, datatypes
from amara.xpath.expressions.basics import string_literal, number_literal

from test_expressions import (
    base_expression,
    # boolean literals
    TRUE, FALSE,
    # number literals (for special values)
    NOT_A_NUMBER, POSITIVE_INFINITY, NEGATIVE_INFINITY,
    # nodeset literals
    nodeset_literal, ROOT, CHILD1, CHILD2, CHILD3, LCHILD1, LCHILD2
    )

# contexts for nodeset {CHILD1, CHILD2, CHILD3}
CONTEXT1 = context(CHILD1, 1, 3)
CONTEXT2 = context(CHILD2, 2, 3)
# contexts for nodeset {LCHILD1, LCHILD2, NONASCIIQNAME}
CONTEXTLANG1 = context(LCHILD1, 1, 3)
CONTEXTLANG2 = context(LCHILD2, 2, 3)

DOC = tree.entity()
EGG1 = DOC.xml_append(tree.element(None, 'egg0'))
EGG1.xml_append(tree.text('0'))
EGG2 = DOC.xml_append(tree.element(None, 'egg1'))
EGG2.xml_append(tree.text('1'))
EGG3 = DOC.xml_append(tree.element(None, 'egg0'))
EGG3.xml_append(tree.text('0'))
EGG4 = DOC.xml_append(tree.element(None, 'egg1'))
EGG4.xml_append(tree.text('1'))
EGG5 = DOC.xml_append(tree.element(None, 'egg0'))
EGG5.xml_append(tree.text('0'))


from amara.xpath.expressions.functioncalls import function_call

def test_last_function():
    for context in (CONTEXT1, CONTEXT2):
        result = function_call('last', ()).evaluate_as_number(context)
        assert isinstance(result, datatypes.number)
        assert result == datatypes.number(3)
    

class test_position_function():
    for context, expected in ( (CONTEXT1, datatypes.number(1)) ,
                               (CONTEXT2, datatypes.number(2)) ):
        result = function_call('position', ()).evaluate_as_number(context)
        assert isinstance(result, datatypes.number)
        assert result == expected


def test_count_function():
    node = function_call('count', (nodeset_literal([ROOT, CHILD1]),))
    result = node.evaluate_as_number(CONTEXT1)
    assert isinstance(result, datatypes.number)
    assert result == datatypes.number(2)


def test_id_function():
    for args, expected in (
        ([number_literal('1')], datatypes.nodeset([CHILD2])),
        ([string_literal('"1 1"')], datatypes.nodeset([CHILD2])),
        ([string_literal('"0"')], datatypes.nodeset()),
        ([string_literal('"0 1"')], datatypes.nodeset([CHILD2])),
        ([string_literal('"0 1 1"')], datatypes.nodeset([CHILD2])),
        ([string_literal('"0 0 1 1"')], datatypes.nodeset([CHILD2])),
        ([nodeset_literal([EGG1])], datatypes.nodeset()),
        ([nodeset_literal([EGG1, EGG2])], datatypes.nodeset([CHILD2])),
        ([nodeset_literal([EGG1, EGG2, EGG3])], datatypes.nodeset([CHILD2])),
        ([nodeset_literal([EGG1, EGG2, EGG3, EGG4])], datatypes.nodeset([CHILD2])),
        ):
        result = function_call('id', args).evaluate_as_nodeset(CONTEXT1)
        assert isinstance(result, datatypes.nodeset)
        result = list(result)
        expected = list(expected)
        assert result == expected, (args, result, expected)

def test_local_name_function():
    for arg, expected in (
        (nodeset_literal([]), datatypes.string()),
        (nodeset_literal([CHILD3]), datatypes.string('CHILD3')),
        ):
        result = function_call('local-name', [arg]).evaluate_as_string(CONTEXT1)
        assert isinstance(result, datatypes.string)
        assert result == expected, (result, expected)

def test_namespace_uri_function():
    for arg, expected in (
        (nodeset_literal([]), datatypes.string()),
        (nodeset_literal([CHILD3]), datatypes.string('http://foo.com'))
        ):
        result = function_call('namespace-uri', [arg]).evaluate_as_string(CONTEXT1)
        assert isinstance(result, datatypes.string)
        assert result == expected, (result, expected)

def test_name_function():
    result = function_call('name', [nodeset_literal([CHILD3])]).evaluate_as_string(CONTEXT1)
    assert isinstance(result, datatypes.string)
    assert result == datatypes.string('foo:CHILD3')


def test_string_function():
    result = function_call('string', [nodeset_literal([CHILD1])]).evaluate_as_string(CONTEXT1)
    assert isinstance(result, datatypes.string)
    expected = datatypes.string('\n    \n    \n    Text1\n  ')
    assert result == expected, (result, expected)

def test_concat_function():
    result = function_call('concat', [nodeset_literal([CHILD1]),
                                      string_literal('"3.14"'),
                                      string_literal('"Hi"')]).evaluate_as_string(CONTEXT1)
    assert isinstance(result, datatypes.string)
    expected = datatypes.string('\n    \n    \n    Text1\n  3.14Hi')
    assert result == expected, (result, expected)

def test_starts_with_function():
    for args, expected in (
        ([nodeset_literal([CHILD1]), string_literal('"3.14"')], datatypes.FALSE),
        ([nodeset_literal([CHILD1]), nodeset_literal([CHILD1])], datatypes.TRUE),
        ([nodeset_literal([CHILD1]), string_literal('""')], datatypes.TRUE),
        ):
        result = function_call('starts-with', args).evaluate_as_boolean(CONTEXT1)
        assert isinstance(result, datatypes.boolean)
        assert result == expected, (result, expected)

def test_contains_function():
    for args, expected in (
        ([nodeset_literal([CHILD1]), string_literal('"3.14"')], datatypes.FALSE),
        ([nodeset_literal([CHILD1]), nodeset_literal([CHILD1])], datatypes.TRUE),
        ([nodeset_literal([CHILD1]), string_literal('""')], datatypes.TRUE),
        ):
        result = function_call('contains', args).evaluate_as_boolean(CONTEXT1)
        assert isinstance(result, datatypes.boolean)
        assert result == expected, (result, expected)

def test_substring_before_function():
    for args, expected in (
        ([string_literal('"3.14Hi"'), string_literal('"Hi"')], datatypes.string('3.14')),
        ([string_literal('"3.14Hi"'), string_literal('""')], datatypes.string())
        ):
        result = function_call('substring-before', args).evaluate_as_boolean(CONTEXT1)
        assert isinstance(result, datatypes.boolean)
        assert result == expected, (result, expected)


def test_substring_after_function():
    for args, expected in (
        ([string_literal('"3.14Hi"'), string_literal('"3.14"')], datatypes.string('Hi')),
        ([string_literal('"3.14Hi"'), string_literal('""')], datatypes.string())
        ):
        result = function_call('substring-after', args).evaluate_as_string(CONTEXT1)
        assert isinstance(result, datatypes.string)
        assert result == expected, (result, expected)


def test_substring_function():
    for args, expected in (
        ([string_literal('"3.14Hi"'), string_literal('"3.14"')], datatypes.string('14Hi')),
        ([string_literal('"3.14Hi"'), string_literal('"3.14"'), number_literal('1')],  datatypes.string('1')),
        ([string_literal('"12345"'), number_literal('2'), number_literal('3')],  datatypes.string('234')),
        ([string_literal('"12345"'), number_literal('2')],  datatypes.string('2345')),
        ([string_literal('"12345"'), number_literal('1.5'), number_literal('2.6')],  datatypes.string('234')),
        ([string_literal('"12345"'), number_literal('0'), number_literal('3')],  datatypes.string('12')),
        ([string_literal('"12345"'), NOT_A_NUMBER, number_literal('3')],  datatypes.string('')),
        ([string_literal('"12345"'), number_literal('1'), NOT_A_NUMBER],  datatypes.string('')),
        ([string_literal('"12345"'), number_literal('-42'), POSITIVE_INFINITY],  datatypes.string('12345')),
        ([string_literal('"12345"'), NEGATIVE_INFINITY, POSITIVE_INFINITY],  datatypes.string('')),
        ):
        result = function_call('substring', args).evaluate_as_string(CONTEXT1)
        assert isinstance(result, datatypes.string)
        assert result == expected, (result, expected)

def test_string_length_function():
    result = function_call('string-length', [string_literal('"3.14Hi"')]).evaluate_as_number(CONTEXT1)
    assert isinstance(result, datatypes.number)
    expected = datatypes.number(6)
    assert result == expected, (result, expected)

def test_normalize_space_function():
    result = function_call('normalize-space',
                           [string_literal('"Ht    	 There	   Mike"')]).evaluate_as_string(CONTEXT1)
    assert isinstance(result, datatypes.string)
    expected = datatypes.string(u'Ht There Mike')
    assert result == expected, (result, expected)

def test_translate_function():
    for args, expected in ( 
        # a,b,c,d,e,f become A,B,C,D,E,F
        ([string_literal('"Ht    \t There\t   Mike"'), string_literal('abcdef'), string_literal('ABCDEF')],
         datatypes.string('Ht    \t ThErE\t   MikE')),
        # e becomes a
        ([string_literal('"hello world"'), string_literal('e'), string_literal('a')],
         datatypes.string('hallo world')),

        # e becomes a; extra chars in To string are ignored
        ([string_literal('"hello world"'), string_literal('e'), string_literal('abc')],
         datatypes.string('hallo world')),

        # e becomes a; l is deleted
        ([string_literal('"hello world"'), string_literal('el'), string_literal('a')],
         datatypes.string('hao word')),

        # a,b,c,d,e,f become A,B,C,D,E,F;
        # the first occurance of a char in the 2nd arg is the replacement
        ([string_literal('"hello world"'), string_literal('abcdde'), string_literal('ABCDEF')],
         datatypes.string('hFllo worlD')),

        # if there is a char in the 2nd arg with no char at the same pos
        # in the 3rd arg, that char is removed from the 1st arg
        ([string_literal('"hello world"'), string_literal('abcdefgh'), string_literal('')],
         datatypes.string('llo worl')),
        ):
        result = function_call('translate', args).evaluate_as_string(CONTEXT1)
        assert isinstance(result, datatypes.string)
        assert result == expected, (result, expected)

def test_boolean_function():
    result = function_call('boolean', [string_literal('"3.14Hi"')]).evaluate_as_boolean(CONTEXT1)
    assert isinstance(result, datatypes.boolean)
    assert result == datatypes.TRUE, result

def test_not_function():
    result = function_call('not', [string_literal('"3.14Hi"')]).evaluate_as_boolean(CONTEXT1)
    assert isinstance(result, datatypes.boolean)
    assert result == datatypes.FALSE, result

def test_true_function():
    result = function_call('true', []).evaluate_as_boolean(CONTEXT1)
    assert isinstance(result, datatypes.boolean)
    assert result == datatypes.TRUE, result

def test_false_function():
    result = function_call('false', []).evaluate_as_boolean(CONTEXT1)
    assert isinstance(result, datatypes.boolean)
    assert result == datatypes.FALSE, result

def test_lang_function():
    for arg, expected, context in (
        (string_literal('en'), datatypes.FALSE, CONTEXTLANG1),
        (string_literal('en'), datatypes.TRUE, CONTEXTLANG2),
        (string_literal(''), datatypes.TRUE, CONTEXTLANG1),
        (string_literal(''), datatypes.FALSE, CONTEXTLANG2),
        (string_literal('foo'), datatypes.FALSE, CONTEXTLANG1),
        (string_literal('foo'), datatypes.FALSE, CONTEXTLANG2),
        ):
        result = function_call('lang', [arg]).evaluate_as_boolean(context)
        assert isinstance(result, datatypes.boolean)
        assert result == expected, (result, expected)


def test_number_function():
    result = function_call('number', []).evaluate_as_number(CONTEXT1)
    assert isinstance(result, datatypes.number)
    assert result.isnan()

def test_sum_function():
    result = function_call('sum', [nodeset_literal([EGG1, EGG2, EGG3, EGG4])]).evaluate_as_number(CONTEXT1)
    assert isinstance(result, datatypes.number)
    assert result == datatypes.number(2)

def test_floor_function():
    for arg, expected in (
        (string_literal('"3.14"'), datatypes.number(3)),
        (NOT_A_NUMBER, datatypes.NOT_A_NUMBER),
        (POSITIVE_INFINITY, datatypes.POSITIVE_INFINITY),
        (NEGATIVE_INFINITY, datatypes.NEGATIVE_INFINITY),
        (number_literal('0.5'), datatypes.number(0)),
        (number_literal('-0.5'), datatypes.number(-1)),
        ):
        result = function_call('floor', [arg]).evaluate_as_number(CONTEXT1)
        assert isinstance(result, datatypes.number)
        assert ((result.isnan() and expected.isnan()) or result == expected), (result, expected)
        
def test_ceiling_function():
    for arg, expected in (
        (string_literal('"3.14"'), datatypes.number(4)),
        (NOT_A_NUMBER, datatypes.NOT_A_NUMBER),
        (POSITIVE_INFINITY, datatypes.POSITIVE_INFINITY),
        (number_literal('0.5'), datatypes.number(1)),
        (number_literal('-0.5'), datatypes.number(-0.0)),
        ):
        result = function_call('ceiling', [arg]).evaluate_as_number(CONTEXT1)
        assert isinstance(result, datatypes.number)
        assert ((result.isnan() and expected.isnan()) or result == expected), (result, expected)

def test_round_function():
    for arg, expected in (
        (string_literal('"3.14"'), datatypes.number(3)),
        (number_literal('-4.5'), datatypes.number(-4)),
        (NOT_A_NUMBER, datatypes.NOT_A_NUMBER),
        (POSITIVE_INFINITY, datatypes.POSITIVE_INFINITY),
        (NEGATIVE_INFINITY, datatypes.NEGATIVE_INFINITY),
        (string_literal('"12345"'), datatypes.number(12345)),
        ):
        print "Call", arg
        result = function_call('round', [arg]).evaluate_as_number(CONTEXT1)
        assert isinstance(result, datatypes.number)
        assert ((result.isnan() and expected.isnan()) or result == expected), (result, expected)


if __name__ == '__main__':
    raise SystemExit('Use nosetests')
