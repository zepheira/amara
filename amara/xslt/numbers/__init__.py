########################################################################
# amara/xslt/numbers/__init__.py
"""
"""

import re
import itertools

__all__ = ['formatter']

DEFAULT_LANG = 'en'
DEFAULT_FORMAT = '1'
DEFAULT_SEPARATOR = '.'

def _repeat_last(seq):
    for item in seq:
        yield item
    while 1:
        yield item
    return

# Bind the class name in the global scope so that the metaclass can be
# safely called for the construction of the initial class.
formatter = None
class formatter(object):

    language = None
    _classmap = {}

    class __metaclass__(type):
        def __init__(cls, name, bases, namespace):
            if formatter is not None:
                cls._classmap[cls.language] = cls
                # Allow sub-classes to be instaniated directly
                cls.__new__ = object.__new__

    def __new__(cls, language, format):
        """
        Creates a `numberer` appropriate for the given language
        or a default, English-based formatter.

        Raises an exception if the language is unsupported. Currently, if the
        language value is given, it must indicate English.
        """
        # lang specifies the language whose alphabet is to be used
        #  for numbering when a format token is alphabetic.
        #
        # "if no lang value is specified, the language should be
        # determined from the system environment." -- unsupported;
        # we just default to English.
        if not language:
            language = DEFAULT_LANG
        if language not in cls._classmap:
            languages = [language]
            if '-' in language:
                primary, subpart = language.split('-', 1)
                languages.append(primary)
            for language in languages:
                name = language.replace('-', '_')
                try:
                    module = __name__ + '.' + name
                    __import__(module, globals(), globals(), ['*'])
                except ImportError:
                    pass
                else:
                    assert language in cls._classmap
                    break
            else:
                language = DEFAULT_LANG
        try:
            cls = cls._classmap[language]
        except KeyError:
            cls = cls._classmap[DEFAULT_LANG]
        return object.__new__(cls)

    _tokenize_re = re.compile('(?u)(\W*)(\w+)(\W*)')

    def __init__(self, language, format):
        if not format:
            format = DEFAULT_FORMAT
        parts = self._tokenize_re.findall(format)
        if not parts:
            # No alphanumeric token in the format string
            self._prefix = self._suffix = format
            self._toks = (DEFAULT_FORMAT,)
            self._seps = (DEFAULT_SEPARATOR,)
        elif len(parts) == 1:
            self._prefix, token, self._suffix = parts[0]
            self._toks = (token,)
            self._seps = (DEFAULT_SEPARATOR,)
        else:
            self._prefix, token, sep = parts[0]
            toks = self._toks = [token]
            seps = self._seps = []
            for prefix, token, suffix in parts[1:]:
                seps.append(sep)
                toks.append(token)
                sep = suffix
            self._suffix = suffix
        return

    def _format(self, number, token, letter_value, grouping, separator):
        raise NotImplementedError

    def format(self, number, letter_value, grouping, separator):
        token = self._toks[0]
        result = self._format(number, token, letter_value, grouping, separator)
        return self._prefix + result + self._suffix

    def formatmany(self, numbers, letter_value, grouping, separator):
        result = [self._prefix]
        for number, tok, sep in itertools.izip(numbers,
                                               _repeat_last(self._toks),
                                               _repeat_last(self._seps)):
            result.append(self._format(number, tok, letter_value, grouping,
                                       separator))
            result.append(sep)
        result[-1] = self._suffix
        return u''.join(result)

# Load the default formatter
from amara.xslt.numbers import en