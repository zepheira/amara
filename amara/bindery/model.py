########################################################################
# amara/bindery/model.py

"""
Bindery node XML model tools
"""

__all__ = [
'constraint', 'child_element_constraint', 'attribute_constraint',
'content_model',
'named_node_test', 'document_model', 'examplotron_model',
'ATTIBUTE_AXIS',
]

import sys
#import re
import sets
import itertools
import warnings
import copy
from functools import *

from amara import tree
from amara.namespaces import *
from amara.lib.xmlstring import *
from amara.lib.util import *
from amara.xpath import datatypes
from amara.xpath.util import *

ATTIBUTE_AXIS = u'@'

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
        return named_node_test(self.ns, self.local, node, axis=ATTIBUTE_AXIS)


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
        assertion = partial(named_node_test, self.ns, self.local) if self.ns else self.local
        constraint.__init__(self, assertion, fixup=(self.set_default if default else None))

    def set_default(self, node):
        #XXX: Should be able to reuse named_node_test function
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


def named_node_test(child_ns, child_local, node, axis=u''):
    '''
    Return an XPath node test for the given child element on the given node
    '''
    for prefix, ns in node.xml_namespaces.items():
        if ns == child_ns:
            #Use this prefix, as long as it's not the default NS
            if not prefix: break
            return axis + prefix + u':' + child_local
    #Probably better to just pass in a temp prefix mapping here
    return u'%s*[namespace-uri()="%s" and local-name()="%s"]'%(axis, child_ns or u'', child_local)


class content_model:
    def __init__(self):
        self.element_types = {}
        self.attribute_types = {}
        self.constraints = []
        self.entities = set()
        self.metadata_resource_expr = None
        self.metadata_rel_expr = None
        self.metadata_value_expr = None
        return

    def add_constraint(self, constraint, validate=False):
        self.constraints.append(constraint)
        if validate: self.validate()
        return

    def validate(self, node=None):
        #print repr(node)
        #re-validate all constraints, not just this one (interlocking constraints will likely be coming in future)
        if node:
            #Check all constraints
            for constraint in self.constraints:
                constraint.validate(node)
            #Make sure all known element types have corresponding properties on the node class
            for (ns, local), (pname, default) in self.element_types.iteritems():
                if not hasattr(node, pname):
                    from amara.bindery.nodes import node
                    setattr(node.__class__, pname, bound_element(ns, local))
        else:
            for d in self.entities:
                subtree = element_subtree_iter(d, include_root=True)
                for e in subtree:
                    if e.xml_model == self:
                        self.validate(e)
        return

    def default_value(self, ns, local):
        pass

    def debug(self, node=None):
        for c in self.constraints:
            print >> sys.stderr, (c.assertion if node else c.assertion(node))
        return

    def generate_metadata(self, root):
        '''
        Process an document for metadata according to extraction cues
        '''
        metadata = []
        def handle_element(elem, resource):
            #print elem.xml_name, (elem.xml_model.metadata_resource_expr, elem.xml_model.metadata_rel_expr, elem.xml_model.metadata_value_expr)
            new_resource = None
            if elem.xml_model.metadata_resource_expr:
                new_resource = datatypes.string(elem.xml_select(elem.xml_model.metadata_resource_expr))
            if elem.xml_model.metadata_rel_expr:
                rel = datatypes.string(elem.xml_select(elem.xml_model.metadata_rel_expr))
                if elem.xml_model.metadata_value_expr:
                    val = datatypes.string(elem.xml_select(elem.xml_model.metadata_value_expr))
                elif new_resource is not None:
                    val = new_resource
                else:
                    val = elem.xml_select(u'string(.)')
                metadata.append((unicode(resource), unicode(rel), simplify(val)))
                #Basically expandqname first
                #prefix, local = splitqname(rattr)
                #try:
                #    ns = elem.xml_namespaces[prefix]
                #    resource = ns + local
                #except KeyError:
                #    resource = rattr
            if new_resource is not None: resource = new_resource
            for child in elem.xml_elements:
                handle_element(child, resource)
            return
        #Make sure we skip any entities and start with top element(s)
        if isinstance(root, tree.entity):
            for elem in root.xml_elements:
                #FIXME: use elem.xml_base when it doesn't core dump :)
                handle_element(elem, root.xml_base)
        else:
            handle_element(root, elem.xml_base)
        return metadata


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
        #raise NotImplementedErr


AKARA_NS = u'http://purl.org/dc/org/xml3k/akara'

class examplotron_model(document_model):
    '''
    XML model information and metadata extraction cues from an examplotron document
    '''
    def __init__(self, egdoc):
        from amara import bindery
        self.model_document = bindery.parse(egdoc)
        self.setup_model()
    
    def setup_model(self, parent=None):
        '''
        Process an examplotron document for constraints
        '''
        NSS = {u'ak': AKARA_NS}
        parent = parent if parent is not None else self.model_document
        allowed_elements_test = []
        for e in parent.xml_elements:
            #Constraint info
            eg_occurs = e.xml_attributes.get((EG_NAMESPACE, 'occurs'))
            if not (e.xml_namespace, e.xml_local) in parent.xml_model.element_types:
                parent.xml_model.element_types[e.xml_namespace, e.xml_local] = (self.model_document.xml_pyname(e.xml_namespace, e.xml_local), None)
            if not eg_occurs in [u'?', u'*']:
                c = child_element_constraint(e.xml_namespace, e.xml_local)
                parent.xml_model.add_constraint(c)
            if not eg_occurs in [u'+', u'*']:
                parent.xml_model.add_constraint(
                    constraint(u'count(%s) = 1'%named_node_test(e.xml_namespace, e.xml_local, parent), msg=u'Only one instance of element allowed')
                )
            allowed_elements_test.append(named_node_test(e.xml_namespace, e.xml_local, parent))

            #Metadata extraction cues
            #FIXME: Compile these XPath expressions
            rattr = e.xml_select(u'@ak:resource', NSS)
            if rattr:
                #ak:resource="" should default to a generated ID
                e.xml_model.metadata_resource_expr = rattr[0].xml_value or u'generate-id()'
            #rattr = e.xml_select(u'string(@ak:resource)', NSS)
            #if rattr: e.xml_model.metadata_resource_expr = rattr
            relattr = e.xml_select(u'string(@ak:rel)', NSS)
            if relattr: e.xml_model.metadata_rel_expr = relattr
            valattr = e.xml_select(u'string(@ak:value)', NSS)
            if valattr: e.xml_model.metadata_value_expr = valattr
            #print e.xml_name, (e.xml_model.metadata_resource_expr, e.xml_model.metadata_rel_expr, e.xml_model.metadata_value_expr)
            
            #Recurse to process children
            self.setup_model(e)

        if allowed_elements_test:
            parent.xml_model.add_constraint(
                constraint(u'count(%s) = count(*)'%u'|'.join(allowed_elements_test), msg=u'Invalid elements present')
            )
        else:
            parent.xml_model.add_constraint(
                constraint(u'not(*)', msg=u'Element should be empty')
            )

        
