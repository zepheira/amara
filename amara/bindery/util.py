########################################################################
# amara/bindery/util.py

"""
Some utilities for Amara bindery
"""

import sys
from amara import tree
from amara.lib.util import *
from amara.xpath import context, parser

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
ALL_MODES = u'*'

class node_handler(object):
    '''
    A decorator
    '''
    def __init__(self, test, mode=None, priority=0):
        self.test = test if type(test) in (list, tuple) else [test]
        self.priority = priority
        self.mode = mode

    def __call__(self, func):
        func.test = self.test
        func.mode = self.mode
        func.priority = self.priority
        return func

#

#A simple, XSLT-like dispatch system
class dispatcher(object):
    def __init__(self):
        self.node_handlers = []
        for obj in ( getattr(self, name) for name in dir(self) ):
            test = getattr(obj, 'test', None)
            if test is not None:
                self.node_handlers.append((obj.priority, obj))
        #Using bisect or cmp for sorted might be more efficient, but in general dispatcher handler sets
        #will be small enough not to matter
        self.node_handlers = [ obj for (priority, obj) in sorted(self.node_handlers, reverse=True) ]
        self.cached_xpath = {}
        return
    
    def check_xpath(self, test, node):
        '''
        The XPath check is reminiscent of the XSLT pattern check.
        If any ancestor of the node can be used as context for the test XPath,
        such that the node is in the resulting node set, the test succeeds
        '''
        #FIXME: optimize, at least for the simple node test case.  No need to climb all the way up the tree for that
        #for i, t in enumerate(obj.test):
            #FIXME: add support for python callable tests
        #    if isinstance(t, basestring):
        #        obj.test[i:i+1] = []
        
        if test not in self.cached_xpath:
            self.cached_xpath[test] = parser.parse(test)
        test = self.cached_xpath[test]
        #if hasattr(test, 'evaluate'):
        #if isinstance(test, unicode):
        cnode = node
        while cnode.xml_parent is not None:
            if node in test.evaluate(context(cnode.xml_parent, namespaces=cnode.xml_parent.xml_namespaces)):
                return True
            cnode = cnode.xml_parent
        return False

    def dispatch(self, node, mode=None):
        for handler in self.node_handlers:
            for test in handler.test:
                if (callable(test) and test(self, node)) or self.check_xpath(test, node):
                    if handler.mode in (mode, ALL_MODES):
                        for chunk in handler(node): yield chunk
                        return

    @node_handler(u'node()', ALL_MODES, DEFAULTY_PRIORITY)
    def default_node(self, node):
        if isinstance(node, tree.element) or isinstance(node, tree.entity):
            #print 'default_element'
            for child in node.xml_children:
                for chunk in self.dispatch(child):
                    yield chunk
        elif isinstance(node, tree.text):
            #print 'default_node'
            #yield unicode(node.xml_select(u'string(.)'))
            yield node.xml_value

