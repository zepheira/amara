########################################################################
# amara/xslt/reader/__init__.py
"""
Classes for the creation of a stylesheet object
"""

import cStringIO
from xml.dom import Node
from xml.sax import SAXParseException
from xml.sax.handler import property_dom_node

from amara import sax
from amara.lib import IriError, inputsource
from amara.lib.xmlstring import isspace
from amara.namespaces import XML_NAMESPACE, XMLNS_NAMESPACE, XSL_NAMESPACE
from amara.xslt import XsltError, tree

#from amara.xslt import builtinextelements, exslt

import content_model, attribute_types

__all__ = ['stylesheet_reader']


# Whitespace stripping rules for a stylesheet:
#   preserve all whitespace within xsl:text elements;
#   strip whitespace from all other elements
STYLESHEET_WHITESPACE_RULES = [(XSL_NAMESPACE, 'text', False),
                               (None, '*', True)]


# pseudo-nodes for save/restore of variable bindings
class push_variables_node(tree.xslt_node):

    isPseudoNode = True

    def __init__(self, root, bindingStack):
        tree.xslt_node.__init__(self, root)
        self.savedVariables = bindingStack
        return

    def instantiate(self, context, processor):
        self.savedVariables.append(context.varBindings)
        context.varBindings = context.varBindings.copy()
        return

class pop_variables_node(tree.xslt_node):

    isPseudoNode = True

    def __init__(self, root, bindingStack):
        tree.xslt_node.__init__(self, root)
        self.savedVariables = bindingStack
        return

    def instantiate(self, context, processor):
        context.varBindings = self.savedVariables[-1]
        del self.savedVariables[-1]
        return


# The XSL attributes allowed on literal elements
RESULT_ELEMENT_XSL_ATTRS = {
    'exclude-result-prefixes' : attribute_types.prefixes(),
    'extension-element-prefixes' : attribute_types.prefixes(),
    'use-attribute-sets' : attribute_types.qnames(),
    'version' : attribute_types.number(),
    }
RESULT_ELEMENT_ATTR_INFO = attribute_types.any_avt()

# Cached values for stylesheet tree creation
_XSLT_ELEMENT_CACHE = {}
_root_content_model = content_model.alt(
    content_model.qname(XSL_NAMESPACE, 'xsl:stylesheet'),
    content_model.qname(XSL_NAMESPACE, 'xsl:transform'),
    content_model.result_elements)
_XSLT_ROOT_VALIDATION = _root_content_model.compile()
_LITERAL_ELEMENT_VALIDATION = content_model.template.compile()


class parse_state:
    """
    Stores the current state of the parser.

    Constructor arguments/instance variables:
      validation - validation state for the current containing node.

      localVariables - set of in-scope variable bindings to determine
                       variable shadowing.

      forwardsCompatible - flag indicating whether or not forwards-compatible
                           processing is enabled.

      currentNamespaces - set of in-scope namespaces for the current node.

      extensionNamespaces - set of namespaces defining extension elements

      outputNamespaces - set of in-scope namespaces for literal result elements
    """

    def __init__(self, node, validation, localVariables, forwardsCompatible,
                 currentNamespaces, extensionNamespaces, outputNamespaces):
        self.node = node
        self.validation = validation
        self.localVariables = localVariables
        self.forwardsCompatible = forwardsCompatible
        self.currentNamespaces = currentNamespaces
        self.extensionNamespaces = extensionNamespaces
        self.outputNamespaces = outputNamespaces
        return


