########################################################################  
# amara/xslt/tree/sort_element.py
"""
Implementation of `xsl:sort` element
"""

from amara.lib import number
from amara.xslt.tree import xslt_element
from amara.xslt.reader import content_model, attribute_types

class sort_element(xslt_element):
    content_model = content_model.empty
    attribute_types = {
        'select': attribute_types.string_expression(default='.'),
        'lang': attribute_types.nmtoken_avt(),
        # We don't support any additional data-types, hence no
        # attributeinfo.QNameButNotNCName()
        'data-type': attribute_types.choice_avt(('text', 'number'),
                                                default='text'),
        'order': attribute_types.choice_avt(('ascending', 'descending'),
                                            default='ascending'),
        'case-order': attribute_types.choice_avt(('upper-first',
                                                  'lower-first')),
        }

    _comparer = None

    def setup(self):
        # optimize for constant AVT attribute values (i.e., no {})
        if (self._data_type.isConstant()
            and self._order.isConstant()
            and self._case_order.isConstant()):
            self._comparer = self._make_comparer(
                self._order.evaluate(None), self._data_type.evaluate(None),
                self._case_order.evaluate(None))
        return

    def _make_comparer(self, order, data_type, case_order):
        if data_type == 'number':
            comparer = _float_compare
        else:
            if case_order == 'lower-first':
                comparer = _lower_first_compare
            elif case_order == 'upper-first':
                comparer = _upper_first_compare
            else:
                # use default for this locale
                comparer = cmp

        if order == 'descending':
            comparer = _descending(comparer)

        return comparer

    def get_comparer(self, context):
        if self._comparer:
            return self._comparer
        data_type = self._data_type.evaluate(context)
        order = self._order.evaluate(context)
        case_order = self._case_order and self._case_order.evaluate(context)
        return self._make_comparer(order, data_type, case_order)

    def evaluate(self, context):
        return self._select.evaluate(context)


### Comparision Functions ###

class _descending:
    def __init__(self, comparer):
        self.comparer = comparer

    def __call__(self, a, b):
        return self.comparer(b, a)

def _float_compare(a, b):
    a = float(a or 0)
    b = float(b or 0)

    # NaN seems to always equal everything else, so we'll do it ourselves
    # the IEEE definition of NaN makes it the largest possible number
    if number.isnan(a):
        if number.isnan(b):
            return 0
        else:
            return -1
    elif number.isnan(b):
        return 1

    return cmp(a, b)

def _lower_first_compare(a, b):
    # case only matters if the strings are equal ignoring case
    if a.lower() == b.lower():
        for i, ch in enumerate(a):
            if ch != b[i]:
                return ch.islower() and -1 or 1
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
