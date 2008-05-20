########################################################################
# amara/xupdate/commands.py
"""
XUpdate request processing
"""

from amara._xmlstring import IsQName
from amara.xpath import XPathError
from amara.xpath.parser import parse as parse_expression
from amara.xupdate import XUpdateError, xupdate_element

__all__ = [
    'modifications_element', 'variable_command', 'insert_before_command',
    'insert_after_command', 'append_command', 'update_command',
    'rename_command', 'remove_command',
    ]

class xupdate_command(object):
    __slots__ = ('namespaces',)


class variable_command(xupdate_command):

    __slots__ = ('name', 'select')

    def __init__(self, namespaces, name, select=None):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # require `name` attribute
        self.name = name
        # optional `select` attribute
        self.select = select
        return


class insert_before_command(xupdate_command):

    __slots__ = ('select',)

    def __init__(self, namespaces, select):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `select` attribute
        self.select = select
        return


class insert_after_command(insert_before_command):
    pass


class append_command(xupdate_command):

    __slots__ = ('select', 'child')

    def __init__(self, namespaces, select, child=None):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `select` attribute
        self.select = select
        # optional `child` attribute
        self.child = child
        return


class update_command(xupdate_command):

    __slots__ = ('select',)

    def __init__(self, namespaces, select):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `select` attribute
        self.select = select
        return


class rename_command(xupdate_command):

    __slots__ = ('select',)

    def __init__(self, namespaces, select):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `select` attribute
        self.select = select
        return


class remove_command(xupdate_command):

    __slots__ = ('select',)

    def __init__(self, namespaces, select):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `select` attribute
        self.select = select
        return

