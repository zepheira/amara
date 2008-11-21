########################################################################
# amara/xslt/numbers/en.py

from amara.xpath import datatypes
from amara.xslt.numbers import formatter

ASCII_DIGITS = '0123456789'
ASCII_LOWER = 'abcdefghijklmnopqrstuvwxyz'
ASCII_UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

class english_formatter(formatter):

    language = 'en'

    _roman_digits = _roman_upper, _roman_lower = [], []
    for multiplier, combining in ((1, ''), (1000, u'\u0305')):
        for base, one, five, ten in ((1, u'I', u'V', u'X'),
                                     (10, u'X', u'L', u'C'),
                                     (100, u'C', u'D', u'M')):
            base *= multiplier
            one += combining
            five += combining
            ten += combining
            digits = (u'', one, one*2, one*3, one+five,
                      five, five+one, five+one*2, five+one*3, one+ten)
            _roman_upper.append((base, digits))
            _roman_lower.append((base, map(unicode.lower, digits)))
    _roman_max = base * len(_roman_upper[-1][1])

    def _alpha_sequence(self, number, alphabet):
        size = len(alphabet)
        digits = ''
        while number > size:
            number, ordinal = divmod(number - 1, size)
            digits += alphabet[ordinal]
        digits += alphabet[number - 1]
        return digits

    def _format(self, number, token, letter_value, separator, grouping):
        if token in ('I', 'i') and letter_value != 'alphabetic':
            # roman numerals
            if 0 < number < self._roman_max:
                result = []
                for bound, digits in self._roman_digits[token == 'i']:
                    if number > bound:
                        index, number = divmod(number, bound)
                        result.append(digits[index])
                    last_digits = digits
                result = u''.join(result)
            else:
                result = '%d' % number
        elif token in ('A', 'a'):
            # alphabetic numbering
            alphabet = ASCII_LOWER if token == 'a' else ASCII_UPPER
            result = self._alpha_sequence(number, alphabet)
        else:
            # arabic numerals
            if token[-1:] != '1':
                # unsupported format token, using '1'
                token == '1'
            result = '%0*d' % (len(token), number)
            if separator and grouping:
                start = -len(numeric)
                step = -grouping
                if start < step:
                    groups = []
                    for next in reversed(xrange(step, start, step)):
                        groups.append(result[start:next])
                        start = next
                    groups.append(result[start:])
                    result = separator.join(groups)

        return datatypes.string(result)
