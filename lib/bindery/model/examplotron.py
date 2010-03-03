########################################################################
# amara/bindery/model/examplotron.py

"""
Examplotron specialization of bindery node XML model tools
"""

__all__ = [
'examplotron_model',
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
from amara.bindery import BinderyError
from amara.bindery.model import document_model, constraint, child_element_constraint, named_node_test, NODE_ID_MARKER
from amara.xpath import datatypes
from amara.xpath.util import top_namespaces, named_node_test, node_test
from amara.xpath import context, parser

from amara.namespaces import AKARA_NAMESPACE, EG_NAMESPACE

class examplotron_model(document_model):
    '''
    XML model information and metadata extraction cues from an examplotron document
    '''
    def __init__(self, egdoc):
        from amara import bindery
        self.model_document = bindery.parse(egdoc)
        self.model_document.xml_model.prefixes = top_namespaces(self.model_document)
        self.setup_model()
        return
    
    def setup_model(self, parent=None):
        '''
        Process an examplotron document for constraints
        '''
        NSS = {u'ak': AKARA_NAMESPACE, u'eg': EG_NAMESPACE}
        parent = parent if parent is not None else self.model_document
        allowed_elements_test = []
        if isinstance(parent, tree.element):
            #for a in parent.xml_attributes:
            #FIXME: Hack until this issue is fixed: http://trac.xml3k.org/ticket/8
            for a in dict(parent.xml_attributes.items()):
                if a[0] not in [EG_NAMESPACE, AKARA_NAMESPACE]:
                    parent.xml_model.attribute_types[a] = (self.model_document.xml_pyname(a[0], a[1], iselement=False), None)
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
            mod = e.xml_model
            rattr = e.xml_select(u'@ak:resource', NSS)
            if rattr:
                #ak:resource="" should default to a generated ID
                mod.metadata_resource_expr = rattr[0].xml_value or NODE_ID_MARKER
            #rattr = e.xml_select(u'string(@ak:resource)', NSS)
            #if rattr: mod.metadata_resource_expr = rattr
            relattr = e.xml_select(u'@ak:rel', NSS)
            if relattr:
                if relattr[0].xml_value:
                    mod.metadata_rel_expr = parser.parse(relattr[0].xml_value)
                else:
                    mod.metadata_rel_expr = parser.parse(u'local-name()')
            valattr = e.xml_select(u'@ak:value', NSS)
            if valattr:
                if valattr[0].xml_value:
                    mod.metadata_value_expr = parser.parse(valattr[0].xml_value)
                else:
                    mod.metadata_value_expr = parser.parse(u'.')
            context_attr = e.xml_select(u'@ak:context', NSS)
            if context_attr:
                mod.metadata_context_expr = parser.parse(context_attr[0].xml_value)
            else:
                #If it doesn't state context, don't check context
                mod.metadata_context_expr = None
                #mod.metadata_context_expr = node_test(parent, e, 'parent')

            #Apply default relationship or value expression
            #If there's ak:rel but no ak:value or ak:resource, ak:value=u'.'
            #If there's ak:value but no ak:rel or ak:resource, ak:rel=u'local-name()'
            if mod.metadata_resource_expr:
                if (mod.metadata_value_expr
                    and not mod.metadata_rel_expr):
                    mod.metadata_rel_expr = parser.parse(u'local-name()')
            else:
                if (mod.metadata_rel_expr
                    and not mod.metadata_value_expr):
                    mod.metadata_value_expr = parser.parse(u'.')
                elif (mod.metadata_value_expr
                    and not mod.metadata_rel_expr):
                    mod.metadata_rel_expr = parser.parse(u'local-name()')

            if mod.metadata_resource_expr not in (NODE_ID_MARKER, None):
                mod.metadata_resource_expr = parser.parse(mod.metadata_resource_expr)
            #if mod.metadata_rel_expr is not None:
            #    mod.metadata_rel_expr = parser.parse(mod.metadata_rel_expr)
            #if mod.metadata_value_expr is not None:
            #    mod.metadata_value_expr = parser.parse(mod.metadata_value_expr)
            relelem = e.xml_select(u'ak:rel', NSS)
            
            for rel in relelem:
                mod.other_rel_exprs.append((unicode(rel.name),unicode(rel.value)))
            #print e.xml_name, (mod.metadata_resource_expr, mod.metadata_rel_expr, mod.metadata_value_expr)
            
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
        #To do:
        #Add <ak:product ak:name="AVT" ak:value="AVT"/>

