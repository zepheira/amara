########################################################################
# amara/xupdate/commands.py
"""
XUpdate request processing
"""

from amara.xupdate import XUpdateError

__all__ = [
    'insert_before_command', 'insert_after_command', 'append_command',
    'update_command', 'rename_command', 'remove_command',
    'variable_command', 'if_command'
    ]


class modifications_list(list):
    # Note, no need to call `list.__init__` if there are no initial
    # items to be added. `list.__new__` takes care of the setup for
    # new empty lists.
    def __repr__(self):
        return '<modifications: %s>' % list.__repr__(self)


class xupdate_command(list):
    __slots__ = ('namespaces',)


class insert_before_command(xupdate_command):
    __slots__ = ('select',)
    def __init__(self, namespaces, select):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `select` attribute
        self.select = select
        return

    def __repr__(self):
        return '<insert-before: %s>' % xupdate_command.__repr__(self)


class insert_after_command(xupdate_command):
    __slots__ = ('select',)
    def __init__(self, namespaces, select):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `select` attribute
        self.select = select
        return

    def __repr__(self):
        return '<insert-after: %s>' % xupdate_command.__repr__(self)


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

    def __repr__(self):
        return '<append: %s>' % xupdate_command.__repr__(self)


class update_command(xupdate_command):
    __slots__ = ('select',)
    def __init__(self, namespaces, select):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `select` attribute
        self.select = select
        return

    def __repr__(self):
        return '<update: %s>' % xupdate_command.__repr__(self)


class rename_command(xupdate_command):
    __slots__ = ('select',)
    def __init__(self, namespaces, select):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `select` attribute
        self.select = select
        return

    def __repr__(self):
        return '<rename: %s>' % xupdate_command.__repr__(self)


class remove_command(xupdate_command):
    __slots__ = ('select',)
    def __init__(self, namespaces, select):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # required `select` attribute
        self.select = select
        return

    def __repr__(self):
        return '<remove select=%s>' % (self.select,)


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

    def __repr__(self):
        return '<variable: %s>' % xupdate_command.__repr__(self)


class if_command(xupdate_command):
    __slots__ = ('test',)
    def __init__(self, namespaces, test):
        # save in-scope namespaces for XPath
        self.namespaces = namespaces
        # require `test` attribute
        self.test = test
        return

    def __repr__(self):
        return '<if: %s>' % xupdate_command.__repr__(self)
