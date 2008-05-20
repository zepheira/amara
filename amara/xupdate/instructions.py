########################################################################
# amara/xupdate/elements.py
"""
XUpdate instructions
"""

from amara.xupdate import XUpdateError

__all__ = [
    'element_instruction', 'attribute_instruction', 'text_instruction',
    'processing_instruction_instruction', 'comment_instruction',
    'value_of_instruction', 'literal_element'
    ]


class xupdate_instruction(list):
    # Note, no need to call `list.__init__` if there are no initial
    # items to be added. `list.__new__` takes care of the setup for
    # new empty lists.
    pass


class element_instruction(xupdate_instruction):
    __slots__ = ('namespaces', 'name', 'namespace')

    def __init__(self, namespaces, name, namespace=None):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `name` attribute
        self.name = name
        # optional `namespace` attribute
        self.namespace = namespace
        return

    def __repr__(self):
        return '<element name=%s, namespace=%s, children=%s>' % (
            self.name, self.namespace, xupdate_instruction.__repr__(self))


class attribute_instruction(xupdate_instruction):
    __slots__ = ('namespaces', 'name', 'namespace')

    def __init__(self, namespaces, name, namespace=None):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `name` attribute
        self.name = name
        # optional `namespace` attribute
        self.namespace = namespace
        return

    def __repr__(self):
        return '<attribute name=%s, namespace=%s, children=%s>' % (
            self.name, self.namespace, xupdate_instruction.__repr__(self))


class text_instruction(xupdate_instruction):

    def __repr__(self):
        return '<text children=%s>' % xupdate_instruction.__repr__(self)


class processing_instruction_instruction(xupdate_instruction):
    __slots__ = ('namespaces', 'name',)

    def __init__(self, namespaces, name):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `name` attribute
        self.name = name
        return

    def __repr__(self):
        return '<processing-instruction name=%s, children=%s>' % (
            self.name, xupdate_instruction.__repr__(self))


class comment_instruction(xupdate_instruction):
    def __repr__(self):
        return '<comment children=%s>' % xupdate_instruction.__repr__(self)


class value_of_instruction(xupdate_instruction):
    __slots__ = ('namespaces', 'select',)
    def __init__(self, namespaces, select):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `select` attribute
        self.select = select
        return

    def __repr__(self):
        return '<value-of select=%s>' % (self.select,)


class literal_element(xupdate_instruction):
    __slots__ = ('name', 'namespace', 'attributes')
    def __init__(self, name, namespace, attributes):
        self.name = name
        self.namespace = namespace
        self.attributes = attributes

    def __repr__(self):
        return '<literal name=%s, namespace=%s, attributes=%s, children=%s>' % (
            self.name, self.namespace, self.attributes,
            xupdate_instruction.__repr__(self))