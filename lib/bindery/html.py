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
from amara.namespaces import XML_NAMESPACE, XHTML_NAMESPACE


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
        return bool(list(self.xml_children))


class element(nodes.element_base, node):
    '''
    attributes - a dict holding name, value pairs for attributes of the node
    childNodes - a list of child nodes of the current node. This must
    include all elements but not necessarily other node types
    _flags - A list of miscellaneous flags that can be set on the node
    '''
    name = nodes.element_base.xml_qname
    namespace = nodes.element_base.xml_namespace
    #@property
    #def name(self):
    #    return self.xml_qname
    #@property
    #def namespace(self):
    #    return self.xml_namespace

    @property
    def nameTuple(self):
        #return XHTML_NAMESPACE, self.xml_name
        return self.xml_namespace, self.xml_qname

    def xml_get_childNodes_(self):
        return self.xml_children

    def xml_set_childNodes_(self, l):
        #No self.xml_clear() ...
        for child in self.xml_children:
            self.xml_remove(child)
        for i in l: self.xml_append(i)
        return

    childNodes = property(xml_get_childNodes_, xml_set_childNodes_, None, "html5lib uses this property to manage HTML element children")
    def __init__(self, ns, qname):
        nodes.element_base.__init__(self, ns, qname)
        self._flags = []
        return

    def xml_set_attributes_(self, attrs):
        for key, val in attrs.iteritems():
            #from amara.bindery import html; doc = html.parse('http://outreach.zepheira.com/public/rdfa/plos-10.1371-journal.pgen.1000219.html'); h = doc.xml_select(u'//h1')[0]; print h.property
            #from amara.bindery import html; doc = html.parse('/tmp/plos-10.1371-journal.pgen.1000219.html'); h = doc.xml_select(u'//h1')[0]; print h.property
            if isinstance(key, tuple):
                self.xml_attributes[key] = val
            elif key.startswith(u'xmlns'):
                prefix, local = splitqname(key)
                self.xml_namespaces[local if prefix else None] = val
            else:
                self.xml_attributes[None, key] = val
        return

    def xml_get_attributes_(self):
        return self.xml_attributes

    attributes = property(xml_get_attributes_, xml_set_attributes_, None, "html5lib uses this property to manage HTML element attrs")


class entity(node, nodes.entity_base):
    """
    Base class for entity nodes (root nodes--similar to DOM documents and document fragments)
    """
    xml_exclude_pnames = frozenset(('name', 'parent', 'appendChild', 'removeChild', 'removeChild', 'value', 'attributes', 'childNodes'))
    xml_element_base = element
    def __init__(self, document_uri=None):
        nodes.entity_base.__init__(self, document_uri)
        return
    __repr__ = nodes.entity_base.__repr__


class comment(tree.comment):
    type = 6
    value = tree.text.xml_value
    def __init__(self, data):
        #tree.comment.__init__(self, data)
        tree.comment.__init__(self)
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

def doctype_create(dummy, name, publicId=None, systemId=None):
    c = comment(u'')
    c.xml_public_id = publicId
    c.xml_system_id = systemId
    c.xml_name = name
    return c


BOGUS_NAMESPACE = u'urn:bogus:x'

class treebuilder(html5lib.treebuilders._base.TreeBuilder):
    documentClass = entity
    #elementClass = xml_element_factory
    commentClass = comment
    doctypeClass = doctype_create
    
    def __init__(self, entity_factory=None, ns_aware=False):
        self.entity = entity_factory()
        html5lib.treebuilders._base.TreeBuilder.__init__(self, ns_aware)
        def eclass(name, namespace):
            namespace, name = (U(namespace) if namespace else None), U(name)
            #Deal with some broken HTML that uses bogus colons in tag names
            if (u":" in name and not namespace):
                namespace = BOGUS_NAMESPACE
            #Yes! Amara ns, name convention this is reverse order from html5lib's
            return self.entity.xml_element_factory(namespace, name)
        self.elementClass = eclass


def parse(source, model=None, encoding=None):
    '''
    
    '''
    #from amara.bindery import html; doc = html.parse("http://www.hitimewine.net/istar.asp?a=6&id=161153!1247")
    #parser = html5lib.HTMLParser()
    def get_tree_instance(ns_aware=False):
        #ns_aware is a boolean, whether or not to use http://www.w3.org/1999/xhtml
        entity_factory = model.clone if model else entity
        return treebuilder(entity_factory, ns_aware)
    parser = html5lib.HTMLParser(tree=get_tree_instance)
    return parser.parse(inputsource(source, None).stream, encoding=encoding)
    #return parser.parse(inputsource(source, None).stream, model)


def markup_fragment(source):
    '''
    Parse a fragment if markup in HTML mode, and return a bindery node
    
    You might want to wrap source with amara.lib.inputsource.text if it's not obviously XML or HTML
    
    from amara.lib import inputsource
    from amara.bindery import html
    doc = html.markup_fragment(inputsource.text('XXX<html><body onload="" color="white"><p>Spam!<p>Eggs!</body></html>YYY'))
    
    See also: http://wiki.xml3k.org/Amara2/Tagsoup
    '''
    doc = html.parse(source)
    frag = doc.html.body
    return frag


def launch(source, **kwargs):
    doc = parse(source)
    if 'pretty' in kwargs:
        doc.xml_write('xml-indent')
    else:
        doc.xml_write()
    return


#Ideas borrowed from
# http://www.artima.com/forums/flat.jsp?forum=106&thread=4829

#FIXME: A lot of this is copied boilerplate that neds to be cleaned up
import sys

def command_line_prep():
    from optparse import OptionParser
    usage = "Amara 2.x.  Command line support for parsing HTML, even tag soup.\n"
    usage += "python -m 'amara.bindery.html' [options] source cmd"
    parser = OptionParser(usage=usage)
    parser.add_option("-p", "--pretty",
                      action="store_true", dest="pretty", default=False,
                      help="Pretty-print the XML output")
    parser.add_option("-H", "--html",
                      action="store_true", dest="html", default=False,
                      help="Output (cleaned-up) HTML rather than XML")
    return parser


def main(argv=None):
    #But with better integration of entry points
    if argv is None:
        argv = sys.argv
    # By default, optparse usage errors are terminated by SystemExit
    try:
        optparser = command_line_prep()
        options, args = optparser.parse_args(argv[1:])
        # Process mandatory arguments with IndexError try...except blocks
        try:
            source = args[0]
        except IndexError:
            optparser.error("Missing source for HTML")
        #try:
        #    xpattern = args[1]
        #except IndexError:
        #    optparser.error("Missing main xpattern")
    except SystemExit, status:
        return status

    # Perform additional setup work here before dispatching to run()
    # Detectable errors encountered here should be handled and a status
    # code of 1 should be returned. Note, this would be the default code
    # for a SystemExit exception with a string message.

    pretty = options.pretty
    html = options.html
    if source == '-':
        source = sys.stdin
    launch(source, pretty=pretty, html=html)
    return


if __name__ == "__main__":
    sys.exit(main(sys.argv))

