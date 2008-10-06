########################################################################
# amara/bindery/nodes.py

"""
Bindery node XML model tools
"""

__all__ = [
'constraint', 'child_element_constraint', 'attribute_constraint',
'content_model',
'element_node_test', 'document_model', 'examplotron_model',
]

import sys
#import re
import sets
import itertools
import warnings
import copy
from functools import *

from amara import tree
from amara.lib.xmlstring import *
from amara.xpath import datatypes

class constraint(object):
    '''
    Represents a constraint on an XML model
    '''
    def __init__(self, assertion, fixup=None, msg=None):
        self.assertion = assertion
        self.fixup = fixup
        self.msg = msg
    
    def validate(self, node):
        '''
        Check this constraint against a node.
        Raise an exception if the constraint fails, possibly after attempting fixup
        '''
        from amara.bindery import BinderyError
        assertion = self.assertion
        if callable(assertion):
            assertion = assertion(node)
        result = datatypes.boolean(node.xml_select(assertion))
        if not result:
            if self.fixup:
                self.fixup(node)
                result = datatypes.string(node.xml_select(assertion))
                if result:
                    return
            raise BinderyError(BinderyError.CONSTRAINT_VIOLATION, constraint=self.msg or assertion)


class attribute_constraint(constraint):
    '''
    Constraint representing the presence of an attribute on an element
    '''
    def __init__(self, ns, local, default=None):
        self.ns = ns
        self.local = local
        self.default = default
        assertion = self.assertion if self.ns else u'@' + self.local
        constraint.__init__(self, assertion, fixup=(self.set_default if default else None))

    def set_default(self, node):
        node.xml_attributes[self.ns, self.local] = self.default

    def assertion(self, node):
        for prefix, ns in node.xml_namespaces:
            if ns == self.ns:
                #Use this prefix, as long as it's not the default NS
                if not prefix: break
                return u'@' + prefix + u':' + self.local
        #Probably better to just pass in a temp prefix mapping here
        return u'@*[namespace-uri()="%s" and local-name()="%s"]'%(self.ns or u'', self.local)


class child_element_constraint(constraint):
    '''
    Constraint representing the presence of a simple child element
    '''
    #XXX: We could make this a bit more flexible by allowing the user to specify an
    #XML fragment as well as simple text default content
    def __init__(self, ns, local, default=None):
        self.ns = ns
        self.local = local
        self.default = default
        assertion = partial(element_node_test, self.ns, self.local) if self.ns else self.local
        constraint.__init__(self, assertion, fixup=(self.set_default if default else None))

    def set_default(self, node):
        #What prefix to use
        for prefix, ns in node.xml_namespaces.items():
            if ns == self.ns and prefix:
                qname = prefix + u':' + self.local
                break
        else:
            #No prefix: just hijack the default namespace
            qname = self.local
        ownerdoc = node.xml_select(u'/')[0]
        eclass = ownerdoc.eclass(self.ns, self.local)
        new_elem = eclass(self.ns, qname)
        new_elem.xml_append(tree.text(self.default))
        node.xml_append(new_elem)
        return


def element_node_test(child_ns, child_local, node):
    '''
    Return an XPath node test for the given child element on the given node
    '''
    for prefix, ns in node.xml_namespaces.items():
        if ns == child_ns:
            #Use this prefix, as long as it's not the default NS
            if not prefix: break
            return prefix + u':' + child_local
    #Probably better to just pass in a temp prefix mapping here
    return u'*[namespace-uri()="%s" and local-name()="%s"]'%(child_ns or u'', child_local)


class content_model:
    def __init__(self):
        self.element_types = {}
        self.attribute_types = {}
        self.constraints = []
        self.entities = set()
        return

    def add_constraint(self, constraint, validate=False):
        self.constraints.append(constraint)
        if validate: self.validate()
        return

    def validate(self, node=None):
        if node:
            for constraint in self.constraints:
                constraint.validate(node)
        else:
            #Make this more efficient?  How?  A list of applicable elements per model will take up a good bit of memory
            #candidate_classmates = self.xml_select(u'//*')
            for d in self.entities:
                for e in d.xml_select(u'//*'): #Should be less of a waste once XPath result node sets are lazy
                    #re-validate all constraints, not just this one (interlocking constraints will likely be coming in future)
                    if e.xml_model == self:
                        self.validate(e)
        return

    def default_value(self, ns, local):
        pass

    def debug(self, node=None):
        for c in self.constraints:
            print >> sys.stderr, (c.assertion if node else c.assertion(node))
        return

#        node.xml_model.constraints.append(u'@xml:id', validate=True)      #Make xml:id required.  Will throw a constraint violation right away if there is not one.  Affects all instances of this class.
#        node.xml_model.validate(recurse=True)     #Recursively validate constraints on node and all children


#No constraints by default
#DEFAULT_MODEL = content_model()

class document_model(object):
    '''
    Represents XML model information set up for an entire document
    '''
    #def __init__(self):
    #    self.model_document = None
    
    def clone(self):
        '''
        Return a new, empty document incorporating the model information
        '''
        raise NotImplementedErr
        from amara.bindery import BinderyError
        assertion = self.assertion


class examplotron_model(document_model):
    '''
    XML model information from an examplotron document
    '''
    def __init__(self, egdoc):
        from amara import bindery
        self.model_document = bindery.parse(egdoc)
        self.generate_constraints()
    
    def clone(self, document_uri=None):
        '''
        Return a new, empty document incorporating the model information
        '''
        from amara.bindery import nodes
        doc = nodes.entity_base(document_uri)
        doc.xml_model_ = self.model_document.xml_model_
        doc._eclasses = self.model_document._eclasses.copy()
        doc._class_names = self.model_document._class_names.copy()
        doc._names = self.model_document._names.copy()
        for c in doc._eclasses.values():
            c.xml_model_.entities.add(doc)
        return doc

    def generate_constraints(self, parent=None):
        '''
        Process an examplotron document for constraints
        '''
        parent = parent or self.model_document
        allowed_elements_test = []
        for e in parent.xml_elements():
            c = child_element_constraint(e.xml_namespace, e.xml_local)
            parent.xml_model.add_constraint(c)
            self.generate_constraints(parent=e)
            allowed_elements_test.append(element_node_test(e.xml_namespace, e.xml_local, parent))
        parent.xml_model.add_constraint(
            constraint(u'count(%s) = count(*)'%u'|'.join(allowed_elements_test), msg=u'Invalid elements present')
        )


