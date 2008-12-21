########################################################################
# amara/writers/treevisitor.py

"""
This module supports document serialization in XML or HTML syntax.
"""

import sys
from xml.dom import Node
from amara import tree
from amara.namespaces import XML_NAMESPACE, XMLNS_NAMESPACE
#import amara.writers.xmlwriter
#import XmlPrinter, XmlPrettyPrinter, HtmlPrinter, HtmlPrettyPrinter
import _xmlprinters, _htmlprinters

class visitor:
    """
    Provides functions to recursively walk a DOM or Domlette object and
    generate SAX-like event calls for each node encountered. See the
    printer classes (XMLPrinter, HTMLPrinter, etc.) for the event
    handlers.
    """
    def __init__(self, stream=sys.stdout, encoding='utf-8', printer=None, ns_hints=None, is_html=False,
                 indent=False, canonical=False, added_attributes=None,
                 removed_ns_decls=None):
        """
        Initializes an instance of the class, selecting the appropriate
        printer to use, depending on the isHtml and indent flags.
        ns_hints, if given, is a dictionary of namespace mappings that
        help determine if namespace declarations need to be emitted when
        visiting the first Element node.
        """
        if printer:
            self.printer = printer
        elif indent and is_html:
            self.printer = _htmlprinters.htmlprettyprinter(stream, encoding)
        elif indent:
            self.printer = _xmlprinters.xmlprettyprinter(stream, encoding)
        elif is_html:
            self.printer = _htmlprinters.htmlprinters(stream, encoding)
        elif canonical:
            self.printer = _xmlprinters.CanonicalXmlPrinter(stream, encoding)
        else:
            self.printer = _xmlprinters.xmlprinter(stream, encoding)

        # Namespaces
        self._namespaces = [{'xml' : XML_NAMESPACE}]
        self._ns_hints = ns_hints
        self._added_attributes = added_attributes or {}
        self._removed_ns_decls = removed_ns_decls or []
        return

    _dispatch = {}
    def visit(self, node):
        """
        Starts walking the tree at the given node.
        """
        try:
            node_type = node.xml_type
        except AttributeError:
            raise ValueError('Not a valid Amara node %r' % node)

        try:
            visit = self._dispatch[node_type]
        except KeyError:
            # unknown node type, try and get a "pretty" name for the error
            #FIXME: Not ported for Amara 2
            node_types = {}
            for name in dir(Node):
                if name.endswith('_NODE'):
                    node_types[getattr(Node, name)] = name
            node_type = node_types.get(node.node_type, node.node_type)
            raise ValueError('Unknown node type %r' % node_type)
        else:
            visit(self, node)
        return

    def visit_not_implemented(self, node):
        """
        Called when an known but unsupported type of node is
        encountered, always raising a NotImplementedError exception. The
        unsupported node types are those that require DTD subset
        support: entity nodes, entity reference nodes, and notation
        nodes.
        """
        raise NotImplementedError('Printing of %r' % node)
    #_dispatch[tree.entity.xml_type] = visitNotImplemented
    #_dispatch[tree.entity.xml_type] = visitNotImplemented

    def visit_document(self, node):
        """
        Called when an Entity node is encountered (e.g. may or may not be a full XML document entity).
        Work on DTDecl details, if any, and then to the children.
        """
        self.printer.start_document()
        if node.xml_system_id:
            for child in node.xml_children:
                if child.xml_type == tree.element.xml_type:
                    self.printer.doctype(child.xml_qname, node.xml_public_id, node.xml_system_id)
                    break
        #hasDocTypeNode = False
        #if hasattr(node, 'doctype'):
            # DOM Level 1/2/3
        #    if node.doctype:
        #        hasDocTypeNode = True
        #        self.visitDocumentType(node.doctype)
        #    children = [ x for x in node.childNodes if x != node.doctype ]
        #if not hasDocTypeNode and hasattr(node, 'systemId'):
            # Domlette
        #    if node.documentElement:
        #        self.printer.doctype(node.documentElement.tagName,
        #                            node.publicId, node.systemId)
        #    children = node.childNodes

        for child in node.xml_children:
            self.visit(child)
        return
    _dispatch[tree.entity.xml_type] = visit_document

    #def visit_document_type(self, node):
    #    """
    #    Called when a DocumentType node is encountered. Generates a
    #    doctype event for the printer.
    #    """
    #    self.printer.doctype(node.name, node.publicId,
    #                        node.systemId)
    #    return
    #_dispatch[Node.DOCUMENT_TYPE_NODE] = visitDocumentType

    def visit_element(self, node):
        """
        Called when an Element node is encountered. Generates for the
        printer a startElement event, events for the node's children
        (including attributes), and an endElement event.
        """
        #print "visit_element", node.xml_name
        current_nss = self._namespaces[-1].copy()
        # Gather the namespaces and attributes for writing
        namespaces = node.xml_namespaces.copy()
        del namespaces[u'xml']

        if self._ns_hints:
            for prefix, namespaceUri in self._ns_hints.items():
                # See if this namespace needs to be emitted
                if current_nss.get(prefix, 0) != namespaceUri:
                    namespaces[prefix or u''] = namespaceUri
            self._ns_hints = None

        if self._added_attributes:
            attributes = self._added_attributes
            self._added_attributes = None
        else:
            attributes = {}

        for attr in node.xml_attributes.nodes():
            # xmlns="uri" or xmlns:foo="uri"
            if attr.xml_namespace == XMLNS_NAMESPACE:
                if not attr.xml_prefix:
                    # xmlns="uri"
                    prefix = None
                else:
                    # xmlns:foo="uri"
                    prefix = attr.xml_local
                if current_nss.get(prefix, 0) != attr.xml_value:
                    namespaces[prefix] = attr.xml_value
            else:
                attributes[attr.xml_qname] = attr.xml_value

        # The element's namespaceURI/prefix mapping takes precedence
        #if node.xml_namespace or current_nss.get(u'', 0):
            #if current_nss.get(node.xml_prefix or u'', 0) != node.xml_namespace:
            #    namespaces[node.xml_prefix or u''] = node.xml_namespace or u""
        if node.xml_namespace or namespaces.get(None, 0):
            if namespaces.get(node.xml_prefix or None, 0) != node.xml_namespace:
                namespaces[node.xml_prefix or None] = node.xml_namespace or u""

        #The 
        kill_prefixes = []
        for prefix in namespaces:
            if prefix in current_nss and current_nss[prefix] == namespaces[prefix]:
                kill_prefixes.append(prefix)

        for prefix in kill_prefixes:
            del namespaces[prefix]

        for prefix in self._removed_ns_decls:
            del namespaces[prefix]

        self.printer.start_element(node.xml_namespace, node.xml_qname, namespaces.iteritems(),
                                 attributes.iteritems())
        if self._removed_ns_decls:
            self._removed_ns_decls = []

        # Update in scope namespaces with those we emitted
        current_nss.update(namespaces)
        self._namespaces.append(current_nss)

        # Write out this node's children
        for child in node.xml_children:
            self.visit(child)

        self.printer.end_element(node.xml_namespace, node.xml_qname)

        del self._namespaces[-1]
        return
    _dispatch[tree.element.xml_type] = visit_element

    def visit_text(self, node):
        """
        Called when a Text node is encountered. Generates a text event
        for the printer.
        """
        self.printer.text(node.xml_value)
        return
    _dispatch[tree.text.xml_type] = visit_text

    def visit_comment(self, node):
        """
        Called when a Comment node is encountered. Generates a comment
        event for the printer.
        """
        self.printer.comment(node.xml_value)
        return
    _dispatch[tree.comment.xml_type] = visit_comment

    def visit_processing_instruction(self, node):
        """
        Called when a ProcessingInstruction node is encountered.
        Generates a processingInstruction event for the printer.
        """
        self.printer.processing_instruction(node.xml_target, node.xml_data)
        return
    _dispatch[tree.processing_instruction.xml_type] = visit_processing_instruction


