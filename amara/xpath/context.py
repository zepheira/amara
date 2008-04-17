########################################################################
# amara/xpath/context.py
"""
The context of an XPath expression
"""

import types

from amara import XML_NAMESPACE
from amara.xpath import extensions

__all__ = ['xpathcontext']

class xpathcontext:
    functions = extensions.extension_functions
    currentInstruction = None

    def __init__(self, node, position=1, size=1,
                 variables=None, namespaces=None,
                 extmodules=(), extfunctions=None):
        self.node, self.position, self.size = node, position, size
        self.variables = variables or {}
        self.namespaces = {'xml': XML_NAMESPACE}
        if namespaces:
            self.namespaces.update(namespaces)

        # This may get mutated during processing
        self.functions = self.functions.copy()
        # Search the extension modules for defined functions
        for module in extmodules:
            if module:
                if not isinstance(module, types.ModuleType):
                    module = __import__(module, {}, {}, ['ExtFunctions'])
                funcs = getattr(module, 'extension_functions', None)
                if funcs:
                    self.functions.update(funcs)
        # Add functions given directly
        if extfunctions:
            self.functions.update(extfunctions)
        return

    def __repr__(self):
        ptr = id(self)
        if ptr < 0: ptr += 0x100000000L
        return "<Context at 0x%x: Node=%s, Postion=%d, Size=%d>" % (
            ptr, self.node, self.position, self.size)

    def addFunction(self, expandedName, function):
        if not callable(function):
            raise TypeError("function must be a callable object")
        self.functions[expandedName] = function
        return

    def copy(self):
        return (self.node, self.position, self.size)

    def set(self, state):
        self.node, self.position, self.size = state
        return

    def clone(self):
        newobj = self.__class__(self, self.node, self.position, self.size)
        newobj.variables = self.variables.copy()
        newobj.namespaces = self.namespaces.copy()
        return newobj

