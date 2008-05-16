########################################################################
# amara/xupdate/commands.py
"""
XUpdate request processing
"""

from amara._xmlstring import IsQName
from amara.xpath import XPathError
from amara.xpath.parser import parse as parse_expression
from amara.xupdate import XUpdateError, xupdate_element

xupdate_command = xupdate_element

class variable_command(xupdate_command):
    element_name = 'variable'
    __slots__ = ('name', 'select')

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
            self.name = (namespace, name)
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
        self.select = select
        return


class insert_before_command(xupdate_command):
    element_name = 'insert-before'

    __slots__ = ('select',)

    def __init__(self, tagname, namespaces, attributes):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
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
            self.select = select
        return


class insert_after_command(insert_before_command):
    element_name = 'insert-after'


class append_command(xupdate_command):
    element_name = 'append'

    __slots__ = ('select', 'child')

    def __init__(self, tagname, namespaces, attributes):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
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
            self.select = select
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
        self.child = child
        return


class update_command(xupdate_command):
    element_name = 'update'

    __slots__ = ('select',)

    def __init__(self, tagname, namespaces, attributes):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
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
            self.select = select
        return


class rename_command(xupdate_command):
    element_name = 'rename'

    __slots__ = ('select',)

    def __init__(self, tagname, namespaces, attributes):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
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
            self.select = select
        return


class remove_command(xupdate_command):
    element_name = 'remove'

    __slots__ = ('select',)

    def __init__(self, tagname, namespaces, attributes):
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
            self.select = select
        return
