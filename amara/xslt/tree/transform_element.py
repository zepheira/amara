########################################################################
# amara/xslt/tree/stylesheet.py
"""
Implementation of the `xsl:stylesheet` and `xsl:transform` elements.
"""

import sys
import operator
import itertools
import collections
from gettext import gettext as _
from amara.tree import Element, Document, Text, Attr
from amara.namespaces import XMLNS_NAMESPACE, XSL_NAMESPACE
from amara import xpath
from amara.writers import outputparameters
from amara.xslt import XsltError, xsltcontext
from amara.xslt.tree import (xslt_element, content_model, attribute_types,
                             literal_element, variable_elements)


__all__ = ['match_tree', 'stylesheet_element']

TEMPLATE_CONFLICT_LOCATION = _(
    'In stylesheet %s, line %s, column %s, pattern %r')

_template_location = operator.attrgetter('baseUri', 'lineNumber',
                                         'columnNumber', '_match')

def _fixup_aliases(node, aliases):
    for child in node:
        if isinstance(child, literal_element):
            child.fixup_aliases(aliases)
            _fixup_aliases(child, aliases)
        elif isinstance(child, xslt_element):
            _fixup_aliases(child, aliases)
    return


# The dispatch table is first keyed by mode, then keyed by node type. If an
# element type, it is further keyed by the name test.
def _dispatch_table():
    class type_dispatch_table(collections.defaultdict):
        def __missing__(self, node_type):
            if node_type and issubclass(node_type, Element):
                value = self[node_type] = collections.defaultdict(list)
            else:
                value = self[node_type] = []
            return value
    return collections.defaultdict(type_dispatch_table)


def match_tree(patterns, context):
    """
    Returns all nodes, from context on down, that match the patterns
    """
    state = context.copy()

    # Save these before any changes are made to the context
    children = context.node.xml_children
    attributes = context.node.xml_attributes

    matched = patterns.xsltKeyPrep(context, context.node)

    pos = 1
    size = len(children)
    for node in children:
        context.node, context.position, context.size = node, pos, size
        map(lambda x, y: x.extend(y), matched, match_tree(patterns, context))
        pos += 1

    if attributes:
        size = len(attributes)
        pos = 1
        for node in attributes.nodes():
            context.node, context.position, context.size = node, pos, size
            map(lambda x, y: x.extend(y),
                matched, patterns.xsltKeyPrep(context, node))
            pos += 1

    context.set(state)
    return matched


