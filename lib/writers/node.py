"""amara.writers.node

Internal module containing the logic for traversing an Amara tree in order to
serialize it.

"""

from amara import tree
from amara.namespaces import XML_NAMESPACE, XMLNS_NAMESPACE

class _Visitor:
    """
    Provides functions to recursively walk a DOM or Domlette object and
    generate SAX-like event calls for each node encountered. See the
    printer classes (XMLPrinter, HTMLPrinter, etc.) for the event
    handlers.
    """
    def __init__(self, printer,
                 ns_hints=None, 
                 added_attributes=None):
        """
        Initializes an instance of the class.
        ns_hints, if given, is a dictionary of namespace mappings that
        help determine if namespace declarations need to be emitted when
        visiting the first Element node.
        """
        self.printer = printer

        # Namespaces
        self._namespaces = [{'xml' : XML_NAMESPACE}]
        self._ns_hints = ns_hints
        self._added_attributes = added_attributes or {}

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

    def visit_not_implemented(self, node):
        """
        Called when an known but unsupported type of node is
        encountered, always raising a NotImplementedError exception. The
        unsupported node types are those that require DTD subset
        support: entity nodes, entity reference nodes, and notation
        nodes.
        """
        raise NotImplementedError('Printing of %r' % node)

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

        for child in node.xml_children:
            self.visit(child)
        self.printer.end_document()
        return
    _dispatch[tree.entity.xml_type] = visit_document

    def visit_element(self, node):
        """
        Called when an Element node is encountered. Generates for the
        printer a startElement event, events for the node's children
        (including attributes), and an endElement event.
        """
        ##print "visit_element", node.xml_name
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

        self.printer.start_element(node.xml_namespace, node.xml_qname, namespaces.iteritems(),
                                 attributes.iteritems())

        # Update in scope namespaces with those we emitted
        current_nss.update(namespaces)
        self._namespaces.append(current_nss)

        # Write out this node's children
        for child in node.xml_children:
            self.visit(child)

        self.printer.end_element(node.xml_namespace, node.xml_qname)

        del self._namespaces[-1]
    _dispatch[tree.element.xml_type] = visit_element

    def visit_text(self, node):
        """
        Called when a Text node is encountered. Generates a text event
        for the printer.
        """
        self.printer.text(node.xml_value)
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
