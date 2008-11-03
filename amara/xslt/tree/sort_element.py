########################################################################  
# amara/xslt/tree/sort_element.py
"""
Implementation of `xsl:sort` element
"""

from amara.xpath import datatypes
from amara.xslt.tree import xslt_element, content_model, attribute_types

class sort_element(xslt_element):
    content_model = content_model.empty
    attribute_types = {
        'select': attribute_types.string_expression(default='.'),
        'lang': attribute_types.nmtoken_avt(),
        # We don't support any additional data-types, hence no
        # attribute_types.QNameButNotNCName()
        'data-type': attribute_types.choice_avt(('text', 'number'),
                                                default='text'),
        'order': attribute_types.choice_avt(('ascending', 'descending'),
                                            default='ascending'),
        'case-order': attribute_types.choice_avt(('upper-first',
                                                  'lower-first')),
        }

    # Using `object` as a sentinel as `None` is a valid compare function
    _missing = object()
    _compare = _missing
    _reverse = _missing

    def setup(self):
        # optimize for constant AVT attribute values (i.e., no {})
        if self._data_type.constant and self._case_order.constant:
            self._compare = self._get_compare(self._data_type.evaluate(None),
                                              self._case_order.evaluate(None))
        if self._order.constant:
            self._reverse = self._order.evaluate(None) == 'descending'
        return

    def _get_compare(self, data_type, case_order):
        if data_type == 'number':
            comparer = _number_compare
        else:
            if case_order == 'lower-first':
                comparer = _lower_first_compare
            elif case_order == 'upper-first':
                comparer = _upper_first_compare
            else:
                # use default for this locale
                comparer = None
        return comparer

    def get_parameters(self, context, _missing=_missing):
        compare, reverse = self._compare, self._reverse
        if compare is _missing:
            data_type = self._data_type.evaluate(context)
            case_order = self._case_order and self._case_order.evaluate(context)
            compare = self._get_compare(data_type, case_order)
        if reverse is _missing:
            reverse = self._order.evaluate(context) == 'descending'
        return (compare, reverse)

    def get_key(self, context):
        data_type = self._data_type.evaluate(context)
        if data_type == 'text':
            # Use "real" strings as XPath string objects implement
            # XPath semantics for relational (<,>) operators.
            return unicode(self._select.evaluate_as_string(context))
        elif data_type == 'number':
            return self._select.evaluate_as_number(context)
        return self._select.evaluate(context)


### Comparision Functions ###

def _number_compare(a, b):
    # NaN seems to always equal everything else, so we'll do it ourselves
    # the IEEE definition of NaN makes it the smallest possible number
    if a.isnan():
        return 0 if b.isnan() else -1
    elif b.isnan():
        return 1
    return cmp(a, b)

def _lower_first_compare(a, b):
    # case only matters if the strings are equal ignoring case
    if a.lower() == b.lower():
        for i, ch in enumerate(a):
            if ch != b[i]:
                return -1 if ch.islower() else 1
        # they are truly equal
        return 0
    else:
        return cmp(a, b)

def _upper_first_compare(a, b):
    # case only matters if the strings are equal ignoring case
    if a.lower() == b.lower():
        for i, ch in enumerate(a):
            if ch != b[i]:
                return ch.isupper() and -1 or 1
        # they are truly equal
        return 0
    else:
        return cmp(a, b)
