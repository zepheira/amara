########################################################################
# amara/xupdate/reader.py
"""
XUpdate document reader
"""

import operator
from amara import XML_NAMESPACE
from amara._expat import ContentModel, Handler, Reader
from amara._xmlstring import SplitQName, IsQName
from amara.xpath import XPathError
from amara.xpath.parser import parse as parse_expression
from amara.xupdate import XUpdateError, XUPDATE_NAMESPACE
from amara.xupdate import commands, instructions
from amara.xupdate.expressions import *

# -- validation models -------------------------------------------------

def qname_type(namespace, name):
    prefix, local = SplitQName(name)
    return ContentModel(ContentModel.TYPE_NAME, (namespace, local), label=name)

_end_event = ContentModel.FINAL_EVENT

_document_content = qname_type(XUPDATE_NAMESPACE, 'xupdate:modifications')
_document_model = _document_content.compile()

_empty_event = '/empty/'
_empty_content = ContentModel(ContentModel.TYPE_NAME, _empty_event,
                              ContentModel.QUANT_REP, label='/empty/')
_empty_model = _empty_content.compile()

_text_event = '#PCDATA'
_text_content = ContentModel(ContentModel.TYPE_NAME, _text_event,
                             ContentModel.QUANT_REP, label='#PCDATA')
_text_model = _text_content.compile()

_literal_event = (None, None)
_literal_content = ContentModel(ContentModel.TYPE_NAME, _literal_event,
                                ContentModel.QUANT_REP,
                                label='/literal-elements/')

_char_template_content = (
    _text_content,
    #qname_type(XUPDATE_NAMESPACE, 'xupdate:if'),
    qname_type(XUPDATE_NAMESPACE, 'xupdate:text'),
    qname_type(XUPDATE_NAMESPACE, 'xupdate:value-of'),
    )
_char_template_content = ContentModel(ContentModel.TYPE_ALT,
                                      _char_template_content,
                                      ContentModel.QUANT_REP,
                                      label='/char-template/')
_char_template_model = _char_template_content.compile()

_template_content = (
    _char_template_content,
    qname_type(XUPDATE_NAMESPACE, 'xupdate:element'),
    qname_type(XUPDATE_NAMESPACE, 'xupdate:attribute'),
    qname_type(XUPDATE_NAMESPACE, 'xupdate:processing-instruction'),
    qname_type(XUPDATE_NAMESPACE, 'xupdate:comment'),
    _literal_content,
    )
_template_content = ContentModel(ContentModel.TYPE_ALT, _template_content,
                                 ContentModel.QUANT_REP, label='/template/')
_template_model = _template_content.compile()

_toplevel_content = (
    qname_type(XUPDATE_NAMESPACE, 'xupdate:insert-before'),
    qname_type(XUPDATE_NAMESPACE, 'xupdate:insert-after'),
    qname_type(XUPDATE_NAMESPACE, 'xupdate:append'),
    qname_type(XUPDATE_NAMESPACE, 'xupdate:update'),
    qname_type(XUPDATE_NAMESPACE, 'xupdate:remove'),
    qname_type(XUPDATE_NAMESPACE, 'xupdate:rename'),
    qname_type(XUPDATE_NAMESPACE, 'xupdate:variable'),
    qname_type(XUPDATE_NAMESPACE, 'xupdate:if'),
    _literal_content)
_toplevel_content = ContentModel(ContentModel.TYPE_ALT, _toplevel_content,
                                 ContentModel.QUANT_REP,
                                 label='/top-level-elements/')
_toplevel_model = _toplevel_content.compile()

# -- element types -----------------------------------------------------

_elements = {}

def autodispatch(element, model):
    """Decorator for adding content-model information"""
    def decorator(func):
        _elements[element] = (func, model)
        return func
    return decorator

@autodispatch('modifications', _toplevel_model)
def modifications_element(tagname, namespaces, attributes):
    try:
        version = attributes[None, 'version']
    except KeyError:
        raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                           element=tagname, attribute='version')
    else:
        if version != '1.0':
            raise XUpdateError(XUpdateError.UNSUPPORTED_VERSION,
                               version=version)
    return commands.modifications_list()

@autodispatch('insert-before', _template_model)
def insert_before_element(tagname, namespaces, attributes):
    # required `select` attribute
    try:
        select = attributes[None, 'select']
    except KeyError:
        raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                            element=tagname, attribute='select')
    else:
        try:
            select = parse_expression(select)
        except XPathError, error:
            raise XUpdateError(XUpdateError.SYNTAX_ERROR,
                               expression=select, text=str(error))
    return commands.insert_before_command(namespaces, select)