class stylesheet_reader(object):
    """
    This class can be used to read, from a variety of sources, a
    stylesheet and all its included and imported stylesheets, building
    from them a single, compact representation of an XSLT stylesheet
    tree (an Ft.Xml.Xslt.Stylesheet.Stylesheet object).

    This is done with the most efficient parsing method available, and
    avoids creating a Domlette document for each document it reads.
    """

    # runtime instance variables
    _input_source = None
    _locator = None
    _stylesheet = None

    def __init__(self):
        self._import_index = 0
        self._global_vars = {}
        self._visited_stylesheet_uris = {}
        self._document_state_stack = []
        self._element_state_stack = []
        self._extelements = {}
        self._extelements.update(Exslt.ExtElements)
        self._extelements.update(BuiltInExtElements.ExtElements)
        self._extelement_cache = {}
        return

    def reset(self):
        self._root = None
        self._import_index = 0
        self._global_vars = {}
        self._visited_stylesheet_uris = {}
        self._document_state_stack = []
        self._element_state_stack = []
        return

    def addExtensionElementMapping(self, elementMapping):
        """
        Add a mapping of extension element names to classes to the
        existing mapping of extension elements.

        This should only be used for standalone uses of this class.  The
        only known standalone use for this class is for creating compiled
        stylesheets.  The benefits of compiled stylesheets are now so minor
        that this use case may also disappear and then so will this function.
        You have been warned.
        """
        self._extElements.update(elementMapping)
        for name in elementMapping:
            if name in self._extensionElementCache:
                del self._extensionElementCache[name]
        return

    # -- ContentHandler interface --------------------------------------

    def setDocumentLocator(self, locator):
        """
        Callback interface for SAX.
        """
        # Save the current document state for nested parsing (inclusions)
        document_state = (self._locator, self._stylesheet)
        self._document_state_stack.append(document_state)
        self._locator = locator
        self._stylesheet = None
        return

    def startDocument(self):
        """
        Callback interface for SAX.
        """
        # Our root is always a document
        # We use a document for this because of error checking and
        # because we explicitly pass ownerDocument to the nodes as
        # they are created
        document_uri = self._locator.getSystemId()
        root = tree.xslt_root(document_uri)
        if not self._root:
            self._root = root

        self._element_state_stack.append(
            parse_state(node=root,
                        validation=_XSLT_ROOT_VALIDATION,
                        localVariables={},
                        forwardsCompatible=False,
                        currentNamespaces={'xml': XML_NAMESPACE, None: None},
                        extensionNamespaces={},
                        outputNamespaces={},
                        )
            )

        # for recursive include checks for xsl:include/xsl:import
        self._visited_stylesheet_uris[document_uri] = True

        # namespaces added for the next element
        self._new_namespaces = {}
        return

    def endDocument(self):
        """
        Callback interface for SAX.
        """
        stack = self._element_state_stack
        state = stack[-1]
        del stack[-1]
        root = state.node

        # ----------------------------------------------------------
        # remove URI from recursive inclusion checking
        del self._visited_stylesheet_uris[root.baseUri]

        # ----------------------------------------------------------
        # finalize the children for the document
        #root.children = tuple(state.nodes)

        # ----------------------------------------------------------
        # finalize the stylesheet AST
        if stack:
            # An xsl:import or xsl:include
            # Merge the top-level elements into the "parent" stylesheet
            # IMPLEMENTATION NOTE: stack[-1] is the import/include element,
            # stack[-2] is the "parent" stylesheet
            stack[-2].node._merge(self._stylesheet)
            #parent_node = stack[-2].node
            #for child in self._stylesheet.children:
            #    child.parent = parent_node
        else:
            # A top-most stylesheet
            stylesheet = self._root.stylesheet
            if stylesheet is not self._stylesheet:
                # An additional stylesheet (e.g., an <?xml-stylesheet ...?>);
                # treat it as an xsl:import into the "master" stylesheet.
                stylesheet.reset()

                # Always update the precedence from the included stylesheet
                # because it may have contained imports thus increasing its
                # import precedence.
                self._import_index += 1
                stylesheet.importIndex = self._import_index

                # Merge the top-level elements into the "master" stylesheet
                stylesheet._merge(self._stylesheet)
                #stylesheet.children += self._stylesheet.children
                #for child in self._stylesheet.children:
                #    child.parent = stylesheet
            else:
                # Prepare for a possible subsequent parse.
                self._import_index += 1

            # Prepare the "master" stylesheet
            stylesheet.setup()

        document_state = self._document_state_stack[-1]
        del self._document_state_stack[-1]
        self._locator, self._stylesheet = document_state
        return

    def startPrefixMapping(self, prefix, uri):
        """
        Callback interface for SAX.
        """
        self._new_namespaces[prefix] = uri
        return

    def startElementNS(self, expandedName, qualifiedName, attribs,
                       _element_classes=tree.ELEMENT_CLASSES,
                       _element_cache={}):
        """
        Callback interface for SAX.
        """
        parent_state = self._element_state_stack[-1]
        state = ParseState(**parent_state.__dict__)
        self._element_state_stack.append(state)

        # ----------------------------------------------------------
        # update in-scope namespaces
        if self._new_namespaces:
            d = state.currentNamespaces = state.currentNamespaces.copy()
            d.update(self._new_namespaces)

            d = state.outputNamespaces = state.outputNamespaces.copy()
            for prefix, uri in self._new_namespaces.iteritems():
                if uri not in (XML_NAMESPACE, XSL_NAMESPACE):
                    d[prefix] = uri

            # reset for next element
            self._new_namespaces = {}

        # ----------------------------------------------------------
        # get the class defining this element
        namespace, local = expandedName
        xsl_class = ext_class = None
        if namespace == XSL_NAMESPACE:
            try:
                xsl_class, validation, validation_token, legal_attrs = \
                    _element_cache[local]
            except KeyError:
                # We need to try to import (and cache) it
                try:
                    module = _element_classes[local]
                except KeyError:
                    if not state.forwardsCompatible:
                        raise XsltParserException(XsltError.XSLT_ILLEGAL_ELEMENT,
                                                  self._locator, local)
                    xsl_class = Undefinedxsltelement
                    validation_token = content_model.RESULT_ELEMENT
                else:
                    parts = module.split('.')
                    path = '.'.join(['Ft.Xml.Xslt'] + parts[:-1])
                    module = __import__(path, {}, {}, parts[-1:])
                    try:
                        xsl_class = module.__dict__[parts[-1]]
                    except KeyError:
                        raise ImportError('.'.join(parts))
                    validation_token = expandedName
                validation = xsl_class.content.compile()
                legal_attrs = xsl_class.legalAttrs.items()
                _element_cache[local] = (
                    xsl_class, validation, validation_token, legal_attrs)
        elif namespace in state.extensionNamespaces:
            try:
                ext_class, validation, legal_attrs = \
                    self._extensionElementCache[expandedName]
            except KeyError:
                try:
                    ext_class = self._extElements[expandedName]
                except KeyError:
                    ext_class = UndefinedExtensionElement
                validation = ext_class.content.compile()
                legal_attrs = ext_class.legalAttrs
                if legal_attrs is not None:
                    legal_attrs = ext_class.legalAttrs.items()
                self._extensionElementCache[expandedName] = (
                    ext_class, validation, legal_attrs)
            validation_token = contentinfo.RESULT_ELEMENT
        else:
            validation = _LITERAL_ELEMENT_VALIDATION
            validation_token = contentinfo.RESULT_ELEMENT
        state.validation = validation

        # ----------------------------------------------------------
        # verify that this element can be declared here
        try:
            next = parent_state.validation[validation_token]
        except KeyError:
            #self._debug_validation(expandedName)
            parent = parent_state.node
            if parent is self._stylesheet:
                if (XSL_NAMESPACE, 'import') == expandedName:
                    raise XsltParserException(XsltError.ILLEGAL_IMPORT,
                                              self._locator)
            elif parent.expandedName == (XSL_NAMESPACE, 'choose'):
                if (XSL_NAMESPACE, 'otherwise') == expandedName:
                    raise XsltParserException(XsltError.ILLEGAL_CHOOSE_CHILD,
                                              self._locator)
            # ignore whatever elements are defined within an undefined
            # element as an exception will occur when/if this element
            # is actually instantiated
            if parent.__class__ is not UndefinedExtensionElement:
                raise XsltParserException(XsltError.ILLEGAL_ELEMENT_CHILD,
                                          self._locator, qualifiedName,
                                          parent.nodeName)
        else:
            # save this state for next go round
            parent_state.validation = next

        # ----------------------------------------------------------
        # create the instance defining this element
        klass = (xsl_class or ext_class or tree.literal_element)
        state.node = instance = klass(self._root, namespace, local,
                                      qualifiedName)
        instance.baseUri = self._locator.getSystemId()
        instance.lineNumber = self._locator.getLineNumber()
        instance.columnNumber = self._locator.getColumnNumber()
        instance.importIndex = self._import_index
        instance.namespaces = state.currentNamespaces

        # -- XSLT element --------------------------------------
        if xsl_class:
            # Handle attributes in the null-namespace
            standand_attributes = local in ('stylesheet', 'transform')
            inst_dict = instance.__dict__
            for attr_name, attr_info in legal_attrs:
                attr_expanded = (None, attr_name)
                if attr_expanded in attribs:
                    value = attribs[attr_expanded]
                    del attribs[attr_expanded]
                elif attr_info.required:
                    raise XsltParserException(
                        XsltError.MISSING_REQUIRED_ATTRIBUTE,
                        self._locator, qualifiedName, attr_name)
                else:
                    value = None
                try:
                    value = attr_info.prepare(instance, value)
                except XsltError, e:
                    raise self._mutate_exception(e, qualifiedName)

                if standand_attributes:
                    self._stylesheet = instance
                    self._handle_standard_attr(state, instance, attr_name,
                                               value)
                else:
                    if '-' in attr_name:
                        attr_name = attr_name.replace('-', '_')
                    inst_dict['_' + attr_name] = value

            if attribs:
                # Process attributes with a namespace-uri and check for
                # any illegal attributes in the null-namespace
                for expanded in attribs:
                    attr_ns, attr_name = expanded
                    if attr_ns is None:
                        if not state.forwardsCompatible:
                            raise XsltParserException(
                                XsltError.ILLEGAL_NULL_NAMESPACE_ATTR,
                                self._locator, attr_name, qualifiedName)
                    else:
                        instance.setAttribute(attr_ns, attr_name,
                                              attribs[expanded])

            # XSLT Spec 2.6 - Combining Stylesheets
            if local in ('import', 'include'):
                self._combine_stylesheet(instance._href, (local == 'import'))

        # -- extension element ---------------------------------
        elif ext_class:
            validate_attributes = (legal_attrs is not None)
            if validate_attributes:
                # Handle attributes in the null-namespace
                inst_dict = instance.__dict__
                for attr_name, attr_info in legal_attrs:
                    attr_expanded = (None, attr_name)
                    if attr_expanded in attribs:
                        value = attribs[attr_expanded]
                        del attribs[attr_expanded]
                    elif attr_info.required:
                        raise XsltParserException(
                            XsltError.MISSING_REQUIRED_ATTRIBUTE,
                            self._locator, qualifiedName, attr_name)
                    else:
                        value = None
                    try:
                        value = attr_info.prepare(instance, value)
                    except XsltError, e:
                        raise self._mutate_exception(e, qualifiedName)
                    if '-' in attr_name:
                        attr_name = attr_name.replace('-', '_')
                    inst_dict['_' + attr_name] = value

            # Process attributes with a namespace-uri and check for
            # any illegal attributes in the null-namespace
            if attribs:
                for expanded in attribs:
                    attr_ns, attr_name = expanded
                    value = attribs[expanded]
                    if validate_attributes and attr_ns is None:
                        raise XsltParserException(
                            XsltError.ILLEGAL_NULL_NAMESPACE_ATTR, self._locator,
                            attr_name, qualifiedName)
                    elif attr_ns == XSL_NAMESPACE:
                        self._handle_result_element_attr(state, instance,
                                                         qualifiedName,
                                                         attr_name, value)
                    else:
                        instance.setAttribute(attr_ns, attr_name, value)

        # -- literal result element ----------------------------
        else:
            output_attrs = []
            for expanded in attribs:
                attr_ns, attr_local = expanded
                value = attribs[expanded]
                if attr_ns == XSL_NAMESPACE:
                    self._handle_result_element_attr(state, instance,
                                                     qualifiedName,
                                                     attr_local, value)
                else:
                    # prepare attributes for literal output
                    value = RESULT_ELEMENT_ATTR_INFO.prepare(instance, value)
                    attr_qname = attribs.getQNameByName(expanded)
                    output_attrs.append((attr_qname, attr_ns, value))

            # save information for literal output
            instance._output_namespace = namespace
            instance._output_nss = state.outputNamespaces
            instance._output_attrs = output_attrs

            # Check for top-level result-element in null namespace
            if parent_state.node is self._stylesheet and \
                   not namespace and not state.forwardsCompatible:
                raise XsltParserException(XsltError.ILLEGAL_ELEMENT_CHILD,
                                          self._locator, qualifiedName,
                                          parent_state.node.nodeName)

        if instance.doesPrime:
            self._root.primeInstructions.append(instance)
        if instance.doesIdle:
            self._root.idleInstructions.append(instance)
        return

    def endElementNS(self, expandedName, qualifiedName):
        """
        Callback interface for SAX.
        """
        stack = self._element_state_stack
        state = stack[-1]
        del stack[-1]
        parent_state = stack[-1]
        element = state.node

        # ----------------------------------------------------------
        # verify that this element has all required content
        try:
            state.validation[contentinfo.END_ELEMENT]
        except KeyError:
            if expandedName == (XSL_NAMESPACE, u'choose'):
                raise XsltParserException(XsltError.CHOOSE_REQUIRES_WHEN,
                                          self._locator)
            raise

        # ----------------------------------------------------------
        # setup variable context
        if state.localVariables is not parent_state.localVariables:
            # add context save/restore nodes
            binding_stack = []
            node = PushVariablesNode(self._root, binding_stack)
            element.insertChild(0, node)
            node = PopVariablesNode(self._root, binding_stack)
            element.appendChild(node)

        # ----------------------------------------------------------
        # finalize the children for this element
        #element.children = tuple(state.nodes)
        #for child in element.children:
        #    if child.doesSetup:
        #s        child.setup()
        del state

        # ----------------------------------------------------------
        # update parent state
        parent_node = parent_state.node
        if self._stylesheet is None and parent_node is element.root:
            # a literal result element as stylesheet
            assert isinstance(element, tree.literal_element), element
            try:
                version = element._version
            except AttributeError:
                raise XsltParserException(XsltError.LITERAL_RESULT_MISSING_VERSION,
                                          self._locator)

            # Reset the root's validation as it has already seen an element.
            parent_state.validation = _XSLT_ROOT_VALIDATION

            # FIXME: use the prefix from the document for the XSL namespace
            stylesheet = (XSL_NAMESPACE, u'stylesheet')
            self.startElementNS(stylesheet, u'xsl:stylesheet',
                                {(None, u'version') : version})

            template = (XSL_NAMESPACE, u'template')
            self.startElementNS(template, u'xsl:template',
                                {(None, u'match') :  u'/'})

            # make this element the template's content
            # Note, this MUST index the stack as the stack has changed
            # due to the startElementNS() calls.
            stack[-1].node.appendChild(element)

            self.endElementNS(template, u'xsl:template')
            self.endElementNS(stylesheet, u'xsl:stylesheet')
            return

        parent_node.appendChild(element)

        if isinstance(element, GenericVariableElement):
            name = element._name
            if parent_node is self._stylesheet:
                # global variables
                if name in self._global_vars:
                    existing = self._global_vars[name]
                    if self._import_index > existing:
                        self._global_vars[name] = self._import_index
                    elif self._import_index == existing:
                        raise XsltParserException(
                            XsltError.DUPLICATE_TOP_LEVEL_VAR,
                            self._locator, name)
                else:
                    self._global_vars[name] = self._import_index
            else:
                # local variables
                # it is safe to ignore import precedence here
                local_vars = parent_state.localVariables
                if name in local_vars:
                    raise XsltParserException(XsltError.ILLEGAL_SHADOWING,
                                              self._locator, name)
                # Copy on use
                if local_vars is stack[-2].localVariables:
                    local_vars = local_vars.copy()
                    parent_state.localVariables = local_vars
                local_vars[name] = True
        return

    def characters(self, data):
        """
        Callback interface for SAX.
        """
        parent_state = self._element_state_stack[-1]
        # verify that the current element can have text children
        try:
            next = parent_state.validation[contentinfo.TEXT_NODE]
        except KeyError:
            # If the parent can have element children, but not text nodes,
            # ignore pure whitespace nodes. This clarification is from
            # XSLT 2.0 [3.4] Whitespace Stripping.
            # e.g. xsl:stylesheet, xsl:apply-templates, xsl:choose
            #self._debug_validation(contentinfo.TEXT_NODE)
            if (contentinfo.EMPTY in parent_state.validation or
                not isspace(data)):
                if len(data) > 10:
                    data = data[:10] + '...'
                raise XsltParserException(XsltError.ILLEGAL_TEXT_CHILD_PARSE,
                                          self._locator, repr(data),
                                          parent_state.node.nodeName)
            #self._debug_validation(contentinfo.TEXT_NODE)
        else:
            # update validation
            parent_state.validation = next

            node = StylesheetTree.XsltText(self._root, data)
            parent_state.node.appendChild(node)
        return

    # -- utility functions ---------------------------------------------

    def _combine_stylesheet(self, href, is_import):
        hint = is_import and 'STYLESHEET IMPORT' or 'STYLESHEET INCLUDE'
        try:
            new_source = self._input_source.resolve(href, hint=hint)
        except (OSError, UriException):
            # FIXME: create special inputsource for 4xslt command-line
            #for uri in self._alt_base_uris:
            #    try:
            #        new_href = self._input_source.getUriResolver().normalize(href, uri)
            #        #Do we need to figure out a way to pass the hint here?
            #        new_source = self._input_source.factory.fromUri(new_href)
            #        break
            #    except (OSError, UriException):
            #        pass
            #else:
            if 1:
                raise XsltParserException(XsltError.INCLUDE_NOT_FOUND,
                                          self._locator, href,
                                          self._locator.getSystemId())

        # XSLT Spec 2.6.1, Detect circular references in stylesheets
        # Note, it is NOT an error to include/import the same stylesheet
        # multiple times, rather that it may lead to duplicate definitions
        # which are handled regardless (variables, params, templates, ...)
        if new_source.uri in self._visited_stylesheet_uris:
            raise XsltParserException(XsltError.CIRCULAR_INCLUDE,
                                      self._locator, new_source.uri)
        self.fromSrc(new_source)

        self._import_index += is_import
        # Always update the precedence as the included stylesheet may have
        # contained imports thus increasing the import precedence.
        self._stylesheet.importIndex = self._import_index
        return


    def _handle_standard_attr(self, state, instance, name, value):
        if name == 'extension-element-prefixes':
            # a whitespace separated list of prefixes
            ext = state.extensionNamespaces = state.extensionNamespaces.copy()
            out = state.outputNamespaces = state.outputNamespaces.copy()
            for prefix in value:
                # add the namespace URI to the set of extension namespaces
                try:
                    uri = instance.namespaces[prefix]
                except KeyError:
                    raise XsltParserException(XsltError.UNDEFINED_PREFIX,
                                              self._locator,
                                              prefix or '#default')
                ext[uri] = True

                # remove all matching namespace URIs
                for output_prefix, output_uri in out.items():
                    if output_uri == uri:
                        del out[output_prefix]
        elif name == 'exclude-result-prefixes':
            # a whitespace separated list of prefixes
            out = state.outputNamespaces = state.outputNamespaces.copy()
            for prefix in value:
                try:
                    uri = instance.namespaces[prefix]
                except KeyError:
                    raise XsltParserException(XsltError.UNDEFINED_PREFIX,
                                              self._locator,
                                              prefix or '#default')
                # remove all matching namespace URIs
                for output_prefix, output_uri in out.items():
                    if output_uri == uri:
                        del out[output_prefix]
        elif name == 'version':
            # XSLT Spec 2.5 - Forwards-Compatible Processing
            state.forwardsCompatible = (value != 1.0)
            instance._version = value
        else:
            if '-' in name:
                name = name.replace('-', '_')
            instance.__dict__['_' + name] = value
        return

    def _handle_result_element_attr(self, state, instance, elementName,
                                    attributeName, value):
        try:
            attr_info = RESULT_ELEMENT_XSL_ATTRS[attributeName]
        except KeyError:
            raise XsltParserException(XsltError.ILLEGAL_XSL_NAMESPACE_ATTR,
                                      self._locator, attributeName,
                                      elementName)
        value = attr_info.prepare(instance, value)
        self._handle_standard_attr(state, instance, attributeName, value)
        return

    def _mutate_exception(self, exception, elementName):
        assert isinstance(exception, XsltError)
        exception.message = MessageSource.EXPRESSION_POSITION_INFO % (
            self._locator.getSystemId(), self._locator.getLineNumber(),
            self._locator.getColumnNumber(), elementName, exception.message)
        return exception

    # -- debugging routines --------------------------------------------

    def _debug_validation(self, token=None):
        from pprint import pprint
        state = self._element_state_stack[-1]
        parent = state.node
        print '='*60
        print 'parent =',parent
        print 'parent class =',parent.__class__
        print 'parent content =', parent.content
        print 'initial validation'
        pprint(parent.content.compile())
        print 'current validation'
        pprint(state.validation)
        if token:
            print 'token', token
        print '='*60
        return

    # -- parsing routines ----------------------------------------------

    def fromDocument(self, document, baseUri='', factory=None):
        """
        Read in a stylesheet source document from a Domlette and add it to
        the stylesheet tree. If a document with the same URI has already been
        read, the cached version will be used instead (so duplicate imports,
        includes, or stylesheet appends do not result in multiple reads).
        """
        if not baseUri:
            if hasattr(document, 'documentURI'):
                baseUri = document.documentURI
            elif hasattr(document, 'baseURI'):
                baseUri = document.baseURI
            else:
                raise TypeError('baseUri required')

        if factory is None:
            factory = inputsource.default_factory

        # check cache
        if self._root is not None:
            # We prefer to use an already-parsed doc, as it has had its
            # external entities and XIncludes resolved already
            if uri in self._root.sourceNodes:
                document = self._root.sourceNodes[baseUri]
            # It's OK to use cached string content, but we have no idea
            # whether we're using the same InputSource class as was used to
            # parse it the first time, and we don't cache external entities
            # or XIncludes, so there is the possibility of those things
            # being resolved differently this time around. Oh well.
            elif uri in self._root.sources:
                content = self._root.sources[baseUri]
                isrc = factory.fromString(content, baseUri)
                # temporarily uncache it so fromSrc will process it;
                # fromSrc will add it back to the cache when finished
                del self._root.sources[baseUri]
                return self.fromSrc(isrc)

        isrc = factory.fromStream(None, baseUri)
        features = []
        properties = [(property_dom_node, document)]
        stylesheet = self._parseSrc(isrc, features, properties)

        # Cache for XSLT document() function
        self._root.sourceNodes[baseUri] = document

        return stylesheet


    def parse(self, source):
        """
        Read in a stylesheet source document from an InputSource and add it to
        the stylesheet tree. If a document with the same URI has already been
        read, the cached version will be used instead (so duplicate imports,
        includes, or stylesheet appends do not result in multiple reads).
        """
        uri = source.uri

        #Check cache
        content = ''
        if self._root is not None:
            # We prefer to use an already-parsed doc, as it has had its
            # external entities and XIncludes resolved already
            if uri in self._root.sourceNodes:
                doc = self._root.sourceNodes[uri]
                # temporarily uncache it so fromDocument will process it;
                # fromDocument will add it back to the cache when finished
                del self._root.sourceNodes[uri]
                return self.fromDocument(doc, baseUri=uri)
            # It's OK to use cached string content, but we have no idea
            # whether we're using the same InputSource class as was used to
            # parse it the first time, and we don't cache external entities
            # or XIncludes, so there is the possibility of those things
            # being resolved differently this time around. Oh well.
            elif uri in self._root.sources:
                content = self._root.sources[uri]
                source = inputsource(content, uri)

        if not content:
            content = isrc.stream.read()
            isrc = isrc.clone(cStringIO.StringIO(content))

        features = [(sax.FEATURE_PROCESS_XINCLUDES, isrc.processIncludes)]
        properties = []
        stylesheet = self._parseSrc(isrc, features, properties)

        # Cache the string content for subsequent uses
        # e.g., xsl:import/xsl:include and document()
        self._root.sources[uri] = content

        return stylesheet

    def _parseSrc(self, isrc, features, properties):
        parser = sax.CreateParser()
        parser.setContentHandler(self)
        for featurename, value in features:
            parser.setFeature(featurename, value)

        # Always set whitespace rules property
        parser.setProperty(sax.PROPERTY_WHITESPACE_RULES,
                           STYLESHEET_WHITESPACE_RULES)
        for propertyname, value in properties:
            parser.setProperty(propertyname, value)

        prev_source = self._input_source
        try:
            self._input_source = isrc
            try:
                parser.parse(isrc)
            except SAXParseException, e:
                e = e.getException() or e
                if isinstance(e, XsltError):
                    raise e
                raise XsltError(XsltError.STYLESHEET_PARSE_ERROR, isrc.uri, e)
        finally:
            self._input_source = prev_source

        return self._root.stylesheet
