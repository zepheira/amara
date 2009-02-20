########################################################################
# amara/bindery/util.py

"""
Some utilities for Amara bindery
"""

import sys
from amara import tree
from amara.lib.util import *

def property_str_getter(propname, node):
    '''
    A tool (use with functools.partial) for creating smart getters that can access an element
    whether or not it appears in the XML, returning its string value
    
    doc = "<a><b><c>spam</c></b><b/></a>"
    import functools
    from amara.bindery.util import property_str_getter
    #Use the bound name of the XML construct
    c_str = functools.partial(property_str_getter('c'))
    c_str(doc.a.b) #Return u'spam'
    c_str(doc.a.b[1]) #Return u''
    '''
    return unicode(getattr(node, propname))

def property_sequence_getter(propname, node):
    '''
    A tool (use with functools.partial) for creating smart getters that can access an element
    whether or not it appears in the XML, returning an empty list if not
    
    doc = "<a><b><c/></b><b/></a>"
    import functools
    from amara.bindery.util import property_sequence_getter
    #Use the bound name of the XML construct
    c_list = functools.partial(property_sequence_getter('c'))
    c_list(doc.a.b) #Return the one c element in a list
    c_list(doc.a.b[1]) #Return an empty list
    '''
    return list(getattr(node, propname, []))

#A more general purpose converter utiliy
def property_getter(propname, node, converter=unicode):
    return converter(getattr(node, propname))


DEFAULTY_PRIORITY = -sys.maxint-1

class node_handler(object):
    '''
    A decorator
    '''
    def __init__(self, test, priority=0):
        self.test = test if type(test) in (list, tuple) else [test]
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
    
    def check_xpath(self, test, node):
        '''
        The XPath check is reminiscent of the XSLT pattern check.
        If any ancestor of the node can be used as context for the test XPath,
        such that the node is in the resulting node set, the test succeeds
        '''
        if isinstance(test, unicode):
            context = node
            while context.xml_parent is not None:
                if node in context.xml_parent.xml_select(test):
                    return True
                context = context.xml_parent
        return False

    def dispatch(self, node):
        for handler in self.node_handlers:
            for test in handler.test:
                if (callable(test) and test(self, node)) or self.check_xpath(test, node):
                    for chunk in handler(node): yield chunk
                    return

    @node_handler(u'node()', DEFAULTY_PRIORITY)
    def default_node(self, node):
        if isinstance(node, tree.element):
            #print 'default_element'
            for child in node.xml_children:
                for chunk in self.dispatch(child):
                    yield chunk
        else:
            #print 'default_node'
            yield unicode(node.xml_select(u'string(.)'))


