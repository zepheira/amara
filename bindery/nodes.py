__all__ = [
'binder', 'TOP', 'ANY_NAMESPACE', 'REMOVE_RULE',
'PY_REPLACE_PAT', 'RESERVED_NAMES'
]

import re
import sets
import keyword
import warnings
import cStringIO
import bisect
           
#Only need to list IDs that do not start with "xml", "XML", etc.
RESERVED_NAMES = [
    '__class__', '__delattr__', '__dict__', '__doc__', '__getattribute__',
    '__getitem__', '__hash__', '__init__', '__iter__', '__module__',
    '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__',
    '__str__', '__unicode__', '__weakref__', '_childNodes', '_docIndex',
    '_localName', '_namespaceURI', '_parentNode', '_prefix', '_rootNode',
    'childNodes', 'docIndex', 
    'localName', 'namespaceURI', 'next_elem', 'nodeName', 'nodeType',
    'ownerDocument', 'parentNode', 'prefix', 'rootNode', 'locals',
    'None'
    ]

RESERVED_NAMES.extend(keyword.kwlist)

RESERVED_NAMES = sets.ImmutableSet(RESERVED_NAMES)

ANY_NAMESPACE = 'http://purl.xml3k.org/amara/reserved/any-namespace'

#FIXME: Use proper L10N (gettext)
def _(t): return t




