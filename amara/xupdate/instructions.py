########################################################################
# amara/xupdate/instructions.py
"""
XUpdate instructions
"""

from amara.xupdate import XUpdateError, xupdate_element

# TODO:
xupdate_instruction = xupdate_element

class element_instruction(xupdate_instruction):
    element_name = 'element'
    __slots__ = ('name', 'namespace')

    def __init__(self, tagname, namespaces, attributes):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `name` attribute
        try:
            name = attributes[None, 'name']
        except KeyError:
            raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                               element=tagname, attribute='name')
        else:
            self.name = qname_avt('name', name)
        # optional `namespace` attribute
        if (None, 'namespace') in attributes:
            self.namespace = namespace_avt(attributes[None, 'namespace'])
        else:
            self.namespace = None
        return


class attribute_instruction(xupdate_instruction):
    element_name = 'attribute'
    __slots__ = ('name', 'namespace')

    def __init__(self, tagname, namespaces, attributes):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `name` attribute
        try:
            name = attributes[None, 'name']
        except KeyError:
            raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                               element=tagname, attribute='name')
        else:
            self.name = qname_avt('name', name)
        # optional `namespace` attribute
        if (None, 'namespace') in attributes:
            self.namespace = namespace_avt(attributes[None, 'namespace'])
        else:
            self.namespace = None
        return


class text_instruction(xupdate_instruction):
    element_name = 'text'


class processing_instruction_instruction(xupdate_instruction):
    element_name = 'processing-instruction'
    __slots__ = ('name')

    def __init__(self, tagname, namespaces, attributes):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `name` attribute
        try:
            name = attributes[None, 'name']
        except KeyError:
            raise XUpdateError(XUpdateError.MISSING_REQUIRED_ATTRIBUTE,
                               element=tagname, attribute='name')
        else:
            self.name = ncname_avt('name', name)
        return


class comment_instruction(xupdate_instruction):
    element_name = 'comment'

