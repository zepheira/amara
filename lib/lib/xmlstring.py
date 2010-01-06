# -*- encoding: utf-8 -*-
# 
# amara.lib.xmlstring
# © 2008, 2009 by Uche Ogbuji and Zepheira LLC
#

import re
from string import *

from amara._xmlstring import *

__all__ = [
    'lstrip', 'rstrip', 'strip',
    'isname', 'isncname', 'isnmtoken', 'isqname', 'isspace', 'splitqname',
    'legalize',
    'U',
    ]

def U(s, encoding='utf-8'):
    """
    Apply a set of heuristics to the object to figure out how best
    to get text from it.
    
    XML is just text. Unfortunately there's a lot that gets in the way of the
    text in common usage: data types, XPath strings (very close, but not exactly
    the same thing as Python Unicode objects), Python string objects, character
    encodings, etc.  This function does its best to cut through all the complexity
    and get you back as conveniently as possible to what's important: the text
    
    import amara
    from amara.lib import U
    x = amara.parse('<a x="1">spam</a>')
    U(x.xml_select('a'))
    """
    from amara.xpath import datatypes
    #xpath.datatypes.string is a subclass of Unicode object, so it won't fall through
    #the test below into the XPath section proper
    if isinstance(s, datatypes.string): return unicode(s)
    #If it's already a Unicode object, nothing to do
    if isinstance(s, unicode): return s
    #If it's a string, decode it to yield Unicode
    if isinstance(s, str): return s.decode(encoding)
    #If it's an XPath data type object, apply the equivalent of the XPath string() function
    if isinstance(s, datatypes.xpathobject): return unicode(datatypes.string(s))
    if s is None:
        #FIXME: L10N
        raise TypeError('Refusing to coerce None into Unicode')
    #Otherwise just leap into default coercions
    try:
        return unicode(s)
    except TypeError, e:
        return str(s).decode(encoding)

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

