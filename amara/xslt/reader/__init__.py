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
from amara.xslt import XsltError, XsltStaticError
from amara.xslt import extensions, exslt
from amara.xslt.tree import *

__all__ = ['stylesheet_reader']

# Whitespace stripping rules for a stylesheet:
#   preserve all whitespace within xsl:text elements;
#   strip whitespace from all other elements
_XSLT_WHITESPACE_STRIPPING = ((XSL_NAMESPACE, 'text', False), (None, '*', True))

# pseudo-nodes for save/restore of variable bindings
class push_variables_node(xslt_node):

    pseudo_node = True

    def __init__(self, root, scope):
        xslt_node.__init__(self, root)
        self._scope = scope
        return

    def instantiate(self, context):
        variables = context.variables
        self._scope.append(variables)
        context.variables = variables.copy()
        return

class pop_variables_node(xslt_node):

    pseudo_node = True

    def __init__(self, root, scope):
        xslt_node.__init__(self, root)
        self._scope = scope
        return

    def instantiate(self, context):
        scope = self._scope
        context.variables = scope[-1]
        del scope[-1]
        return


ELEMENT_CLASSES = {
    'apply-imports': apply_imports_element.apply_imports_element,
    'apply-templates': apply_templates_element.apply_templates_element,
    'attribute': attribute_element.attribute_element,
    'call-template': call_template_element.call_template_element,
    'choose': choose_elements.choose_element,
    'otherwise': choose_elements.otherwise_element,
    'when': choose_elements.when_element,
    'comment': comment_element.comment_element,
    'copy': copy_element.copy_element,
    'copy-of': copy_of_element.copy_of_element,
    'element': element_element.element_element,
    'fallback': fallback_elements.fallback_element,
    'for-each': for_each_element.for_each_element,
    'if': if_element.if_element,
    'message': message_element.message_element,
    'number': number_element.number_element,
    'processing-instruction':
        processing_instruction_element.processing_instruction_element,
    'stylesheet': transform_element.transform_element,
    'transform': transform_element.transform_element,
    'template': template_element.template_element,
    'text': text_element.text_element,
    'value-of': value_of_element.value_of_element,
    'variable': variable_elements.variable_element,
    'param': variable_elements.param_element,
    'sort': sort_element.sort_element,
    'with-param': with_param_element.with_param_element,

    'import': declaration_elements.import_element,
    'include': declaration_elements.include_element,
    'strip-space': declaration_elements.strip_space_element,
    'preserve-space': declaration_elements.preserve_space_element,
    'output': declaration_elements.output_element,
    'key': declaration_elements.key_element,
    'decimal-format': declaration_elements.decimal_format_element,
    'namespace-alias': declaration_elements.namespace_alias_element,
    'attribute-set': declaration_elements.attribute_set_element,
    }

# The XSL attributes allowed on literal elements
_RESULT_ELEMENT_XSL_ATTRS = {
    'exclude-result-prefixes' : attribute_types.prefixes(),
    'extension-element-prefixes' : attribute_types.prefixes(),
    'use-attribute-sets' : attribute_types.qnames(),
    'version' : attribute_types.number(),
    }
