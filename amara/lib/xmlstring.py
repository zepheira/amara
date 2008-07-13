#XmlStrLStrip', 'XmlStrRStrip', 'XmlStrStrip', 'isname', 'isncname', 'isnmtoken', 'isqname', 'isspace', 'isxml', 'splitqname'
from amara._xmlstring import *

xml_str_lstrip = XmlStrLStrip
xml_str_rstrip = XmlStrRStrip
xml_str_strip = XmlStrStrip

from string import *

def U(s):
    if isinstance(s, unicode): return s
    return s.decode('utf-8')

