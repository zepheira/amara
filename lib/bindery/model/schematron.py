########################################################################
# amara/bindery/model/examplotron.py

"""
Schematron specialization of bindery node XML model tools
"""

__all__ = [
'schematron_model',
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
from amara.lib.util import first_item
from amara.bindery import BinderyError
from amara.bindery.model import document_model, constraint, child_element_constraint, named_node_test, NODE_ID_MARKER
from amara.xpath import datatypes
from amara.xpath.util import top_namespaces, named_node_test
from amara.namespaces import AKARA_NAMESPACE, STRON_NAMESPACE, OLD_STRON_NAMESPACE
from amara.bindery.util import dispatcher, node_handler

class schematron_model(document_model, dispatcher):
    '''
    XML model information and metadata extraction cues from an examplotron document
    '''
    def __init__(self, schdoc):
        from amara import bindery
        dispatcher.__init__(self)
        self.model_document = bindery.parse(schdoc)
        self.model_document.xml_model.prefixes = top_namespaces(self.model_document)
        self.rules = []
        self.setup_model()
        return
    
    def setup_model(self, parent=None):
        '''
        Process a schematron document for constraints
        '''
        NSS = {u'ak': AKARA_NAMESPACE, u'sch': STRON_NAMESPACE}
        if parent is None:
            parent = self.model_document
        parent.xml_namespaces.update(NSS)
        list(self.dispatch(parent))
        return
    
    @node_handler(u'sch:schema')
    def schema(self, node):
        #print >> sys.stderr, "GRIPPO", node.xml_children
        for child in node.xml_children:
            for chunk in self.dispatch(child):
                yield None
        #list(chain(*imap(self.dispatch, node.xml_children)))

    #@node_handler(u'sch:schema')
    #def schema(self, node):
    
    @node_handler(u'sch:schema/sch:pattern')
    def pattern(self, node):
        list(chain(*imap(self.dispatch, node.xml_children)))

    @node_handler(u'sch:pattern/sch:rule')
    def rule(self, node):
        context_elem = first_item(e.xml_select(u'ak:resource'))
        if context_elem:
            resource = U(context_elem.select)
        self.rules.append((U(node.context), resource, []))
        list(chain(*imap(self.dispatch, node.xml_children)))

    @node_handler(u'sch:rule/sch:report')
    def report(self, node):
        curr_report_list = self.rules[-1][1]
        curr_report_list.append((node.test, []))
        relelems = e.xml_select(u'ak:rel')
        for relelem in relelems:
            curr_rel_list = curr_report_list[-1][1]
            curr_rel_list.append(U(rel.name), U(rel.value))

    def generate_metadata(self, root):
        '''
        Process a document to extract metadata
        Amara allows you to embed metadata extraction cues into an examplotron document
        These cues are worked into the model, and are used to drive the extraction from the
        instance at root
        '''
        prefixes = root.xml_model.prefixes
        print >> sys.stderr, "STACEY"
        def handle_node(node, resource):
            print >> sys.stderr, "GRIPPO", node, resource
            for (context, resource, report_list) in self.rules():
                if self.check_xpath(context, node):
                    for (test, rel_list) in report_list:
                        if node.xml_select(test):
                            for (relname, relvalue) in rel_list:
                                yield (resource, relname, relvalue)
            #
            for child in node.xml_children:
                for item in handle_node(child, resource):
                    yield item
            return

        return ( item for item in handle_node(root, root.xml_base) )

