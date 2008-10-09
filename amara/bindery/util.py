########################################################################
# amara/bindery/util.py

"""
Some utilities for Amara bindery
"""

from amara.lib.util import *

def property_str_getter(propname, node):
    return unicode(getattr(node, propname))

#A more general purpose converter utiliy
def property_getter(propname, node, converter=unicode):
    return converter(getattr(node, propname))