def xml_print(root, stream=sys.stdout, encoding='UTF-8', **kwargs):
    """
    Given a Node instance assumed to be the root of a DOM or Domlette
    tree, this function serializes the document to the given stream or
    stdout, using the given encoding (UTF-8 is the default). The asHtml
    flag can be used to force HTML-style serialization of an XML DOM.
    Otherwise, the DOM type (HTML or XML) is automatically determined.
    This function does nothing if root is not a Node.

    It is preferable that users import this from Ft.Xml.Domlette
    rather than directly from Ft.Xml.Lib.
    """
    #if not hasattr(root, "nodeType"):
    #    return
    #ns_hints = SeekNss(root)
    ns_hints = {}
    # When as_html is not specified, choose output method from interface
    # of document node (getElementsByName is an HTML DOM only method)
    #if as_html is None:
    #    as_html = hasattr(root.ownerDocument or root, 'getElementsByName')
    v = visitor(stream, encoding, **kwargs)
    v.visit(root)
    return


def PrettyPrint(root, stream=sys.stdout, encoding='UTF-8', asHtml=None):
    """
    Given a Node instance assumed to be the root of a DOM or Domlette
    tree, this function serializes the document to the given stream or
    stdout, using the given encoding (UTF-8 is the default). Extra
    whitespace is added to the output for visual formatting. The asHtml
    flag can be used to force HTML-style serialization of an XML DOM.
    Otherwise, the DOM type (HTML or XML) is automatically determined.
    This function does nothing if root is not a Node.

    Please import this from Ft.Xml.Domlette
    rather than directly from Ft.Xml.Lib.
    """
    from Ft.Xml.Domlette import SeekNss
    if not hasattr(root, "nodeType"):
        return
    ns_hints = SeekNss(root)
    # When asHtml is not specified, choose output method from interface
    # of document node (getElementsByName is an HTML DOM only method)
    if asHtml is None:
        asHtml = hasattr(root.ownerDocument or root, 'getElementsByName')
    visitor = PrintVisitor(stream, encoding, ns_hints, asHtml, 1)
    visitor.visit(root)
    stream.write('\n')
    return


