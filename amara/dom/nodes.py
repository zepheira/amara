########################################################################
# amara/dom/nodes.py

"""
Amara DOM node implementations
"""

from xml.dom import Node as stdlib_node
from xml.dom import EMPTY_NAMESPACE, XML_NAMESPACE
from xml.dom import NoModificationAllowedErr, NamespaceErr, NotFoundErr
from xml.dom import NotSupportedErr, HierarchyRequestErr, WrongDocumentErr
from xml.dom import InvalidCharacterErr#, UnspecifiedEventTypeErr

from functools import *
from amara.lib.xmlstring import *
from amara import tree
import sets
import itertools
import warnings


class Node(object):
    nodeValue = None
    nodeName = None
    attributes = None
    readOnly = False
    childNodes = []
    firstChild = None
    lastChild = None
    previousSibling = None
    nextSibling = None
    _ownerDocument = None

    def _set_ownerdoc(self, owner):
        self._ownerDocument = owner

    @property
    def ownerDocument(self): return self._ownerDocument
    @property
    def localName(self): return self.xml_local
    @property
    def namespaceURI(self): return self.xml_namespace
    @property
    def prefix(self): return self.xml_prefix
    @property
    def nodeType(self): return self.xml_node_type
    #@property
    #def ownerDocument(self):
    #    result = self.xml_select(u'/')
    #    return result[0] if result else None
    @property
    def parentNode(self): return self.xml_parent
    #def normalize(self): return self.xml_normalize()
    #def isSupported(self)
    def isSameNode(self, other): return self is other
    #def isSupported(self)
    def cloneNode(self, deep=False): return copy.deepcopy(self) if deep else copy.copy(self)

    def hasChildNodes(self): return False
    #Don't just assign the functions since there are subtle differences we'll need to fix up
    def appendChild(self, newChild):
        raise HierarchyRequestErr("%s does not support child node operations" % (repr(self)))
    def replaceChild(self, newChild, oldChild):
        raise HierarchyRequestErr("%s does not support child node operations" % (repr(self)))
    def removeChild(self, node):
        raise HierarchyRequestErr("%s does not support child node operations" % (repr(self)))
    def appendChild(self, node):
        raise HierarchyRequestErr("%s does not support child node operations" % (repr(self)))

    def isSupported(self, feature, version):
        return self.ownerDocument.implementation.hasFeature(feature, version)
    def getInterface(self, feature):
        if self.isSupported(feature, None):
            return self
        else:
            return None


class _container(Node):
    @property
    def childNodes(self): return self.xml_children
    @property
    def firstChild(self): return self.xml_first_child
    @property
    def lastChild(self): return self.xml_last_child
    @property
    def previousSibling(self): return self.xml_preceding_sibling
    @property
    def nextSibling(self): return self.xml_following_sibling

    def hasChildNodes(self): return bool(self.xml_children)
    #Don't just assign the functions since there are subtle differences we'll need to fix up
    def appendChild(self, node): return self.xml_append(node)
    def replaceChild(self, newChild, oldChild): return self.xml_replace(oldChild, newChild)
    def removeChild(self, node): return self.xml_remove(node)
    def insertBefore(self, newChild, refNode):
        index = self.xml_index(refChild)
        return self.xml_insert(index, newChild)
    def getElementsByTagNameNS(self, namespaceURI, localName): return ( e for e in self.xml_select(u'//*') if (e.xml_namespace, e.xml_local) == (namespaceURI, localName))


class DocumentFragment(_container, tree.entity):
    nodeType = stdlib_node.DOCUMENT_FRAGMENT_NODE
    nodeName = "#document-fragment"


class ProcessingInstruction(Node, tree.processing_instruction):
    @property
    def nodeName(self): return self.xml_target
    @property
    def target(self): return self.xml_target
    @property
    def data(self): return self.xml_data


class Attr(Node, tree.attribute):
    specified = False
    @property
    def nodeName(self): return self.xml_qname


class Element(_container, tree.element):
    def xml_attribute_factory(self, ns, local, value=u''):
        node = Attr(ns, local, value)
        node._set_ownerdoc(self)
        return node

    @property
    def nodeName(self): return self.xml_qname
    tagName = nodeName
    def hasAttributeNS(self, namespaceURI, localName): return bool(self.xml_attributes.get(namespaceURI, localName))
    def hasAttributes(self): return bool(self.xml_attributes)
    def getAttributeNS(self, namespaceURI, localName):
        return self.xml_attributes.get((namespaceURI, localName))
    def setAttributeNS(self, namespaceURI, localName, value): self.xml_attributes[namespaceURI, localName] = value
    def removeAttributeNS(self, namespaceURI, localName): del self.xml_attributes[namespaceURI, localName]
    def getAttributeNodeNS(self, namespaceURI, localName): return self.xml_attributes.get(namespaceURI, localName)
    def setAttributeNodeNS(self, node): self.xml_attributes[node.xml_namespace, node.xml_local] = node
    def removeAttributeNodeNS(self, node): del self.xml_attributes[node.xml_namespace, node.xml_local]


