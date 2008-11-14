#!/usr/bin/env python
from amara import tree
from amara.xpath import context, datatypes
from amara.xpath.expressions.basics import string_literal, number_literal

from test_expressions import (
    test_expression,
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


class test_function_call(test_expression):
    module_name = 'amara.xpath.expressions.functioncalls'
    class_name = 'function_call'


class test_last_function(test_function_call):
    evaluate_method = 'evaluate_as_number'
    return_type = datatypes.number
    test_cases = [
        (['last', ()], datatypes.number(3), CONTEXT1),
        (['last', ()], datatypes.number(3), CONTEXT2),
        ]


class test_position_function(test_function_call):
    evaluate_method = 'evaluate_as_number'
    return_type = datatypes.number
    test_cases = [
        (['position', ()], datatypes.number(1), CONTEXT1),
        (['position', ()], datatypes.number(2), CONTEXT2),
        ]


class test_count_function(test_function_call):
    evaluate_method = 'evaluate_as_number'
    return_type = datatypes.number
    test_cases = [
        (['count', (nodeset_literal([ROOT, CHILD1]),)], datatypes.number(2), CONTEXT1)
        ]


class test_id_function(test_function_call):
    evaluate_method = 'evaluate_as_nodeset'
    return_type = datatypes.nodeset
    test_cases = [
        (['id', [number_literal('1')]], datatypes.nodeset([CHILD2]), CONTEXT1),
        (['id', [string_literal('"1 1"')]], datatypes.nodeset([CHILD2]), CONTEXT1),
        (['id', [string_literal('"0"')]], datatypes.nodeset(), CONTEXT1),
        (['id', [string_literal('"0 1"')]], datatypes.nodeset([CHILD2]), CONTEXT1),
        (['id', [string_literal('"0 1 1"')]], datatypes.nodeset([CHILD2]), CONTEXT1),
        (['id', [string_literal('"0 0 1 1"')]], datatypes.nodeset([CHILD2]), CONTEXT1),
        (['id', [nodeset_literal([EGG1])]], datatypes.nodeset(), CONTEXT1),
        (['id', [nodeset_literal([EGG1, EGG2])]], datatypes.nodeset([CHILD2]), CONTEXT1),
        (['id', [nodeset_literal([EGG1, EGG2, EGG3])]], datatypes.nodeset([CHILD2]), CONTEXT1),
        (['id', [nodeset_literal([EGG1, EGG2, EGG3, EGG4])]], datatypes.nodeset([CHILD2]), CONTEXT1),
        ]


class test_local_name_function(test_function_call):
    evaluate_method = 'evaluate_as_string'
    return_type = datatypes.string
    test_cases = [
        (['local-name', [nodeset_literal([])]], datatypes.string(), CONTEXT1),
        (['local-name', [nodeset_literal([CHILD3])]], datatypes.string('CHILD3'), CONTEXT1),
        ]


class test_namespace_uri_function(test_function_call):
    evaluate_method = 'evaluate_as_string'
    return_type = datatypes.string
    test_cases = [
        (['namespace-uri', [nodeset_literal([])]],
         datatypes.string(), 
         CONTEXT1),
        (['namespace-uri', [nodeset_literal([CHILD3])]], 
         datatypes.string('http://foo.com'), 
         CONTEXT1),
        ]


class test_name_function(test_function_call):
    evaluate_method = 'evaluate_as_string'
    return_type = datatypes.string
    test_cases = [
        (['name', [nodeset_literal([CHILD3])]],
         datatypes.string('foo:CHILD3'), 
         CONTEXT1),
        ]


class test_string_function(test_function_call):
    evaluate_method = 'evaluate_as_string'
    return_type = datatypes.string
    test_cases = [
        (['string', [nodeset_literal([CHILD1])]],
         datatypes.string('\n    Text1\n  '), 
         CONTEXT1),
        ]


class test_concat_function(test_function_call):
    evaluate_method = 'evaluate_as_string'
    return_type = datatypes.string
    test_cases = [
        (['concat', [nodeset_literal([CHILD1]), string_literal('"3.14"'), string_literal('"Hi"')]],
         datatypes.string('\n    Text1\n  3.14Hi'), 
         CONTEXT1),
        ]


class test_starts_with_function(test_function_call):
    evaluate_method = 'evaluate_as_boolean'
    return_type = datatypes.boolean
    test_cases = [
        (['starts-with', [nodeset_literal([CHILD1]), string_literal('"3.14"')]], 
         datatypes.FALSE, CONTEXT1),
        (['starts-with', [nodeset_literal([CHILD1]), nodeset_literal([CHILD1])]], 
         datatypes.TRUE, CONTEXT1),
        (['starts-with', [nodeset_literal([CHILD1]), string_literal('""')]], 
         datatypes.TRUE, CONTEXT1),
        ]


class test_contains_function(test_function_call):
    evaluate_method = 'evaluate_as_boolean'
    return_type = datatypes.boolean
    test_cases = [
        (['contains', [nodeset_literal([CHILD1]), string_literal('"3.14"')]], 
         datatypes.FALSE, CONTEXT1),
        (['contains', [nodeset_literal([CHILD1]), nodeset_literal([CHILD1])]], 
         datatypes.TRUE, CONTEXT1),
        (['contains', [nodeset_literal([CHILD1]), string_literal('""')]], 
         datatypes.TRUE, CONTEXT1),
        ]


class test_substring_before_function(test_function_call):
    evaluate_method = 'evaluate_as_string'
    return_type = datatypes.string
    test_cases = [
        (['substring-before', [string_literal('"3.14Hi"'), string_literal('"Hi"')]],
         datatypes.string('3.14'), CONTEXT1),
        (['substring-before', [string_literal('"3.14Hi"'), string_literal('""')]],
         datatypes.string(), CONTEXT1),
        ]


class test_substring_after_function(test_function_call):
    evaluate_method = 'evaluate_as_string'
    return_type = datatypes.string
    test_cases = [
        (['substring-after', [string_literal('"3.14Hi"'), string_literal('"3.14"')]],
         datatypes.string('Hi'), CONTEXT1),
        (['substring-after', [string_literal('"3.14Hi"'), string_literal('""')]],
         datatypes.string(), CONTEXT1),
        ]


class test_substring_after_function(test_function_call):
    evaluate_method = 'evaluate_as_string'
    return_type = datatypes.string
    test_cases = [
        (['substring', [string_literal('"3.14Hi"'), string_literal('"3.14"')]],
         datatypes.string('14Hi'), CONTEXT1),
        (['substring', [string_literal('"3.14Hi"'), string_literal('"3.14"'), number_literal('1')]], 
         datatypes.string('1'), CONTEXT1),
        (['substring', [string_literal('"12345"'), number_literal('2'), number_literal('3')]], 
         datatypes.string('234'), CONTEXT1),
        (['substring', [string_literal('"12345"'), number_literal('2')]], 
         datatypes.string('2345'), CONTEXT1),
        (['substring', [string_literal('"12345"'), number_literal('1.5'), number_literal('2.6')]], 
         datatypes.string('234'), CONTEXT1),
        (['substring', [string_literal('"12345"'), number_literal('0'), number_literal('3')]], 
         datatypes.string('12'), CONTEXT1),
        (['substring', [string_literal('"12345"'), NOT_A_NUMBER, number_literal('3')]], 
         datatypes.string(''), CONTEXT1),
        (['substring', [string_literal('"12345"'), number_literal('1'), NOT_A_NUMBER]], 
         datatypes.string(''), CONTEXT1),
        (['substring', [string_literal('"12345"'), number_literal('-42'), POSITIVE_INFINITY]], 
         datatypes.string('12345'), CONTEXT1),
        (['substring', [string_literal('"12345"'), NEGATIVE_INFINITY, POSITIVE_INFINITY]], 
         datatypes.string(''), CONTEXT1),
        ]


class test_string_length_function(test_function_call):
    evaluate_method = 'evaluate_as_number'
    return_type = datatypes.number
    test_cases = [
        (['string-length', [string_literal('"3.14Hi"')]],
        datatypes.number(6), CONTEXT1),
        ]


class test_normalize_space_function(test_function_call):
    evaluate_method = 'evaluate_as_string'
    return_type = datatypes.string
    test_cases = [
        (['normalize-space', [string_literal('"Ht    	 There	   Mike"')]],
         datatypes.string(u'Ht There Mike'), CONTEXT1),
        ]


class test_translate_function(test_function_call):
    evaluate_method = 'evaluate_as_string'
    return_type = datatypes.string
    test_cases = [
        # a,b,c,d,e,f become A,B,C,D,E,F
        (['translate', [string_literal('"Ht    	 There	   Mike"'), string_literal('abcdef'), string_literal('ABCDEF')]],
         datatypes.string('Ht    \t ThErE\t   MikE'), CONTEXT1),
        # e becomes a
        (['translate', [string_literal('"hello world"'), string_literal('e'), string_literal('a')]],
         datatypes.string('hallo world'), CONTEXT1),
        # e becomes a; extra chars in To string are ignored
        (['translate', [string_literal('"hello world"'), string_literal('e'), string_literal('abc')]],
         datatypes.string('hallo world'), CONTEXT1),
        # e becomes a; l is deleted
        (['translate', [string_literal('"hello world"'), string_literal('el'), string_literal('a')]],
         datatypes.string('hao word'), CONTEXT1),
        # a,b,c,d,e,f become A,B,C,D,E,F;
        # the first occurance of a char in the 2nd arg is the replacement
        (['translate', [string_literal('"hello world"'), string_literal('abcdde'), string_literal('ABCDEF')]],
         datatypes.string('hFllo worlD'), CONTEXT1),
        # if there is a char in the 2nd arg with no char at the same pos
        # in the 3rd arg, that char is removed from the 1st arg
        (['translate', [string_literal('"hello world"'), string_literal('abcdefgh'), string_literal('')]],
         datatypes.string('llo worl'), CONTEXT1),
        ]


class test_boolean_function(test_function_call):
    evaluate_method = 'evaluate_as_boolean'
    return_type = datatypes.boolean
    test_cases = [
        (['boolean', [string_literal('"3.14Hi"')]],
         datatypes.TRUE, CONTEXT1),
        ]


class test_not_function(test_function_call):
    evaluate_method = 'evaluate_as_boolean'
    return_type = datatypes.boolean
    test_cases = [
        (['not', [string_literal('"3.14Hi"')]],
         datatypes.FALSE, CONTEXT1),
        ]


class test_true_function(test_function_call):
    evaluate_method = 'evaluate_as_boolean'
    return_type = datatypes.boolean
    test_cases = [
        (['true', []], datatypes.TRUE, CONTEXT1),
        ]


class test_false_function(test_function_call):
    evaluate_method = 'evaluate_as_boolean'
    return_type = datatypes.boolean
    test_cases = [
        (['false', []], datatypes.FALSE, CONTEXT1),
        ]


class test_boolean_function(test_function_call):
    evaluate_method = 'evaluate_as_boolean'
    return_type = datatypes.boolean
    test_cases = [
        (['lang', [string_literal('en')]], datatypes.FALSE, CONTEXTLANG1),
        (['lang', [string_literal('en')]], datatypes.TRUE, CONTEXTLANG2),
        (['lang', [string_literal('')]], datatypes.TRUE, CONTEXTLANG1),
        (['lang', [string_literal('')]], datatypes.FALSE, CONTEXTLANG2),
        (['lang', [string_literal('foo')]], datatypes.FALSE, CONTEXTLANG1),
        (['lang', [string_literal('foo')]], datatypes.FALSE, CONTEXTLANG2),
        ]


class test_number_function(test_function_call):
    evaluate_method = 'evaluate_as_number'
    return_type = datatypes.number
    test_cases = [
        (['number', []], datatypes.NOT_A_NUMBER, CONTEXT1),
        ]


class test_sum_function(test_function_call):
    evaluate_method = 'evaluate_as_number'
    return_type = datatypes.number
    test_cases = [
        (['sum', [nodeset_literal([EGG1, EGG2, EGG3, EGG4])]],
         datatypes.number(2), CONTEXT1),
        ]


class test_floor_function(test_function_call):
    evaluate_method = 'evaluate_as_number'
    return_type = datatypes.number
    test_cases = [
        (['floor', [string_literal('"3.14"')]], 
         datatypes.number(3), CONTEXT1),
        (['floor', [NOT_A_NUMBER]],
         datatypes.NOT_A_NUMBER, CONTEXT1),
        (['floor', [POSITIVE_INFINITY]],
         datatypes.POSITIVE_INFINITY, CONTEXT1),
        (['floor', [NEGATIVE_INFINITY]],
         datatypes.NEGATIVE_INFINITY, CONTEXT1),
        (['floor', [number_literal('0.5')]],
         datatypes.number(0), CONTEXT1),
        (['floor', [number_literal('-0.5')]],
         datatypes.number(-1), CONTEXT1),
        ]


class test_ceiling_function(test_function_call):
    evaluate_method = 'evaluate_as_number'
    return_type = datatypes.number
    test_cases = [
        (['ceiling', [string_literal('"3.14"')]],
         datatypes.number(4), CONTEXT1),
        (['ceiling', [NOT_A_NUMBER]],
         datatypes.NOT_A_NUMBER, CONTEXT1),
        (['ceiling', [POSITIVE_INFINITY]],
         datatypes.POSITIVE_INFINITY, CONTEXT1),
        (['ceiling', [number_literal('0.5')]],
         datatypes.number(1), CONTEXT1),
        (['ceiling', [number_literal('-0.5')]],
         datatypes.number(-0.0), CONTEXT1),
        ]


class test_round_function(test_function_call):
    evaluate_method = 'evaluate_as_number'
    return_type = datatypes.number
    test_cases = [
        (['round', [string_literal('"3.14"')]],
         datatypes.number(3), CONTEXT1),
        (['round', [number_literal('-4.5')]],
         datatypes.number(-4), CONTEXT1),
        (['round', [NOT_A_NUMBER]],
         datatypes.NOT_A_NUMBER, CONTEXT1),
        (['round', [POSITIVE_INFINITY]],
         datatypes.POSITIVE_INFINITY, CONTEXT1),
        (['round', [NEGATIVE_INFINITY]],
         datatypes.NEGATIVE_INFINITY, CONTEXT1),
        (['round', [string_literal('"12345"')]],
         datatypes.number(12345), CONTEXT1),
        ]


if __name__ == '__main__':
    from amara.lib import testsupport
    testsupport.test_main()