def CanonicalPrint(root, stream=sys.stdout, exclusive=False,
                   inclusivePrefixes=None):
    """
    Given a Node instance assumed to be the root of an XML DOM or Domlette
    tree, this function serializes the document to the given stream or
    stdout, using c14n serialization, according to
    http://www.w3.org/TR/xml-c14n (the default) or
    http://www.w3.org/TR/xml-exc-c14n/
    This function does nothing if root is not a Node.

    exclusive - if true, apply exclusive c14n according to
        http://www.w3.org/TR/xml-exc-c14n/
    inclusivePrefixes - if exclusive is True, use this as a list of namespaces
        representing the "InclusiveNamespacesPrefixList" list in exclusive c14n

    Please import this from Ft.Xml.Domlette
    rather than directly from Ft.Xml.Lib.
    """
    from Ft.Xml.Domlette import SeekNss
    if not hasattr(root, "nodeType"):
        return
    added_attributes = {}  #All the contents should be XML NS attrs
    nshints = {}
    if not exclusive:
        #Roll in ancestral xml:* attributes
        parent_xml_attrs = root.xpath(u'ancestor::*/@xml:*')
        for attr in parent_xml_attrs:
            aname = (attr.namespaceURI, attr.nodeName)
            if (aname not in added_attributes
                and aname not in root.attributes):
                added_attributes[attr.nodeName] = attr.value
    nsnodes = root.xpath('namespace::*')
    inclusivePrefixes = inclusivePrefixes or []
    if u'#default' in inclusivePrefixes:
        inclusivePrefixes.remove(u'#default')
        inclusivePrefixes.append(u'')
    decls_to_remove = []
    if exclusive:
        used_prefixes = [ node.prefix for node in root.xpath('self::*|@*') ]
        declared_prefixes = []
        for ans, anodename in root.attributes:
            if ans == XMLNS_NAMESPACE:
                attr = root.attributes[ans, anodename]
                prefix = attr.localName
                declared_prefixes.append(prefix)
                #print attr.prefix, attr.localName, attr.nodeName
                if attr.localName not in used_prefixes:
                    decls_to_remove.append(prefix)
        #for prefix in used_prefixes:
        #    if prefix not in declared_prefixes:
        #        nshints[ns.nodeName] = ns.value
    #Roll in ancestral  NS nodes
    for ns in nsnodes:
        prefix = ns.nodeName
        if (ns.value != XML_NAMESPACE
            and (XMLNS_NAMESPACE, ns.nodeName) not in root.attributes
            and (not exclusive or ns.localName in inclusivePrefixes)):
            #added_attributes[(XMLNS_NAMESPACE, ns.nodeName)] = ns.value
            nshints[prefix] = ns.value
        elif (exclusive
              and prefix in used_prefixes
              and prefix not in declared_prefixes):
            nshints[prefix] = ns.value
    visitor = PrintVisitor(stream, 'UTF-8', nshints, False,
                           0, True, added_attributes, decls_to_remove)
    visitor.visit(root)
    return

