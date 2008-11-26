########################################################################
# amara/xslt/exslt/regular_expressions.py
"""
EXSLT 2.0 - Regular Expressions (http://www.exslt.org/regexp/index.html)
"""
import re

from amara.xpath import datatypes

EXSL_REGEXP_NS = "http://exslt.org/regular-expressions"

def match_function(context, source, pattern, flags=None):
    """
    The regexp:match function lets you get hold of the substrings of the
    string passed as the first argument that match the captured parts of
    the regular expression passed as the second argument.

    The second argument is a regular expression that follows the Javascript
    regular expression syntax.

    The third argument is a string consisting of character flags to be used
    by the match. If a character is present then that flag is true. The
    flags are:
      g: global match - the submatches from all the matches in the string
                        are returned. If this character is not present, then
                        only the submatches from the first match in the
                        string are returned.
      i: case insensitive - the regular expression is treated as case
                            insensitive. If this character is not present,
                            then the regular expression is case sensitive.

    The regexp:match function returns a node set of 'match' elements, each of
    whose string value is equal to a portion of the first argument string
    that was captured by the regular expression. If the match is not global,
    the first match element has a value equal to the portion of the string
    matched by the entire regular expression.
    """
    source = source.evaluate_as_string(context)
    pattern = pattern.evaluate_as_string(context)
    flags = flags.evaluate_as_string(context) if flags else ''

    regexp = re.compile(pattern, re.IGNORECASE if 'i' in flags else 0)

    match = regexp.search(source)
    if match is None:
        return datatypes.nodeset()
    context.push_tree_writer(context.instruction.baseUri)
    if 'g' in flags:
        # find all matches in the source
        while match:
            context.start_element(u'match')
            # return everything that matched the pattern
            context.text(match.group())
            context.end_element(u'match')
            match = regexp.search(source, match.end())
    else:
        # the first 'match' element contains entire matched text
        all = [match.group()]
        groups = match.groups()
        groups and all.extend(list(groups))
        for match in all:
            context.start_element(u'match')
            match and context.text(match)
            context.end_element(u'match')
    writer = context.pop_writer()
    rtf = writer.get_result()
    return datatypes.nodeset(rtf.xml_children)


def replace_function(context, source, pattern, flags, repl):
    """
    The regexp:replace function replaces the parts of a string that match
    a regular expression with another string.

    The first argument is the string to be matched and replaced. The second
    argument is a regular expression that follows the Javascript regular
    expression syntax. The fourth argument is the string to replace the
    matched parts of the string.

    The third argument is a string consisting of character flags to be used
    by the match. If a character is present then that flag is true. The flags
    are:
      g: global replace - all occurrences of the regular expression in the
                          string are replaced. If this character is not
                          present, then only the first occurrence of the
                          regular expression is replaced.
      i: case insensitive - the regular expression is treated as case
                            insensitive. If this character is not present,
                            then the regular expression is case sensitive.
    """
    source = source.evaluate_as_string(context)
    pattern = pattern.evaluate_as_string(context)
    flags = flags.evaluate_as_string(context)
    repl = repl.evaluate_as_string(context)

    regexp = re.compile(pattern, re.IGNORECASE if 'i' in flags else 0)
    # a count of zero means replace all in RE.sub()
    result = regexp.sub(repl, source, 'g' not in flags)
    return datatypes.string(result)


def test_function(context, source, pattern, flags=''):
    """
    The regexp:test function returns true if the string given as the first
    argument matches the regular expression given as the second argument.

    The second argument is a regular expression that follows the Javascript
    regular expression syntax.

    The third argument is a string consisting of flags to be used by the test.
    If a character is present then that flag is true. The flags are:
      g: global test - has no effect on this function, but is retained for
                       consistency with regexp:match and regexp:replace.
      i: case insensitive - the regular expression is treated as case
                            insensitive. If this character is not present,
                            then the regular expression is case sensitive.
    """
    source = source.evaluate_as_string(context)
    pattern = pattern.evaluate_as_string(context)
    flags = flags.evaluate_as_string(context) if flags else ''

    regexp = re.compile(pattern, re.IGNORECASE if 'i' in flags else 0)
    return datatypes.TRUE if regexp.search(source) else datatypes.FALSE


## XSLT Extension Module Interface ####################################

extension_namespaces = {
    EXSL_REGEXP_NS : 'regexp',
    }

extension_functions = {
    (EXSL_REGEXP_NS, 'match') : match_function,
    (EXSL_REGEXP_NS, 'replace') : replace_function,
    (EXSL_REGEXP_NS, 'test') : test_function,
    }

extension_elements = {
    }