@autodispatch('insert-after', _template_model)
def insert_after_element(tagname, namespaces, attributes):
    # required `select` attribute
    try:
        select = attributes[None, 'select']
    except KeyError:
        raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                            element=tagname, attribute='select')
    else:
        try:
            select = parse_expression(select)
        except XPathError, error:
            raise XUpdateError(XUpdateError.SYNTAX_ERROR,
                               expression=select, text=str(error))
    return commands.insert_after_command(namespaces, select)

@autodispatch('append', _template_model)
def append_element(tagname, namespaces, attributes):
    # required `select` attribute
    try:
        select = attributes[None, 'select']
    except KeyError:
        raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                           element=tagname, attribute='select')
    else:
        try:
            select = parse_expression(select)
        except XPathError, error:
            raise XUpdateError(XUpdateError.SYNTAX_ERROR,
                                expression=select, text=str(error))
    # optional `child` attribute
    if (None, 'child') in attributes:
        child = attributes[None, 'child']
        try:
            child = parse_expression(child)
        except XPathError, error:
            raise XUpdateError(XUpdateError.SYNTAX_ERROR,
                               expression=child, text=str(error))
    else:
        child = None
    return commands.append_command(namespaces, select, child)

@autodispatch('update', _char_template_model)
def update_element(tagname, namespaces, attributes):
    # required `select` attribute
    try:
        select = attributes[None, 'select']
    except KeyError:
        raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                            element=tagname, attribute='select')
    else:
        try:
            select = parse_expression(select)
        except XPathError, error:
            raise XUpdateError(XUpdateError.SYNTAX_ERROR,
                               expression=select, text=str(error))
    return commands.update_command(namespaces, select)

@autodispatch('remove', _empty_model)
def remove_element(tagname, namespaces, attributes):
    # required `select` attribute
    try:
        select = attributes[None, 'select']
    except KeyError:
        raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                            element=tagname, attribute='select')
    else:
        try:
            select = parse_expression(select)
        except XPathError, error:
            raise XUpdateError(XUpdateError.SYNTAX_ERROR,
                               expression=select, text=str(error))
    return commands.remove_command(namespaces, select)

@autodispatch('rename', _char_template_model)
def rename_element(tagname, namespaces, attributes):
    # required `select` attribute
    try:
        select = attributes[None, 'select']
    except KeyError:
        raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                            element=tagname, attribute='select')
    else:
        try:
            select = parse_expression(select)
        except XPathError, error:
            raise XUpdateError(XUpdateError.SYNTAX_ERROR,
                               expression=select, text=str(error))
    return commands.rename_command(namespaces, select)

@autodispatch('variable', _template_model)
def variable_element(tagname, namespaces, attributes):
    # required `name` attribute
    try:
        name = attributes[None, 'name']
    except KeyError:
        raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                           element=tagname, attribute='name')
    else:
        if not IsQName(name):
            raise XUpdateError(XUpdateError.INVALID_QNAME_ATTR,
                               attribute='name', value=name)
        prefix, name = SplitQName(name)
        if prefix:
            try:
                namespace = namespaces[prefix]
            except KeyError:
                raise XUpdateError(XUpdateError.UNDEFINED_PREFIX,
                                   prefix=prefix)
        else:
            namespace = None
        name = (namespace, name)
    # optional `select` attribute
    if (None, 'select') in attributes:
        select = attributes[None, 'select']
        try:
            select = parse_expression(select)
        except XPathError, error:
            raise XUpdateError(XUpdateError.SYNTAX_ERROR,
                               expression=select, text=str(error))
    else:
        select = None
    return commands.variable_command(namespaces, name, select)

@autodispatch('if', _toplevel_model)
def if_element(tagname, namespaces, attributes):
    # required `test` attribute
    try:
        test = attributes[None, 'test']
    except KeyError:
        raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                            element=tagname, attribute='test')
    else:
        try:
            test = parse_expression(test)
        except XPathError, error:
            raise XUpdateError(XUpdateError.SYNTAX_ERROR,
                               expression=test, text=str(error))
    return commands.if_command(namespaces, test)

@autodispatch('element', _template_model)
def element_element(tagname, namespaces, attributes):
    # required `name` attribute
    try:
        name = attributes[None, 'name']
    except KeyError:
        raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                           element=tagname, attribute='name')
    else:
        name = qname_avt('name', name)
    # optional `namespace` attribute
    if (None, 'namespace') in attributes:
        namespace = namespace_avt(attributes[None, 'namespace'])
    else:
        namespace = None
    return instructions.element_instruction(namespaces, name, namespace)

