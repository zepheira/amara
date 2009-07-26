########################################################################
# amara/xpath/__init__.py
"""
Implementation of the standard XPath object types
"""

from amara.xpath._datatypes import *

__all__ = ('xpathobject', 'string', 'number', 'boolean', 'nodeset',
           'EMPTY_STRING',
           'NOT_A_NUMBER', 'POSITIVE_INFINITY', 'NEGATIVE_INFINITY',
           'TRUE', 'FALSE',
           )

# Add the string constants
EMPTY_STRING = string.EMPTY

# Add the number constants
NOT_A_NUMBER, POSITIVE_INFINITY, NEGATIVE_INFINITY = \
    number.NaN, number.POSITIVE_INFINITY, number.NEGATIVE_INFINITY

# Add the boolean constants
TRUE, FALSE = boolean.TRUE, boolean.FALSE
