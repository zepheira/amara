########################################################################
# amara/xupdate/elements.py
"""
XUpdate instructions
"""

from amara._xmlstring import SplitQName
from amara.xpath import datatypes
from amara.xupdate import XUpdateError, xupdate_primitive

__all__ = [
    'element_instruction', 'attribute_instruction', 'text_instruction',
    'processing_instruction_instruction', 'comment_instruction',
    'value_of_instruction', 'literal_element'
    ]


class xupdate_instruction(xupdate_primitive):
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

    def instantiate(self, context):
        context.namespaces = self.namespaces
        name = self.name.evaluate_as_string(context)
        if self.namespace:
            namespace = self.namespace.evaluate_as_string(context)
        else:
            prefix, local = SplitQName(name)
            try:
                namespace = self.namespaces[prefix]
            except KeyError:
                if not prefix:
                    prefix = '#default'
                raise XUpdateError(XUpdateError.UNDEFINED_PREFIX,
                                   prefix=prefix)
        context.start_element(name, namespace)
        for child in self:
            child.instantiate(context)
        context.end_element(name, namespace)
        return


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

    def instantiate(self, context):
        context.namespaces = self.namespaces
        name = self.name.evaluate_as_string(context)
        if self.namespace:
            namespace = self.namespace.evaluate_as_string(context)
        else:
            prefix, local = SplitQName(name)
            if prefix:
                try:
                    namespace = self.namespaces[prefix]
                except KeyError:
                    raise XUpdateError(XUpdateError.UNDEFINED_PREFIX,
                                    prefix=prefix)
            else:
                namespace = None
        context.push_string_writer(errors=False)
        for child in self:
            child.instantiate(context)
        writer = context.pop_writer()
        context.attribute(name, writer.get_result(), namespace)
        return


class text_instruction(xupdate_instruction):

    def __repr__(self):
        return '<text children=%s>' % xupdate_instruction.__repr__(self)

    def instantiate(self, context):
        context.characters(self[0])
        return


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

    def instantiate(self, context):
        context.namespaces = self.namespaces
        name = self.name.evaluate_as_string(context)
        context.push_string_writer(errors=False)
        for child in self:
            child.instantiate(context)
        writer = context.pop_writer()
        context.processing_instruction(name, writer.get_result())
        return


class comment_instruction(xupdate_instruction):

    def __repr__(self):
        return '<comment children=%s>' % xupdate_instruction.__repr__(self)

    def instantiate(self, context):
        context.push_string_writer(errors=False)
        for child in self:
            child.instantiate(context)
        writer = context.pop_writer()
        context.comment(writer.get_result())
        return


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

    def instantiate(self, context):
        context.namespaces = self.namespaces
        result = self.select.evaluate(context)
        if isinstance(result, datatypes.nodeset):
            for node in result:
                context.copy_node(node)
        else:
            context.characters(datatypes.string(result))
        return


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

    def instantiate(self, context):
        context.start_element(self.name, self.namespace)
        for namespace, name, value in self.attributes:
            context.attribute(name, value, namespace)
        for child in self:
            child.instantiate(context)
        context.end_element(self.name, self.namespace)
        return


class literal_text(unicode):

    def instantiate(self, context):
        context.characters(self)