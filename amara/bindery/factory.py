########################################################################
# amara/bindery/factory.py

"""
Factory functions for bindery nodes
"""

import re
from xml.dom import Node

from amara.lib.xmlstring import *
import nodes

class factory(object):
    '''
    Manager class for the process of serializing XML to a binding
    '''
    PY_REPLACE_PAT = re.compile(u'[^a-zA-Z0-9_]')
    
    def __init__(self):
        self._eclasses = {}
        self._class_names = {}
        self._names = {}

    def pyname(self, ns, qname, exclude=None):
        '''
        ns - the XML namespace
        qname - the XML QName
        exclude - iterator of names not to use (e.g. to avoid clashes)
        '''
        python_id = self._names.get((local, ns))
        if not python_id:
            python_id = self.PY_REPLACE_PAT.sub('_', local)
            if python_id in RESERVED_NAMES:
                python_id = python_id + '_'
            self._names[(local, ns)] = python_id
        if exclude:
            while python_id in exclude:
                python_id += '_'
        return python_id

    def xname(self, python_id):
        #XML NMTOKENS are a superset of Python IDs
        return python_id

    def element(self, ns, qname, pname=None):
        prefix, local = splitqname(qname)
        if not pname: pname = self.pyname(ns, qname)
        if (ns, local) not in self._eclasses:
            unique = False
            while not unique:
                class_name = self.PY_REPLACE_PAT.sub('_', local)
                if class_name in RESERVED_NAMES: class_name += '_'
            eclass = type(class_name, (nodes.element_base,))
            self._eclasses[(ns, local)] = eclass
        else:
            eclass = self._eclasses[(ns, local)]
        e = eclass(ns, qname)
        return e

    def entity(self, document_uri=None):
        return nodes.entity_base(document_uri=document_uri)


DEFAULT_FACTORIES = {
    Node.DOCUMENT_NODE: factory.entity,
    Node.ELEMENT_NODE: factory.element,
}