class CharacterData(Node):
    @property
    def nodeValue(self): return self.xml_value
    data = nodeValue

    def __repr__(self):
        MAXREPR = 10
        data = self.data
        if len(data) > MAXREPR:
            dotdotdot = "..."
        else:
            dotdotdot = ""
        return "<Amara DOM %s node \"%s%s\">" % (
            self.__class__.__name__, data[0:MAXREPR], dotdotdot)

    def substringData(self, offset, count):
        if offset < 0:
            raise IndexSizeErr("offset cannot be negative")
        if offset > len(self.xml_value):
            raise IndexSizeErr("offset cannot be beyond end of data")
        if count < 0:
            raise IndexSizeErr("count cannot be negative")
        return self.xml_value[offset:offset+count]

    def appendData(self, more):
        self.xml_value += more

    def insertData(self, offset, more):
        if offset < 0:
            raise IndexSizeErr("offset cannot be negative")
        if offset > len(self.xml_value):
            raise IndexSizeErr("offset cannot be beyond end of data")
        if more:
            self.xml_value = "%s%s%s" % (
                self.xml_value[:offset], more, self.xml_value[offset:])

    def deleteData(self, offset, count):
        if offset < 0:
            raise IndexSizeErr("offset cannot be negative")
        if offset > len(self.data):
            raise IndexSizeErr("offset cannot be beyond end of data")
        if count < 0:
            raise IndexSizeErr("count cannot be negative")
        if count:
            self.xml_value = self.xml_value[:offset] + self.xml_value[offset+count:]

    def replaceData(self, offset, count, repl):
        if offset < 0:
            raise IndexSizeErr("offset cannot be negative")
        if offset > len(self.xml_value):
            raise IndexSizeErr("offset cannot be beyond end of data")
        if count < 0:
            raise IndexSizeErr("count cannot be negative")
        if count:
            self.xml_value = "%s%s%s" % (
                self.xml_value[:offset], repl, self.xml_value[offset+count:])


class Text(CharacterData, tree.text):
    nodeName = "#text"


class Comment(CharacterData, tree.comment):
    nodeName = "#comment"


class CDATASection(Text):
    nodeType = stdlib_node.CDATA_SECTION_NODE
    nodeName = "#cdata-section"


class DocumentType(Node, tree.node):
    nodeType = stdlib_node.DOCUMENT_TYPE_NODE
    name = None
    publicId = None
    systemId = None
    internalSubset = None

    def __init__(self, qualifiedName):
        self.entities = NamedNodeMap() #Note, technically should be read-only NNN that preserves order (see minidom.ReadOnlySequentialNamedNodeMap)
        self.notations = NamedNodeMap()
        if qualifiedName:
            prefix, localname = splitqname(qualifiedName)
            self.name = localname
        self.nodeName = self.name


class Entity(Node, tree.node):
    attributes = None
    nodeType = stdlib_node.ENTITY_NODE
    nodeValue = None

    actualEncoding = None
    encoding = None
    version = None

    def __init__(self, name, publicId, systemId, notation):
        self.nodeName = name
        self.notationName = notation


class Notation(Node, tree.node):
    nodeType = stdlib_node.NOTATION_NODE
    nodeValue = None


class DOMImplementation(object):
    _features = [("core", "1.0"),
                 ("core", "2.0"),
                 ("core", "3.0"),
                 ("core", None),
                 ("xml", "1.0"),
                 ("xml", "2.0"),
                 ("xml", "3.0"),
                 ("xml", None),
                 ("ls-load", "3.0"),
                 ("ls-load", None),
                 ]

    def hasFeature(self, feature, version):
        if version == "":
            version = None
        return (feature.lower(), version) in self._features

    def createDocument(self, namespaceURI, qualifiedName, doctype):
        if doctype and doctype.xml_parent is not None:
            raise WrongDocumentErr(
                "doctype object owned by another DOM tree")
        doc = Document()

        add_root_element = not (namespaceURI is None
                                and qualifiedName is None
                                and doctype is None)

        if not qualifiedName and add_root_element:
            # The spec is unclear what to raise here; SyntaxErr
            # would be the other obvious candidate. Since Xerces raises
            # InvalidCharacterErr, and since SyntaxErr is not listed
            # for createDocument, that seems to be the better choice.
            # XXX: need to check for illegal characters here and in
            # createElement.

            # DOM Level III clears this up when talking about the return value
            # of this function.  If namespaceURI, qName and DocType are
            # Null the document is returned without a document element
            # Otherwise if doctype or namespaceURI are not None
            # Then we go back to the above problem
            raise InvalidCharacterErr("Element with no name")

        if add_root_element:
            prefix, localname = splitqname(qualifiedName)
            if prefix == "xml" \
               and namespaceURI != "http://www.w3.org/XML/1998/namespace":
                raise NamespaceErr("illegal use of 'xml' prefix")
            if prefix and not namespaceURI:
                raise NamespaceErr(
                    "illegal use of prefix without namespaces")
            element = doc.createElementNS(namespaceURI, qualifiedName)
            if doctype:
                doc.appendChild(doctype)
            doc.appendChild(element)

        if doctype:
            doctype.parentNode = doctype.ownerDocument = doc

        doc.doctype = doctype
        doc.implementation = self
        return doc

    def createDocumentType(self, qualifiedName, publicId, systemId):
        doctype = DocumentType(qualifiedName)
        doctype.publicId = publicId
        doctype.systemId = systemId
        return doctype

    def getInterface(self, feature):
        if self.hasFeature(feature, None):
            return self
        else:
            return None


