########################################################################
# amara/xupdate/elements.py
"""
XUpdate instructions
"""

from amara.xupdate import XUpdateError

__all__ = [
    'element_instruction', 'attribute_instruction', 'text_instruction',
    'processing_instruction_instruction', 'comment_instruction',
    ]

# TODO:
class xupdate_instruction(object):
    __slots__ = ('namespaces',)


class element_instruction(xupdate_instruction):
    __slots__ = ('name', 'namespace')

    def __init__(self, namespaces, name, namespace=None):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `name` attribute
        self.name = name
        # optional `namespace` attribute
        self.namespace = namespace
        return


class attribute_instruction(xupdate_instruction):
    __slots__ = ('name', 'namespace')

    def __init__(self, namespaces, name, namespace=None):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `name` attribute
        self.name = name
        # optional `namespace` attribute
        self.namespace = namespace
        return


class text_instruction(xupdate_instruction):
    pass


class processing_instruction_instruction(xupdate_instruction):
    __slots__ = ('name')

    def __init__(self, namespaces, name):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `name` attribute
        self.name = name
        return


class comment_instruction(xupdate_instruction):
    pass