@autodispatch('attribute', _char_template_model)
def attribute_element(tagname, namespaces, attributes):
    # required `name` attribute
    try:
        name = attributes[None, 'name']
    except KeyError:
        raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                           element=tagname, attribute='name')
    else:
        name = qname_avt('name', name)
    # optional `namespace` attribute
    if (None, 'namespace') in attributes:
        namespace = namespace_avt(attributes[None, 'namespace'])
    else:
        namespace = None
    return instructions.attribute_instruction(namespaces, name, namespace)

@autodispatch('text', _text_model)
def text_element(tagname, namespaces, attributes):
    return instructions.text_instruction()

@autodispatch('processing-instruction', _char_template_model)
def processing_instruction_element(tagname, namespaces, attributes):
    # required `name` attribute
    try:
        name = attributes[None, 'name']
    except KeyError:
        raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                           element=tagname, attribute='name')
    else:
        name = ncname_avt('name', name)
    return instructions.processing_instruction_instruction(namespaces, name)

@autodispatch('comment', _char_template_model)
def comment_element(tagname, namespaces, attributes):
    return instructions.comment_instruction()

@autodispatch('value-of', _empty_model)
def value_of_element(tagname, namespaces, attributes):
    # required `select` attribute
    try:
        select = attributes[None, 'select']
    except KeyError:
        raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                            element=tagname, attribute='select')
    else:
        try:
            select = parse_expression(select)
        except XPathError, error:
            raise XUpdateError(XUpdateError.SYNTAX_ERROR,
                               expression=select, text=str(error))
    return instructions.value_of_instruction(namespaces, select)


class handler_state(object):
    __slots__ = ('item', 'name', 'namespaces', 'validation')
    def __init__(self, item, name, namespaces, validation):
        self.item = item
        self.name = name
        self.namespaces = namespaces
        self.validation = validation


class xupdate_handler(Handler):

    def __init__(self):
        self._modifications = []
        self._dispatch = _elements
        self._state_stack = [
            handler_state(self._modifications, '#document',
                          {'xml': XML_NAMESPACE, None: None}, _document_model)
            ]
        self._push_state = self._state_stack.append

    modifications = property(operator.attrgetter('_modifications'))

    def start_element(self, expandedName, tagName, namespaces, attributes):
        parent_state = self._state_stack[-1]

        # update in-scope namespaces (copy-on-demand)
        if namespaces:
            inscope_namespaces = parent_state.namespaces.copy()
            inscope_namespaces.update(namespaces)
        else:
            inscope_namespaces = parent_state.namespaces

        # get the class defining this element
        namespace, local = expandedName
        if namespace == XUPDATE_NAMESPACE:
            try:
                factory, validation = self._dispatch[local]
            except KeyError:
                raise XUpdateError(XUpdateError.ILLEGAL_ELEMENT,
                                   element=tagName)
            else:
                item = factory(tagName, inscope_namespaces, attributes)
            validation_event = expandedName
        else:
            qname = attributes.getQNameByName
            attrs = [ (name[0], qname(name), attributes[name])
                      for name in attributes ]
            item = instructions.literal_element(tagName, namespace, attrs)
            validation = _template_model
            validation_event = _literal_event
        # verify that this element can be declared here
        try:
            next = parent_state.validation[validation_event]
        except KeyError:
            raise XUpdateError(XUpdateError.ILLEGAL_ELEMENT_CHILD,
                               element=parent_state.name, child=tagName)
        else:
            # save the new state for the next event check
            parent_state.validation = next
        new_state = handler_state(item, tagName, inscope_namespaces, validation)
        self._push_state(new_state)
        return

    def end_element(self, expandedName, tagName):
        current_state = self._state_stack[-1]
        del self._state_stack[-1]
        parent_state = self._state_stack[-1]
        item = current_state.item

        # verify that the element has all required content
        try:
            current_state.validation[_end_event]
        except KeyError:
            raise XUpdateError(XUpdateError.INCOMPLETE_ELEMENT,
                               element=tagName)
        ## let the XUpdate primitive perform any add'l setup, if needed
        #if item.has_setup:
        #    item.setup()
        # update parent state
        parent_state.item.append(item)
        return

    def characters(self, data):
        current_state = self._state_stack[-1]
        # verify that the current node can have text content
        try:
            next = current_state.validation[_text_event]
        except KeyError:
            raise XUpdateError(XUpdateError.INVALID_TEXT,
                               element=current_state.name)
        else:
            current_state.validation = next
        current_state.item.append(instructions.literal_text(data))
        return


def parse(source):
    handler = xupdate_handler()
    reader = Reader((handler,))
    reader.parse(source)
    return handler.modifications[0]