class Document(_container, tree.entity):
    _child_node_types = (stdlib_node.ELEMENT_NODE, stdlib_node.PROCESSING_INSTRUCTION_NODE,
                         stdlib_node.COMMENT_NODE, stdlib_node.DOCUMENT_TYPE_NODE)

    nodeType = stdlib_node.DOCUMENT_NODE
    nodeName = "#document"
    doctype = None
    parentNode = None
    implementation = DOMImplementation()
    actualEncoding = None
    encoding = None
    standalone = None
    version = None
    strictErrorChecking = False
    errorHandler = None
    documentURI = None

    def xml_comment_factory(self, data):
        node = Comment(data)
        node._set_ownerdoc(self)
        return node

    def xml_processing_instruction_factory(self, target, data):
        node = ProcessingInstruction(target, data)
        node._set_ownerdoc(self)
        return node

    def xml_text_factory(self, data):
        node = Text(data)
        node._set_ownerdoc(self)
        return node

    def xml_element_factory(self, ns, local):
        node = Element(ns, local)
        node._set_ownerdoc(self)
        return node

    def createDocumentFragment(self):
        d = DocumentFragment()
        d.ownerDocument = self
        return d

    def createElement(self, tagName):
        e = Element(tagName)
        e.ownerDocument = self
        return e

    def createTextNode(self, data):
        if not isinstance(data, basestring):
            raise TypeError, "node contents must be a string"
        t = Text()
        t.data = data
        t.ownerDocument = self
        return t

    def createCDATASection(self, data):
        if not isinstance(data, basestring):
            raise TypeError, "node contents must be a string"
        c = CDATASection()
        c.data = data
        c.ownerDocument = self
        return c

    def createComment(self, data):
        c = Comment(data)
        c.ownerDocument = self
        return c

    def createProcessingInstruction(self, target, data):
        p = ProcessingInstruction(target, data)
        p.ownerDocument = self
        return p

    def createAttribute(self, qName):
        a = Attr(qName)
        a.ownerDocument = self
        a.xml_value = ""
        return a

    def createElementNS(self, namespaceURI, qualifiedName):
        prefix, localName = splitqname(qualifiedName)
        e = Element(qualifiedName, namespaceURI, prefix)
        e.ownerDocument = self
        return e

    def createAttributeNS(self, namespaceURI, qualifiedName):
        prefix, localName = splitqname(qualifiedName)
        a = Attr(qualifiedName, namespaceURI, localName, prefix)
        a.ownerDocument = self
        a.xml_value = ""
        return a

    # A couple of implementation-specific helpers to create node types
    # not supported by the W3C DOM specs:

    def _create_entity(self, name, publicId, systemId, notationName):
        e = Entity(name, publicId, systemId, notationName)
        e.ownerDocument = self
        return e

    def _create_notation(self, name, publicId, systemId):
        n = Notation(name, publicId, systemId)
        n.ownerDocument = self
        return n

    @property
    def documentElement(self):
        child_elements = [ ch for ch in self.xml_children if isinstance(ch, tree.element) ]
        return child_elements[0] if child_elements else None

    def importNode(self, node, deep):
        if node.nodeType == stdlib_node.DOCUMENT_NODE:
            raise NotSupportedErr("cannot import document nodes")
        elif node.nodeType == stdlib_node.DOCUMENT_TYPE_NODE:
            raise NotSupportedErr("cannot import document type nodes")
        new_tree = self.cloneNode(deep)
        def set_owner(node):
            node.ownerDocument = self
            for child in node.xml_children:
                set_owner(child)
            if isinstance(node, tree.element):
                for attr in node.xml_attributes:
                    set_owner(attr)
        return new_tree


def getDOMImplementation(features=None):
    if features:
        if isinstance(features, StringTypes):
            features = domreg._parse_feature_string(features)
        for f, v in features:
            if not Document.implementation.hasFeature(f, v):
                return None
    return Document.implementation

