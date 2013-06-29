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

from amara.thirdparty import html5lib
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
        raise NotImplementedError

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
    #name = nodes.element_base.xml_qname
    #namespace = nodes.element_base.xml_namespace
    xml_exclude_pnames = frozenset(('name', 'parent', 'appendChild', 'removeChild', 'removeChild', 'value', 'attributes', 'childNodes'))
    @property
    def name(self):
        return getattr(self, 'xml_html5lib_name', self.xml_qname)

    @property
    def namespace(self):
        return getattr(self, 'xml_html5lib_namespace', self.xml_namespace)

    @property
    def nameTuple(self):
        name = getattr(self, 'xml_html5lib_name', self.xml_qname)
        namespace = getattr(self, 'xml_html5lib_namespace', self.xml_namespace)
        return namespace, name
        #return XHTML_NAMESPACE, self.xml_name

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

    def cloneNode(self):
        """Return a shallow copy of the current node i.e. a node with the same
        name and attributes but with no parent or child nodes
        """
        newelem = self.xml_root.xml_element_factory(self.xml_namespace, self.xml_local)
        for k, v in self.xml_attributes.items():
            newelem.xml_attributes[k] = v
        return newelem


class entity(node, nodes.entity_base):
    """
    Base class for entity nodes (root nodes--similar to DOM documents and document fragments)
    """
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
NAME_FOR_ELEMENTS_UNNAMED_BY_HTML5LIB = u'UNNAMED_BY_HTML5LIB'

class treebuilder_pre_0_90(html5lib.treebuilders._base.TreeBuilder):
    documentClass = entity
    #elementClass = xml_element_factory
    commentClass = comment
    doctypeClass = doctype_create
    
    def __init__(self, entity_factory=None):
        self.entity = entity_factory()
        html5lib.treebuilders._base.TreeBuilder.__init__(self)
        def eclass(name):
            if not name: name = NAME_FOR_ELEMENTS_UNNAMED_BY_HTML5LIB
            namespace, name = None, U(name)
            #Deal with some broken HTML that uses bogus colons in tag names
            if (u":" in name and not namespace):
                namespace = BOGUS_NAMESPACE
            return self.entity.xml_element_factory(namespace, name)
        self.elementClass = eclass


MARKER = object()

class treebuilder(html5lib.treebuilders._base.TreeBuilder):
    documentClass = entity
    #elementClass = xml_element_factory
    commentClass = comment
    doctypeClass = doctype_create
    
    def __init__(self, entity_factory=None, use_xhtml_ns=False):
        self.entity = entity_factory()
        #html5lib.treebuilders._base.TreeBuilder breaks if you do not pass in True for namespaceHTMLElements
        #We'll take care of that ourselves with the if not use_xhtml_ns... below
        html5lib.treebuilders._base.TreeBuilder.__init__(self, True)
        def eclass(name, namespace):
            xml_html5lib_name, xml_html5lib_namespace = MARKER, MARKER
            if not use_xhtml_ns and namespace == XHTML_NAMESPACE:
                #html5lib feints support for HTML5 elements kept in the null namespace
                #But in reality this support is broken.  We have to in effect keep
                #Two namespaces for each element, the real one from an amara perspective
                #And another that is always XHTML for HTML5 elements, so html5lib doesn't break
                xml_html5lib_namespace = namespace
                namespace = None
            #For some reason html5lib sometimes sends None as name
            if not name:
                xml_html5lib_name = name
                name = NAME_FOR_ELEMENTS_UNNAMED_BY_HTML5LIB
            namespace, name = U(namespace) if namespace else None, U(name)
            #import sys; print >> sys.stderr, (namespace, name, use_xhtml_ns)
            #Deal with some broken HTML that uses bogus colons in tag names
            if (u":" in name and not namespace):
                xml_html5lib_namespace = namespace
                namespace = BOGUS_NAMESPACE
            #Yes! Amara ns, name convention this is reverse order from html5lib's
            elem = self.entity.xml_element_factory(namespace, name)
            if xml_html5lib_namespace != MARKER:
                elem.xml_html5lib_namespace = xml_html5lib_namespace
            if xml_html5lib_name != MARKER:
                elem.xml_html5lib_name = xml_html5lib_name
            return elem
        self.elementClass = eclass


def parse(source, prefixes=None, model=None, encoding=None, use_xhtml_ns=False):
    '''
    Parse an input source with HTML text into an Amara Bindery tree

    Warning: if you pass a string, you must make sure it's a byte string, not a Unicode object.  You might also want to wrap it with amara.lib.inputsource.text if it's not obviously XML or HTML (for example it could be confused with a file name)
    '''
    from amara.lib.util import set_namespaces
    #from amara.bindery import html; doc = html.parse("http://www.hitimewine.net/istar.asp?a=6&id=161153!1247")
    #parser = html5lib.HTMLParser()
    if PRE_0_90:
        def get_tree_instance():
            entity_factory = model.clone if model else entity
            return treebuilder(entity_factory)
    else:
        def get_tree_instance(namespaceHTMLElements, use_xhtml_ns=use_xhtml_ns):
            #use_xhtml_ns is a boolean, whether or not to use http://www.w3.org/1999/xhtml
            entity_factory = model.clone if model else entity
            return treebuilder(entity_factory, use_xhtml_ns)
    parser = html5lib.HTMLParser(tree=get_tree_instance)
    doc = parser.parse(inputsource(source, None).stream, encoding=encoding)
    if prefixes: set_namespaces(doc, prefixes)
    return doc
    #return parser.parse(inputsource(source, None).stream, model)


def markup_fragment(source, encoding=None):
    '''
    Parse a fragment if markup in HTML mode, and return a bindery node
    
    Warning: if you pass a string, you must make sure it's a byte string, not a Unicode object.  You might also want to wrap it with amara.lib.inputsource.text if it's not obviously XML or HTML (for example it could be confused with a file name)
    
    from amara.lib import inputsource
    from amara.bindery import html
    doc = html.markup_fragment(inputsource.text('XXX<html><body onload="" color="white"><p>Spam!<p>Eggs!</body></html>YYY'))
    
    See also: http://wiki.xml3k.org/Amara2/Tagsoup
    '''
    doc = parse(source, encoding=encoding)
    frag = doc.html.body
    return frag


try:
    HTML5LIB_VERSION = html5lib.__version__
    PRE_0_90 = False
except AttributeError:
    #0.11.1 and earlier do not seem to have __version__
    #Note later versions seem to have a broken __version__
    #This logic is really there for when they fix that
    HTML5LIB_VERSION = 'PRE_0.90'
    PRE_0_90 = True
    treebuilder = treebuilder_pre_0_90


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

