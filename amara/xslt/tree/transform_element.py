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

from amara.namespaces import XMLNS_NAMESPACE, XSL_NAMESPACE
from amara import tree, xpath
from amara.writers import outputparameters
from amara.xpath import XPathError, datatypes
from amara.xslt import XsltError, xsltcontext
from amara.xslt.tree import (xslt_element, content_model, attribute_types,
                             literal_element, variable_elements)


__all__ = ['match_tree', 'transform_element']

TEMPLATE_CONFLICT_LOCATION = _(
    'In stylesheet %s, line %s, column %s, pattern %r')

BUILTIN_TEMPLATE_WITH_PARAMS = _(
    'Built-in template invoked with parameters that will be ignored.')

_template_location = operator.attrgetter('baseUri', 'lineNumber',
                                         'columnNumber', '_match')

def _fixup_aliases(node, aliases):
    for child in node:
        if isinstance(child, literal_element.literal_element):
            child.fixup_aliases(aliases)
            _fixup_aliases(child, aliases)
        elif isinstance(child, xslt_element):
            _fixup_aliases(child, aliases)
    return


# The dispatch table is first keyed by mode, then keyed by node type. If an
# element type, it is further keyed by the name test.
class _type_dispatch_table(dict):
    def __missing__(self, type_key):
        if type_key == tree.element.xml_typecode:
            value = self[type_key] = collections.defaultdict(list)
        else:
            value = self[type_key] = []
        return value


