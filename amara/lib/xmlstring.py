########################################################################
# amara/lib/xmlstring.py

from string import *
from amara._xmlstring import *

__all__ = [
    'lstrip', 'rstrip', 'strip',
    'isname', 'isncname', 'isnmtoken', 'isqname', 'isspace', 'splitqname',
    'U',
    ]

def U(s):
    if isinstance(s, unicode): return s
    if isinstance(s, str): return s.decode('utf-8')
    if s is None: return None
    return unicode(s, 'utf-8')

