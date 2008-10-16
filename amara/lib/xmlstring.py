########################################################################
# amara/lib/xmlstring.py

import re
from string import *

from amara._xmlstring import *

__all__ = [
    'lstrip', 'rstrip', 'strip',
    'isname', 'isncname', 'isnmtoken', 'isqname', 'isspace', 'splitqname',
    'legalize',
    'U',
    ]

def U(s):
    if isinstance(s, unicode): return s
    if isinstance(s, str): return s.decode('utf-8')
    if s is None: return None
    return str(s).decode('utf-8')

#Basic idea is as old as the XML spec, but was good to reuse a regex at
#http://maxharp3r.wordpress.com/2008/05/15/pythons-minidom-xml-and-illegal-unicode-characters/

#from http://boodebr.org/main/python/all-about-python-and-unicode#UNI_XML
RE_XML_ILLEGAL_PAT = u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                     u'|' + \
                     u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
                       (unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
                        unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
                        unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff))
RE_XML_ILLEGAL = re.compile(RE_XML_ILLEGAL_PAT)

def legalize(s, repl=u'?'):
    '''
    >>> from amara.lib.xmlstring import legalize
    >>> legalize(u'A\u001aB\u0000C')
    u'A?B?C'
    
    '''
    return RE_XML_ILLEGAL.subn(repl, s)[0]

