########################################################################
# amara/bindery/model/__init__.py

"""
Bindery node XML model tools

An Amara element model (e.xml_model) is a collection of metadata and rules that characterize
the nature of an XML element

An Amara Document model (e.xml_model.) is a collection of metadata and rules that characterize the nature
of an overall XML document type

A document model might be implemented as a set of element models, or as something more
centrally expressed.

A constraint is one possible component of an element model.  

"""

__all__ = [
'constraint', 'child_element_constraint', 'attribute_constraint',
'content_model',
'named_node_test', 'document_model',
'ATTIBUTE_AXIS',
'metadata_dict',
'generate_metadata',
]

import sys
#import re
import warnings
import copy
from cStringIO import StringIO
from itertools import *
from functools import *
from operator import *

from amara import tree
from amara.lib.xmlstring import U
from amara.xpath import datatypes
from amara.xpath.util import named_node_test
from amara.bindery import BinderyError
from amara.namespaces import AKARA_NAMESPACE
from amara.xpath import context, parser

ATTIBUTE_AXIS = u'@'
NODE_ID_MARKER = u'generate-id()'

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
            raise BinderyError(BinderyError.CONSTRAINT_VIOLATION, constraint=self.msg or assertion, node=abspath(node))


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


class content_model:
    def __init__(self):
        #Used to be: {(ns, local): (python-name, default)}
        #Now, for performance, is: {(ns, local): (python-name, default)}
        self.element_types = {}
        self.attribute_types = {}
        self.constraints = []
        self.entities = set()
        self.metadata_resource_expr = None
        self.metadata_rel_expr = None
        self.metadata_value_expr = None
        self.metadata_coercion_expr = None
        self.metadata_context_expr = None
        self.other_rel_exprs = []
        self.prefixes = {}
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
        Process a document to extract metadata
        Amara allows you to embed metadata extraction cues into an examplotron document
        These cues are worked into the model, and are used to drive the extraction from the
        instance at root
        '''
        #FIXME: investigate the requirement for prefixes=prefixes for XPath, even for prefixes defined in source doc
        def handle_element(elem, resource):
            new_resource = None
            prefixes = elem.xml_root.xml_model.prefixes
            if elem.xml_model.metadata_context_expr:
                if not elem.xml_model.metadata_context_expr.evaluate(context(elem, namespaces=prefixes)):
                    return
            #Is there a cue that designates this element as a resource envelope?
            if elem.xml_model.metadata_resource_expr:
                if elem.xml_model.metadata_resource_expr == NODE_ID_MARKER:
                    #FIXME: Isn't going from unicode -> xpath str -> unicode wasteful?
                    new_resource = unicode(datatypes.string(elem.xml_nodeid))
                else:
                    new_resource = unicode(datatypes.string(elem.xml_model.metadata_resource_expr.evaluate(context(elem, namespaces=prefixes))))
            #Is there a cue that designates a relationship in this element?
            if elem.xml_model.metadata_rel_expr:
                #Execute the XPath to get the relationship name/title
                rel = datatypes.string(elem.xml_model.metadata_rel_expr.evaluate(context(elem, namespaces=prefixes)))
                if elem.xml_model.metadata_value_expr:
                    #Execute the XPath to get the relationship value
                    val = elem.xml_model.metadata_value_expr.evaluate(context(elem, namespaces=prefixes))
                elif new_resource is not None:
                    #If the element is also a resource envelope, the default value is the new resource ID
                    val = new_resource
                else:
                    #Handle the default ak:value of "."
                    val = datatypes.nodeset([elem])
                yield (unicode(resource), unicode(rel), val)
                #Basically expandqname first
                #prefix, local = splitqname(rattr)
                #try:
                #    ns = elem.xml_namespaces[prefix]
                #    resource = ns + local
                #except KeyError:
                #    resource = rattr
            if new_resource is not None: resource = new_resource

            for rel_expr, val_expr in elem.xml_model.other_rel_exprs:
                rel = datatypes.string(elem.xml_select(rel_expr, prefixes=prefixes))
                val = elem.xml_select(val_expr, prefixes=prefixes)
                yield (unicode(resource), unicode(rel), val)
            
            for child in elem.xml_elements:
                for item in handle_element(child, resource):
                    yield item
            return
        #Make sure we skip any entities and start with top element(s)
        if isinstance(root, tree.entity):
            return ( item for elem in root.xml_elements for item in handle_element(elem, root.xml_base) )
        else:
            return ( item for item in handle_element(root, root.xml_base) )


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


def generate_metadata(root):
    return root.xml_model.generate_metadata(root)

#Singleton/sentinel
MARK = object()

def metadata_dict(metadata):
    resources = {}
    first_id = MARK
    #Use sorted to ensure grouping by resource IDs
    for rid, row in groupby(sorted(metadata, key=itemgetter(0)), itemgetter(0)):
        if first_id == MARK: first_id = rid
        #entry[u'id'] = eid
        resource = {}
        #It's all crazy lazy, so use list to consume the iterator
        for (i, key, val) in row:
            if key in resource:
                if isinstance(resource[key], list):
                    resource[key].append(val)
                else:
                    resource[key] = [resource[key], val]
            else:
                resource[key] = val
        resources[rid] = resource
    return resources, first_id


from examplotron import examplotron_model

__all__.append('examplotron_model')
