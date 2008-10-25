########################################################################
# amara/html.py
"""

"""

__all__ = [
'Document', 'Doctype', 'Comment', 'Element',
]

import copy
import itertools
from functools import *
from itertools import *

import html5lib
from amara import tree
from amara.lib import inputsource
from amara.bindery import nodes
from amara.lib.xmlstring import *

class node(html5lib.treebuilders._base.Node):
    appendChild = tree.element.xml_append
    removeChild = tree.element.xml_remove
    parent = tree.node.xml_parent
    value = tree.text.xml_value

    def insertText(self, data, insertBefore=None):
        """Insert data as text in the current node, positioned before the 
        start of node insertBefore or to the end of the node's text.
        """
        if insertBefore:
            self.insertBefore(tree.text(data), insertBefore)
        else:
            self.xml_append(tree.text(data))

    def insertBefore(self, node, refNode):
        """Insert node as a child of the current node, before refNode in the 
        list of child nodes. Raises ValueError if refNode is not a child of 
        the current node"""
        offset = self.xml_index(refNode)
        self.xml_insert(offset, node)

    def cloneNode(self):
        """Return a shallow copy of the current node i.e. a node with the same
        name and attributes but with no parent or child nodes
        """
        return copy.deepcopy(self)

    def hasContent(self):
        """Return true if the node has children or text, false otherwise
        """
        return bool(list(xml_children))


class element(nodes.element_base, node):
    '''
    attributes - a dict holding name, value pairs for attributes of the node        childNodes - a list of child nodes of the current node. This must 
    include all elements but not necessarily other node types
    _flags - A list of miscellaneous flags that can be set on the node
    '''
    name = nodes.element_base.xml_qname
    childNodes = nodes.element_base.xml_children
    def __init__(self, ns, qname):
        nodes.element_base.__init__(self, ns, qname)
        self._flags = []
        return

    def xml_set_attributes_(self, attrs):
        for key, val in attrs.iteritems():
            self.xml_attributes[None, key] = val
        return

    def xml_get_attributes_(self, attrs):
        return self.xml_attributes

    attributes = property(xml_get_attributes_, xml_set_attributes_, None, "html5lib uses this property to manage HTML element attrs")


class entity(node, nodes.entity_base):
    """
    Base class for entity nodes (root nodes--similar to DOM documents and document fragments)
    """
    xml_exclude_pnames = ('name', 'parent', 'appendChild', 'removeChild', 'removeChild', 'value', 'attributes', 'childNodes')
    xml_element_base = element
    def __init__(self, document_uri=None):
        nodes.entity_base.__init__(self, document_uri)
        return


class comment(tree.comment):
    type = 6
    value = tree.text.xml_value
    def __init__(self, data):
        tree.comment.__init__(self, data)
        self.data = data

    def toxml(self):
        return "<!--%s-->" % self.data

    #def hilite(self):
    #    return '<code class="markup comment">&lt;!--%s--></code>' % escape(self.data)


class doctype(tree.node, html5lib.treebuilders.simpletree.DocumentType):
    def __new__(cls, name, publicId, systemId):
        return tree.node.__new__(cls)

    def __init__(self, name, publicId, systemId):
        self.xml_public_id = publicId
        self.xml_system_id = systemId
        self.xml_name = name

def doctype_create(dummy, name, publicId, systemId):
    c = comment(u'')
    c.xml_public_id = publicId
    c.xml_system_id = systemId
    c.xml_name = name
    return c

class treebuilder(html5lib.treebuilders._base.TreeBuilder):
    documentClass = entity
    #elementClass = xml_element_factory
    commentClass = comment
    doctypeClass = doctype_create
    
    def __init__(self):
        self.entity = entity()
        html5lib.treebuilders._base.TreeBuilder.__init__(self)
        def eclass(name):
            return self.entity.xml_element_factory(None, str(name))
        self.elementClass = eclass
    

def parse(source):
    '''
    
    '''
    #from amara.bindery import html; doc = html.parse("http://www.hitimewine.net/istar.asp?a=6&id=161153!1247")
    #parser = html5lib.HTMLParser()
    parser = html5lib.HTMLParser(tree=treebuilder)
    return parser.parse(inputsource(source, None).stream)