class _key_dispatch_table(dict):

    __slots__ = ('_match_table', '_matches_attribute')

    _unpack_key = operator.attrgetter('_match', '_use', 'namespaces')
    _unpack_pattern = operator.attrgetter('node_test', 'axis_type', 'node_type')

    def __init__(self, keys):
        match_table = _type_dispatch_table()
        for key in keys:
            match, use, namespaces = self._unpack_key(key)
            for pattern in match:
                node_test, axis_type, node_type = self._unpack_pattern(pattern)
                info = (node_test, axis_type, namespaces, use)
                # Add the template rule to the dispatch table
                type_key = node_type.xml_typecode
                if type_key == tree.element.xml_typecode:
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
                            name_key = namespace, local
                    match_table[type_key][name_key].append(info)
                else:
                    # Every other node type gets lumped into a single list
                    # for that node type
                    match_table[type_key].append(info)
        # Now expanded the tables and convert to regular dictionaries to
        # prevent inadvertant growth when non-existant keys are used.
        # Add those patterns that don't have a distinct type:
        #   node(), id() and key() patterns
        any_patterns = match_table[tree.node.xml_typecode]
        match_table = self._match_table = dict(match_table)
        for type_key, patterns in match_table.iteritems():
            if type_key == tree.element.xml_typecode:
                # Add those that are wildcard tests ('*' and 'prefix:*')
                wildcard_names = patterns[None]
                name_table = match_table[type_key] = dict(patterns)
                for name_key, patterns in name_table.iteritems():
                    if name_key is not None:
                        patterns.extend(wildcard_names)
                    patterns.extend(any_patterns)
                    name_table[name_key] = tuple(patterns)
            else:
                patterns.extend(any_patterns)
                match_table[type_key] = tuple(patterns)
        self._matches_attribute = tree.attribute.xml_typecode in match_table

    def _match_nodes(self, context, nodes):
        initial_focus = context.node, context.position, context.size
        context.size = len(nodes)
        position = 1
        for node in nodes:
            context.node = context.current_node = node
            context.position = position
            position += 1
            # Get the possible maches for `node`
            type_key = node.xml_typecode
            type_table = self._match_table
            if type_key in type_table:
                if type_key == tree.element.xml_typecode:
                    element_table = type_table[type_key]
                    name_key = node.xml_name
                    if name_key in element_table:
                        matches = element_table[name_key]
                    else:
                        matches = element_table[None]
                else:
                    matches = type_table[type_key]
            else:
                matches = type_table[tree.node.xml_typecode]

            for pattern, axis_type, namespaces, use_expr in matches:
                context.namespaces = namespaces
                if pattern.match(context, node, axis_type):
                    focus = context.node, context.position, context.size
                    context.node, context.position, context.size = node, 1, 1
                    value = use_expr.evaluate(context)
                    if isinstance(value, datatypes.nodeset):
                        for value in value:
                            yield datatypes.string(value), node
                    else:
                        yield datatypes.string(value), node
                    context.node, context.position, context.size = focus

            if isinstance(node, tree.element):
                for item in self._match_nodes(context, node.xml_children):
                    yield item
                if self._matches_attribute and node.xml_attributes:
                    attributes = tuple(node.xml_attributes.nodes())
                    for item in self._match_nodes(context, attributes):
                        yield item
            elif isinstance(node, tree.entity):
                for item in self._match_nodes(context, node.xml_children):
                    yield item
        context.node, context.position, context.size = initial_focus
        return

    def __missing__(self, key):
        assert isinstance(key, tree.entity), key
        values = collections.defaultdict(set)
        context = xsltcontext.xsltcontext(key, 1, 1)
        for value, node in self._match_nodes(context, [key]):
            values[value].add(node)
        # Now store the unique nodes as an XPath nodeset
        values = self[key] = dict(values)
        for value, nodes in values.iteritems():
            values[value] = datatypes.nodeset(nodes)
        return values


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
    attribute_sets = None
    match_templates = None
    named_templates = None
    parameters = None
    variables = None
    global_variables = None
    initial_functions = None

    builtin_param_warning = True

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
                self.output_parameters.indent = indent
            if media_type is not None:
                self.output_parameters.media_type = media_type
            if byte_order_mark is not None:
                self.output_parameters.byte_order_mark = byte_order_mark
            if canonical_form is not None:
                self.output_parameters.canonical_form = canonical_form

        # - process the `xsl:key` elements
        # Group the keys by name
        elements = top_level_elements['key']
        name_key = operator.attrgetter('_name')
        elements.sort(key=name_key)
        keys = self._keys = {}
        for name, elements in itertools.groupby(elements, name_key):
            keys[name] = tuple(elements)

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
                    result_prefix = element._result_prefix
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
        sets = self.attribute_sets = {}
        for element in top_level_elements['attribute-set']:
            sets[element._name] = element

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
        match_templates = collections.defaultdict(_type_dispatch_table)
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
                    if template_priority is None:
                        priority = node_test.priority
                    else:
                        priority = template_priority
                    sort_key = (precedence, template_priority, position)
                    info = (sort_key, node_test, axis_type, element)
                    # Add the template rule to the dispatch table
                    type_key = node_type.xml_typecode
                    if type_key == tree.element.xml_typecode:
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
                                name_key = namespace, local
                        mode_table[type_key][name_key].append(info)
                    else:
                        # Every other node type gets lumped into a single list
                        # for that node type
                        mode_table[type_key].append(info)
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
            any_patterns = type_table[tree.node.xml_typecode]
            type_table = match_templates[mode] = dict(type_table)
            for type_key, patterns in type_table.iteritems():
                if type_key == tree.element.xml_typecode:
                    # Add those that are wildcard tests ('*' and 'prefix:*')
                    wildcard_names = patterns[None]
                    name_table = type_table[type_key] = dict(patterns)
                    for name_key, patterns in name_table.iteritems():
                        if name_key is not None:
                            patterns.extend(wildcard_names)
                        patterns.extend(any_patterns)
                        patterns.sort(reverse=True)
                        name_table[name_key] = tuple(patterns)
                else:
                    patterns.extend(any_patterns)
                    patterns.sort(reverse=True)
                    type_table[type_key] = tuple(patterns)
        #self._dump_match_templates(match_templates)
        return

    def _dump_match_templates(self, match_templates=None):
        from pprint import pprint
        if match_templates is None:
            match_templates = self.match_templates
        print "=" * 50
        for mode, type_table in match_templates.iteritems():
            print "mode:", mode
            for node_type, patterns in type_table.iteritems():
                print "  node type:", node_type
                print "  patterns: ",
                pprint(patterns)
                #for patterninfo in self.match_templates[mode][nodetype]:
                #    pat, axistype, template = patterninfo
                #    print "    template matching pattern  %r  for axis type %s" % (pat, axistype)
                #    templates[template] = 1
                print '-'*30
        return

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

        for name, keys in self._keys.iteritems():
            context.keys[name] = _key_dispatch_table(keys)
        return

    def update_keys(self, context):
        """
        Update all the keys for all documents in the context
        Only used as an override for the default lazy key eval
        """
        node = context.node
        for doc in context.documents.itervalues():
            context.node = doc
            for key_name in self._keys:
                self.update_key(context, key_name)
        context.node = node
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

    def apply_imports(self, context, precedence):
        node, mode = context.node, context.mode
        # Get the possible template rules for `node`
        type_key = node.xml_typecode
        if mode in self.match_templates:
            type_table = self.match_templates[mode]
            if type_key in type_table:
                if type_key == tree.element.xml_typecode:
                    element_table = type_table[type_key]
                    name = node.xml_name
                    if name in element_table:
                        template_rules = element_table[name]
                    else:
                        template_rules = element_table[None]
                else:
                    template_rules = type_table[type_key]
            else:
                template_rules = type_table[tree.node.xml_typecode]
        else:
            template_rules = ()

        first_template = locations = None
        for sort_key, pattern, axis_type, template in template_rules:
            # Filter out those patterns with a higher import precedence than
            # what was specified.
            if sort_key[0] < precedence:
                context.namespaces = template.namespaces
                if pattern.match(context, node, axis_type):
                    # Make sure the template starts with a clean slate
                    state = context.template, context.variables
                    context.template = template
                    context.variables = context.global_variables
                    try:
                        template.instantiate(context)
                    finally:
                        context.template, context.variables = state
                    break
        else:
            # Nothing matched, use builtin templates
            if isinstance(node, (tree.element, tree.entity)):
                self.apply_templates(context, node.xml_children)
            elif isinstance(node, (tree.text, tree.attribute)):
                context.text(node.xml_value)
        return

    def apply_templates(self, context, nodes, mode=None, params=None):
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
            type_key = node.xml_typecode
            if mode in self.match_templates:
                type_table = self.match_templates[mode]
                if type_key in type_table:
                    if type_key == tree.element.xml_typecode:
                        element_table = type_table[type_key]
                        name = node.xml_name
                        if name in element_table:
                            template_rules = element_table[name]
                        else:
                            template_rules = element_table[None]
                    else:
                        template_rules = type_table[type_key]
                else:
                    template_rules = type_table[tree.node.xml_typecode]
            else:
                template_rules = ()

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
                if params and self.builtin_param_warning:
                    context.processor.warning(BUILTIN_TEMPLATE_WITH_PARAMS)
                    self.builtin_param_warning = False
                if isinstance(node, (tree.element, tree.entity)):
                    self.apply_templates(context, node.xml_children)
                elif isinstance(node, (tree.text, tree.attribute)):
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