class transform_element(xslt_element):
    content_model = content_model.seq(
        content_model.rep(content_model.qname(XSL_NAMESPACE, 'xsl:import')),
        content_model.top_level_elements,
        )
    attribute_types = {
        'id': attribute_types.id(),
        'extension-element-prefixes': attribute_types.prefixes(),
        'exclude-result-prefixes': attribute_types.prefixes(),
        'version': attribute_types.number(required=True),
        }

    space_rules = None
    decimal_formats = None
    namespace_aliases = None
    match_templates = None
    named_templates = None
    parameters = None
    variables = None
    global_variables = None
    initial_functions = None

    def setup(self, _param_element=variable_elements.param_element):
        """
        Called only once, at the first initialization
        """
        self.output_parameters = outputparameters.outputparameters()

        # Sort the top-level elements in decreasing import precedence to ease
        # processing later.
        precedence_key = operator.attrgetter('import_precedence')
        elements = sorted(self.children, key=precedence_key, reverse=True)

        # Merge the top-level stylesheet elements into their respective
        # lists.  Any element name not in the mapping is discarded.
        # Note, by sharing the same list no merging is required later.
        whitespace_elements, variable_elements = [], []
        top_level_elements = {
            'strip-space' : whitespace_elements,
            'preserve-space' : whitespace_elements,
            'output' : [],
            'key' : [],
            'decimal-format' : [],
            'namespace-alias' : [],
            'attribute-set': [],
            'variable' : variable_elements,
            'param' : variable_elements,
            'template' : [],
            }
        # Using `groupby` takes advantage of series of same-named elements
        # appearing adjacent to each other.
        key = operator.attrgetter('expanded_name')
        for (namespace, name), nodes in itertools.groupby(self.children, key):
            if namespace == XSL_NAMESPACE and name in top_level_elements:
                top_level_elements[name].extend(nodes)

        # - process the `xsl:preserve-space` and `xsl:strip-space` elements
        # RECOVERY: Multiple matching patterns use the last occurance
        space_rules = {}
        for element in whitespace_elements:
            strip = element._strip_whitespace
            for token in element._elements:
                namespace, name = token
                space_rules[token] = (namespace, name, strip)
        self.space_rules = space_rules.values()
        # sort in decreasing priority, where `*` is lowest, followed by
        # `prefix:*`, then all others.
        self.space_rules.sort(reverse=True)

        # - process the `xsl:output` elements
        # Sort in increasing import precedence, so the last one added
        # will have the highest import precedence
        elements = top_level_elements['output']
        getter = operator.attrgetter(
            '_method', '_version', '_encoding', '_omit_xml_declaration',
            '_standalone', '_doctype_system', '_doctype_public',
            '_cdata_section_elements', '_indent', '_media_type',
            '_byte_order_mark', '_canonical_form')
        for element in elements:
            (method, version, encoding, omit_xmldecl, standalone,
             doctype_system, doctype_public, cdata_elements, indent,
             media_type, byte_order_mark, canonical_form) = getter(element)
            if method is not None:
                self.output_parameters.method = method
            if version is not None:
                self.output_parameters.version = version
            if encoding is not None:
                self.output_parameters.encoding = encoding
            if omit_xmldecl is not None:
                self.output_parameters.omit_xml_declaration = omit_xmldecl
            if standalone is not None:
                self.output_parameters.standalone = standalone
            if doctype_system is not None:
                self.output_parameters.doctype_system = doctype_system
            if doctype_public is not None:
                self.output_parameters.doctype_public = doctype_public
            if cdata_elements:
                self.output_parameters.cdata_section_elements += cdata_elements
            if indent is not None:
                self.output_parameters.doctype_public = doctype_public
            if media_type is not None:
                self.output_parameters.doctype_public = doctype_public
            if byte_order_mark is not None:
                self.output_parameters.byte_order_mark = byte_order_mark
            if canonical_form is not None:
                self.output_parameters.canonical_form = canonical_form

        # - process the `xsl:key` elements
        # Group the keys by name
        keys = top_level_elements['key']
        name_key = operator.attrgetter('_name')
        keys.sort(key=name_key)
        self._keys = {}
        getter = operator.attrgetter('_match', '_use', 'namespaces')
        for name, keys in itertools.groupby(keys, name_key):
            self._keys[name] = map(getter, keys)

        # - process the `xsl:decimal-format` elements
        formats = self.decimal_formats = {}
        getter = operator.attrgetter(
            '_decimal_separator', '_grouping_separator', '_infinity',
            '_minus_sign', '_NaN', '_percent', '_per_mille', '_zero_digit',
            '_digit', '_pattern_separator')
        for element in top_level_elements['decimal-format']:
            name = element._name
            format = getter(element)
            # It is an error to declare a decimal-format more than once
            # (even with different import precedence) with different values.
            if name in formats and formats[name] != format:
                # Construct a useful name for the error message.
                if name:
                    namespace, name = name
                    if namespace:
                        name = element.namespaces[namespace] + ':' + name
                else:
                    name = '#default'
                raise XsltError(XsltError.DUPLICATE_DECIMAL_FORMAT, name)
            else:
              formats[name] = format
        # Add the default decimal format, if not declared.
        if None not in formats:
            formats[None] = ('.', ',', 'Infinity', '-', 'NaN', '%',
                             unichr(0x2030), '0', '#', ';')

        # - process the `xsl:namespace-alias` elements
        elements = top_level_elements['namespace-alias']
        elements.reverse()
        aliases = self.namespace_aliases = {}
        for precedence, group in itertools.groupby(elements, precedence_key):
            mapped = {}
            for element in group:
                namespace = element.namespaces[element._stylesheet_prefix]
                if namespace not in aliases:
                    mapped[namespace] = True
                    result_prefix = alias._result_prefix
                    result_namespace = element.namespaces[result_prefix]
                    aliases[namespace] = (result_namespace, result_prefix)
                # It is an error for a namespace URI to be mapped to multiple
                # different namespace URIs (with the same import precedence).
                elif namespace in mapped:
                    raise XsltError(XsltError.DUPLICATE_NAMESPACE_ALIAS,
                                    element._stylesheet_prefix)
        if aliases:
            # apply namespace fixup for the literal elements
            _fixup_aliases(self, aliases)

        # - process the `xsl:attribute-set` elements
        elements = top_level_elements['attribute-set']

        # - process the `xsl:param` and `xsl:variable` elements
        index, self._variables = {}, variable_elements[:]
        variable_elements.reverse()
        for element in variable_elements:
            name = element._name
            if name not in index:
                # unique (or first) variable binding
                index[name] = 1
            else:
                # shadowed variable binding, remove from processing list
                self._variables.remove(element)
        self.parameters = frozenset(element._name for element in self._variables
                                    if isinstance(element, _param_element))

        # - process the `xsl:template` elements
        match_templates = _dispatch_table()
        named_templates = self.named_templates = {}
        elements = top_level_elements['template']
        elements.reverse()
        getter = operator.attrgetter('node_test', 'axis_type', 'node_type')
        for position, element in enumerate(elements):
            match, name = element._match, element._name
            precedence = element.import_precedence
            if match:
                namespaces = element.namespaces
                template_priority = element._priority
                mode_table = match_templates[element._mode]
                for pattern in match:
                    node_test, axis_type, node_type = getter(pattern)
                    print node_type, pattern
                    if template_priority is None:
                        priority = node_test.priority
                    else:
                        priority = template_priority
                    info = ((precedence, template_priority, position),
                            node_test, axis_type, element)
                    # Add the template rule to the dispatch table
                    if node_type and issubclass(node_type, Element):
                        # Element types are further keyed by the name test.
                        name_key = node_test.name_key
                        if name_key:
                            prefix, local = name_key
                            # Unprefixed names are in the null-namespace
                            try:
                                namespace = prefix and namespaces[prefix]
                            except KeyError:
                                raise XPathError(XPathError.UNDEFINED_PREFIX,
                                                 prefix=prefix)
                            else:
                                name_key = namespace, prefix
                        mode_table[node_type][name_key].append(info)
                    else:
                        # Every other node type gets lumped into a single list
                        # for that node type
                        mode_table[node_type].append(info)
            if name:
                # XSLT 1.0, Section 6, Paragraph 3:
                # It is an error if a stylesheet contains more than one
                # template with the same name and same import precedence.
                if name not in named_templates:
                    named_templates[name] = element
                elif named_templates[name].import_precedence == precedence:
                    # Construct a useful name for the error message.
                    namespace, name = name
                    if namespace:
                        name = element.namespaces[namespace] + ':' + name
                    raise XsltError(XsltError.DUPLICATE_NAMED_TEMPLATE, name)
        # Now expanded the tables and convert to regular dictionaries to
        # prevent inadvertant growth when non-existant keys are used.
        match_templates = self.match_templates = dict(match_templates)
        for mode, type_table in match_templates.iteritems():
            # Add those patterns that don't have a distinct type:
            #   node(), id() and key() patterns
            any_patterns = type_table[None]
            type_table = match_templates[mode] = dict(type_table)
            for node_type, patterns in type_table.iteritems():
                if node_type:
                    if issubclass(node_type, Element):
                        # Add those that are wildcard tests ('*' and 'prefix:*')
                        wildcard_names = patterns[None]
                        name_table = type_table[node_type] = dict(patterns)
                        for name_key, patterns in name_table.iteritems():
                            if name_key is not None:
                                patterns.extend(wildcard_names)
                            patterns.extend(any_patterns)
                            patterns.sort(reverse=True)
                    else:
                        patterns.extend(any_patterns)
                        patterns.sort(reverse=True)
        return

    #def _printMatchTemplates(self):
    #    print "=" * 50
    #    print "match_templates:"
    #    templates = {}
    #    for mode in self.match_templates:
    #        print "-" * 50
    #        print "mode:",mode
    #        for nodetype in self.match_templates[mode]:
    #            print "  node type:",nodetype
    #            for patterninfo in self.match_templates[mode][nodetype]:
    #                pat, axistype, template = patterninfo
    #                print "    template matching pattern  %r  for axis type %s" % (pat, axistype)
    #                templates[template] = 1
    #
    #    print
    #    for template in templates.keys():
    #        template._printTemplateInfo()
    #
    #    return

    ############################# Prime Routines #############################

    def prime(self, context):
        processed = context.variables
        elements, deferred = self._variables, []
        num_writers = len(context._writers)
        while 1:
            for element in elements:
                if element._name in processed:
                    continue
                try:
                    element.instantiate(context)
                except XPathError, error:
                    if error.code != XPathError.UNDEFINED_VARIABLE:
                        raise
                    # Remove any aborted and possibly unbalanced
                    # outut handlers on the stack.
                    del context._writers[num_writers:]
                    deferred.append(element)
            if not deferred:
                break
            elif deferred == elements:
                # Just pick the first one as being the "bad" variable.
                raise XsltError(XsltError.CIRCULAR_VARIABLE,
                                name=deferred[0]._name)
            # Re-order stored variable elements to simplify processing for
            # the next transformation.
            for element in deferred:
                self._variables.remove(element)
                self._variables.append(element)
            # Try again, but this time processing only the ones that
            # referenced, as of yet, undefined variables.
            elements, deferred = deferred, []
        return

    def updateKey(self, doc, keyName, processor):
        """
        Update a particular key for a new document
        """
        from pprint import pprint
        if doc not in processor.keys:
            processor.keys[doc] = {}
        if keyName not in processor.keys[doc]:
            key_values = processor.keys[doc][keyName] = {}
        else:
            key_values = processor.keys[doc][keyName]
        try:
            keys = self._keys[keyName]
        except KeyError:
            return

        # Find the matching nodes using all matching xsl:key elements
        updates = {}
        for key in keys:
            match_pattern, use_expr, namespaces = key
            context = xsltcontext.xslt_context(
                doc, 1, 1, processorNss=namespaces, processor=processor,
                extFunctionMap=self.initialFunctions)
            patterns = PatternList([match_pattern], namespaces)
            matched = match_tree(patterns, context)[0]
            for node in matched:
                state = context.copy()
                context.node = node
                key_value_list = use_expr.evaluate(context)
                if not isinstance(key_value_list, list):
                    key_value_list = [key_value_list]
                for key_value in key_value_list:
                    if key_value not in updates:
                        updates[key_value] = [node]
                    else:
                        updates[key_value].append(node)
                context.set(state)

        # Put the updated results in document order with duplicates removed
        for key_value in updates:
            if key_value in key_values:
                nodes = Set.Union(key_values[key_value], updates[key_value])
            else:
                nodes = Set.Unique(updates[key_value])
            key_values[key_value] = nodes
        return

    def updateAllKeys(self, context, processor):
        """
        Update all the keys for all documents in the context
        Only used as an override for the default lazy key eval
        """
        for keyName in self._keys:
            for doc in context.documents.values():
                self.updateKey(doc, keyName, processor)
        return

    ############################# Exit Routines #############################

    def reset(self):
        """
        Called whenever the processor is reset, i.e. after each run
        Also called whenever multiple stylesheets are appended to
        a processor, because the new top-level elements from the
        new stylesheet need to be processed into the main one
        """
        self.reset1()
        self.reset2()
        return

    ############################ Runtime Routines ############################

    def apply_templates(self, context, nodes, mode=None, params=None,
                        precedence=None):
        """
        Intended to be used by XSLT instruction implementations only.

        Implements the xsl:apply-templates instruction by attempting to
        let the stylesheet apply its own template for the given context.
        If the stylesheet does not have a matching template, the
        built-in templates are invoked.

        context is an XsltContext instance. params is a dictionary of
        parameters being passed in, defaulting to None.
        """
        initial_focus = context.node, context.position, context.size
        initial_state = context.template, context.mode

        if params is None:
            params = {}

        context.size, context.mode = len(nodes), mode
        # Note, it is quicker to increment the `position` variable than it
        # is to use enumeration: itertools.izip(nodes, itertools.count(1))
        position = 1
        for node in nodes:
            # Set the current node for this template application
            context.node = context.current_node = node
            context.position = position
            position += 1

            # Get the possible template rules for `node`
            node_type = node.xml_type
            if mode in self.match_templates:
                type_table = self.match_templates[mode]
                if node_type in type_table:
                    if node_type == Element.xml_type:
                        element_table = type_table[node_type]
                        name = node.xml_name
                        if name in element_table:
                            template_rules = element_table[name]
                        else:
                            template_rules = element_table[None]
                    else:
                        template_rules = type_table[node_type]
                else:
                    template_rules = type_table[None]
            else:
                template_rules = ()

            # If this is called from apply-imports, filter out those patterns
            # with a higher import precedence than what was specified.
            if precedence:
                template_rules = ( rule for rule in template_rules
                                   if rule[0][0] < precedence )

            first_template = locations = None
            for sort_key, pattern, axis_type, template in template_rules:
                context.namespaces = template.namespaces
                if pattern.match(context, node, axis_type):
                    if 1: # recovery_method == Recovery.SILENT
                        # (default until recovery behaviour is selectable)
                        # Just use the first matching pattern since they are
                        # already sorted in descending order.
                        break
                    else: # recovery_method in (Recovery.WARNING, Recovery.NONE)
                        if not first_template:
                            first_template = template
                        else:
                            if not locations:
                                locations = [_template_location(first_template)]
                            locations.append(_template_location(template))
            else:
                # All template rules have been processed
                if locations:
                    # Multiple template rules have matched.  Report the
                    # template rule conflicts, sorted by position
                    locations.sort()
                    locations = '\n'.join(TEMPLATE_CONFLICT_LOCATION % location
                                          for location in locations)
                    exception = XsltError(XsltError.MULTIPLE_MATCH_TEMPLATES,
                                          node, locations)
                    if 1: # recovery_method == Recovery.WARNING
                        processor.warning(str(exception))
                    else:
                        raise exception
                if first_template:
                    template = first_template
                    context.namespaces = template.namespaces
                else:
                    template = None

            if template:
                context.template = template
                # Make sure the template starts with a clean slate
                variables = context.variables
                context.variables = context.global_variables
                try:
                    template.instantiate(context, params)
                finally:
                    context.variables = variables
            else:
                # Nothing matched, use builtin templates
                if params and not self._builtInWarningGiven:
                    self.warning(MessageSource.BUILTIN_TEMPLATE_WITH_PARAMS)
                    self._builtInWarningGiven = 1
                if isinstance(node, (Element, Document)):
                    self.apply_templates(context, node.xml_children)
                elif isinstance(node, (Text, Attr)):
                    context.text(node.xml_value)

        # Restore context
        context.node, context.position, context.size = initial_focus
        context.template, context.mode = initial_state
        return

#def PrintStylesheetTree(node, stream=None, indentLevel=0, showImportIndex=0,
#                        lastUri=None):
#    """
#    Function to print the nodes in the stylesheet tree, to aid in debugging.
#    """
#    stream = stream or sys.stdout
#    if lastUri != node.xml_base:
#        stream.write(indentLevel * '  ')
#        stream.write('====%s====\n' % node.xml_base)
#        lastUri = node.xml_base
#    stream.write(indentLevel * '  ' + str(node))
#    if showImportIndex:
#        stream.write(' [' + str(node.import_precedence) + ']')
#    stream.write('\n')
#    stream.flush()
#    show_ii = isinstance(node, xslt_element) and \
#        node.expandedName in [(XSL_NAMESPACE, 'stylesheet'),
#                              (XSL_NAMESPACE, 'transform')]
#    for child in node.children:
#        PrintStylesheetTree(child, stream, indentLevel+1, show_ii, lastUri)
#    return
