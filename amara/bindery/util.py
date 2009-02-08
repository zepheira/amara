########################################################################
# amara/bindery/util.py

"""
Some utilities for Amara bindery
"""

import sys
from amara import tree
from amara.lib.util import *

def property_str_getter(propname, node):
    return unicode(getattr(node, propname))

#A more general purpose converter utiliy
def property_getter(propname, node, converter=unicode):
    return converter(getattr(node, propname))


DEFAULTY_PRIORITY = -sys.maxint-1

class node_handler(object):
    '''
    A decorator
    '''
    def __init__(self, test, priority=0):
        self.test = test
        self.priority = priority

    def __call__(self, func):
        func.test = self.test
        func.priority = self.priority
        return func


#A simple, XSLT-like dispatch system
class dispatcher(object):
    def __init__(self):
        self.node_handlers = []
        for obj in ( getattr(self, name) for name in dir(self) ):
            test = getattr(obj, 'test', None)
            if test:
                self.node_handlers.append((obj.priority, obj))
        #Using bisect or cmp for sorted might be more efficient, but in general dispatcher handler sets
        #will be small enough not to matter
        self.node_handlers = [ obj for (priority, obj) in sorted(self.node_handlers, reverse=True) ]
        return
    
    def check_xpath(self, handler, node):
        '''
        The XPath check is reminiscent of the XSLT pattern check.
        If any ancestor of the node can be used as context for the test XPath,
        such that the node is in the resulting node set, the test succeeds
        '''
        if isinstance(handler.test, unicode):
            context = node
            while context.xml_parent is not None:
                if node in context.xml_parent.xml_select(handler.test):
                    return True
                context = context.xml_parent
        return False

    def dispatch(self, node):
        for handler in self.node_handlers:
            if (callable(handler.test) and handler.test(self, node)) or self.check_xpath(handler, node):
                for chunk in handler(node): yield chunk
                break
        else:
            yield unicode(node.xml_select(u'string(.)'))

    @node_handler(u'*', DEFAULTY_PRIORITY)
    def default_node(self, node):
        if isinstance(node, tree.element):
            #print 'default_element'
            for child in node.xml_children:
                for chunk in self.dispatch(child):
                    yield chunk
        else:
            #print 'default_node'
            yield unicode(node.xml_select(u'string(.)'))