_RESULT_ELEMENT_ATTR_INFO = attribute_types.any_avt()

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
    _root = None

    def __init__(self):
        self._import_index = 0
        self._global_vars = {}
        self._visited_stylesheet_uris = {}
        self._document_state_stack = []
        self._element_state_stack = []
        self._extelements = {}
        self._extelements.update(exslt.extension_elements)
        self._extelements.update(extensions.extension_elements)
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
        self._extelements.update(elementMapping)
        for name in elementMapping:
            if name in self._extelement_cache:
                del self._extelement_cache[name]
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
        root = xslt_root(document_uri)
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
                stylesheet.import_precedence = self._import_index

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
                       _literal_element=literal_element.literal_element,
                       _element_classes=ELEMENT_CLASSES,
                       _element_cache={}, ):
        """
        Callback interface for SAX.
        """
        parent_state = self._element_state_stack[-1]
        state = parse_state(**parent_state.__dict__)
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
                    xsl_class = _element_classes[local]
                except KeyError:
                    if not state.forwardsCompatible:
                        raise XsltStaticError(XsltError.XSLT_ILLEGAL_ELEMENT,
                                              parent_state.node, element=local)
                    xsl_class = fallback_elements.undefined_xslt_element
                    validation_token = content_model.RESULT_ELEMENT
                else:
                    validation_token = expandedName
                validation = xsl_class.content_model.compile()
                legal_attrs = xsl_class.attribute_types.items()
                _element_cache[local] = (
                    xsl_class, validation, validation_token, legal_attrs)
        elif namespace in state.extensionNamespaces:
            try:
                ext_class, validation, legal_attrs = \
                    self._extelement_cache[expandedName]
            except KeyError:
                try:
                    ext_class = self._extelements[expandedName]
                except KeyError:
                    ext_class = fallback_elements.undefined_extension_element
                validation = ext_class.content_model.compile()
                legal_attrs = ext_class.attribute_types
                if legal_attrs is not None:
                    legal_attrs = legal_attrs.items()
                self._extelement_cache[expandedName] = (
                    ext_class, validation, legal_attrs)
            validation_token = content_model.RESULT_ELEMENT
        else:
            validation = _LITERAL_ELEMENT_VALIDATION
            validation_token = content_model.RESULT_ELEMENT
        state.validation = validation

        # ----------------------------------------------------------
        # verify that this element can be declared here
        try:
            next = parent_state.validation[validation_token]
        except KeyError:
            #self._debug_validation(expandedName)
            # ignore whatever elements are defined within an undefined
            # element as an exception will occur when/if this element
            # is actually instantiated
            if not isinstance(parent_state.node,
                              fallback_elements.undefined_extension_element):
                raise XsltStaticError(XsltError.ILLEGAL_ELEMENT_CHILD,
                                      parent_state.node, element=qualifiedName)
        else:
            # save this state for next go round
            parent_state.validation = next

        # ----------------------------------------------------------
        # create the instance defining this element
        klass = (xsl_class or ext_class or _literal_element)
        state.node = instance = klass(self._root, expandedName, qualifiedName,
                                      state.currentNamespaces)
        instance.baseUri = self._locator.getSystemId()
        instance.lineNumber = self._locator.getLineNumber()
        instance.columnNumber = self._locator.getColumnNumber()
        instance.import_precedence = self._import_index

        if xsl_class: # -- XSLT element --------------------------------
            # Handle attributes in the null-namespace
            standand_attributes = local in ('stylesheet', 'transform')
            inst_dict = instance.__dict__
            for attr_name, attr_info in legal_attrs:
                attr_expanded = (None, attr_name)
                if attr_expanded in attribs:
                    value = attribs[attr_expanded]
                    del attribs[attr_expanded]
                elif attr_info.required:
                    raise XsltStaticError(XsltError.MISSING_REQUIRED_ATTRIBUTE,
                                          instance, element=qualifiedName,
                                          attribute=attr_name)
                else:
                    value = None
                try:
                    value = attr_info.prepare(instance, value)
                except XsltError, e:
                    #raise self._mutate_exception(e, qualifiedName)
                    raise

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
                            raise XsltStaticError(
                                XsltError.ILLEGAL_NULL_NAMESPACE_ATTR, instance,
                                attribute=attr_name, element=qualifiedName)
                    else:
                        instance.setAttribute(attr_ns, attr_name,
                                              attribs[expanded])

            # XSLT Spec 2.6 - Combining Stylesheets
            if local in ('import', 'include'):
                self._combine_stylesheet(instance, (local == 'import'))
        elif ext_class: # -- extension element -------------------------
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
                        raise XsltStaticError(
                            XsltError.MISSING_REQUIRED_ATTRIBUTE, instance,
                            element=qualifiedName, attribute=attr_name)
                    else:
                        value = None
                    try:
                        value = attr_info.prepare(instance, value)
                    except XsltError, e:
                        #raise self._mutate_exception(e, qualifiedName)
                        raise
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
                        raise XsltStaticError(
                            XsltError.ILLEGAL_NULL_NAMESPACE_ATTR, instance,
                            attribute=attr_name, element=qualifiedName)
                    elif attr_ns == XSL_NAMESPACE:
                        self._handle_result_element_attr(state, instance,
                                                         qualifiedName,
                                                         attr_name, value)
                    else:
                        instance.setAttribute(attr_ns, attr_name, value)
        else: # -- literal result element ------------------------------
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
                    value = _RESULT_ELEMENT_ATTR_INFO.prepare(instance, value)
                    attr_qname = attribs.getQNameByName(expanded)
                    output_attrs.append((attr_qname, attr_ns, value))

            # save information for literal output
            instance._output_namespace = namespace
            instance._output_nss = state.outputNamespaces
            instance._output_attrs = output_attrs

            # Check for top-level result-element in null namespace
            if parent_state.node is self._stylesheet and \
                   not namespace and not state.forwardsCompatible:
                raise XsltStaticError(XsltError.ILLEGAL_ELEMENT_CHILD,
                                      parent_state.node, element=qualifiedName)
        return

    def endElementNS(self, expandedName, qualifiedName,
                     _literal_element=literal_element.literal_element,
                     _variable_element=variable_elements.variable_element):
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
            state.validation[content_model.END_ELEMENT]
        except KeyError:
            if expandedName == (XSL_NAMESPACE, u'choose'):
                raise XsltStaticError(XsltError.MISSING_REQUIRED_ELEMENT,
                                      element, element=element.nodeName,
                                      child='xsl:when')
            raise

        # ----------------------------------------------------------
        # setup variable context
        if state.localVariables is not parent_state.localVariables:
            # add context save/restore nodes
            binding_stack = []
            node = push_variables_node(self._root, binding_stack)
            element.insertChild(0, node)
            node = pop_variables_node(self._root, binding_stack)
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
            assert isinstance(element, _literal_element), element
            try:
                version = element._version
            except AttributeError:
                raise XsltStaticError(XsltError.LITERAL_RESULT_MISSING_VERSION,
                                      element)

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

        if isinstance(element, _variable_element):
            name = element._name
            if parent_node is self._stylesheet:
                # global variables
                if name in self._global_vars:
                    existing = self._global_vars[name]
                    if self._import_index > existing:
                        self._global_vars[name] = self._import_index
                    elif self._import_index == existing:
                        raise XsltStaticError(XsltError.DUPLICATE_TOP_LEVEL_VAR,
                                              element, variable=name)
                else:
                    self._global_vars[name] = self._import_index
            else:
                # local variables
                # it is safe to ignore import precedence here
                local_vars = parent_state.localVariables
                if name in local_vars:
                    raise XsltStaticError(XsltError.ILLEGAL_SHADOWING,
                                          element, variable=name)
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
            next = parent_state.validation[content_model.TEXT_NODE]
        except KeyError:
            # If the parent can have element children, but not text nodes,
            # ignore pure whitespace nodes. This clarification is from
            # XSLT 2.0 [3.4] Whitespace Stripping.
            # e.g. xsl:stylesheet, xsl:apply-templates, xsl:choose
            #self._debug_validation(content_model.TEXT_NODE)
            #if (content_model.EMPTY in parent_state.validation or
            #    not isspace(data)):
            if 1:
                if len(data) > 10:
                    data = data[:10] + '...'
                raise XsltStaticError(XsltError.ILLEGAL_TEXT_CHILD,
                                      parent_state.node, data=data,
                                      element=parent_state.node.nodeName)
            #self._debug_validation(content_model.TEXT_NODE)
        else:
            # update validation
            parent_state.validation = next

            node = xslt_text(self._root, data)
            parent_state.node.appendChild(node)
        return

    # -- utility functions ---------------------------------------------

    def _combine_stylesheet(self, element, is_import):
        href = element._href
        try:
            new_source = self._input_source.resolve(href)
        except (OSError, IriError):
            # FIXME: create special inputsource for 4xslt command-line
            #for uri in self._alt_base_uris:
            #    try:
            #        new_href = self._input_source.getUriResolver().normalize(href, uri)
            #        #Do we need to figure out a way to pass the hint here?
            #        new_source = self._input_source.factory.fromUri(new_href)
            #        break
            #    except (OSError, IriError):
            #        pass
            #else:
            raise XsltStaticError(XsltError.INCLUDE_NOT_FOUND, element,
                                  uri=href, base=self._locator.getSystemId())

        # XSLT Spec 2.6.1, Detect circular references in stylesheets
        # Note, it is NOT an error to include/import the same stylesheet
        # multiple times, rather that it may lead to duplicate definitions
        # which are handled regardless (variables, params, templates, ...)
        if new_source.uri in self._visited_stylesheet_uris:
            raise XsltStaticError(XsltError.CIRCULAR_INCLUDE, element,
                                  uri=new_source.uri)
        self.parse(new_source)

        self._import_index += is_import
        # Always update the precedence as the included stylesheet may have
        # contained imports thus increasing the import precedence.
        self._stylesheet.import_precedence = self._import_index
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
                    raise XsltStaticError(XsltError.UNDEFINED_PREFIX, instance,
                                          prefix=prefix or '#default')
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
                    raise XsltStaticError(XsltError.UNDEFINED_PREFIX, instance,
                                          prefix=prefix or '#default')
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
            attr_info = _RESULT_ELEMENT_XSL_ATTRS[attributeName]
        except KeyError:
            raise XsltStaticError(XsltError.ILLEGAL_XSL_NAMESPACE_ATTR,
                                  instance, attribute=attributeName,
                                  element=elementName)
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
        print 'parent content =', parent.content_model
        print 'initial validation'
        pprint(parent.content_model.compile())
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
                # temporarily uncache it so `parse()` will process it;
                # `parse()` will add it back to the cache when finished
                del self._root.sources[baseUri]
                return self.parse(isrc)

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
            content = source.stream.read()
            source = inputsource(cStringIO.StringIO(content), source.uri)

        #features = [(sax.FEATURE_PROCESS_XINCLUDES, True)]
        features, properties = [], []
        stylesheet = self._parseSrc(source, features, properties)

        # Cache the string content for subsequent uses
        # e.g., xsl:import/xsl:include and document()
        self._root.sources[uri] = content

        return stylesheet

    def _parseSrc(self, isrc, features, properties):
        parser = sax.create_parser()
        parser.setContentHandler(self)
        for featurename, value in features:
            parser.setFeature(featurename, value)

        # Always set whitespace rules property
        parser.setProperty(sax.PROPERTY_WHITESPACE_RULES,
                           _XSLT_WHITESPACE_STRIPPING)
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
                raise XsltError(XsltError.STYLESHEET_PARSE_ERROR,
                                uri=isrc.uri, text=str(e))
        finally:
            self._input_source = prev_source

        return self._root.stylesheet
