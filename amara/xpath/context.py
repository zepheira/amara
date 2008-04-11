########################################################################
# amara/xpath/context.py
"""
The context of an XPath expression
"""

from amara import XML_NAMESPACE
from types import ModuleType

import CoreFunctions, BuiltInExtFunctions

__all__ = ['xpathcontext']

class xpathcontext:
    functions = functions.builtin_functions.copy()
    functions.update(extensions.ext_functions)
    currentInstruction = None

    def __init__(self,
                 node,
                 position=1,
                 size=1,
                 variables=None,
                 namespaces=None,
                 extModuleList=None,
                 extFunctionMap=None):
        self.node = node
        self.position = position
        self.size = size
        self.variables = variables or {}
        self.namespaces = {'xml': XML_NAMESPACE}
        if namespaces:
            self.namespaces.update(namespaces)

        # This may get mutated during processing
        functions = dict(self.functions)

        # Search the extension modules for defined functions
        if extModuleList:
            for module in extModuleList:
                if module:
                    if not isinstance(module, ModuleType):
                        module = __import__(module, {}, {}, ['ExtFunctions'])

                    if hasattr(module, 'ExtFunctions'):
                        functions.update(module.ExtFunctions)

        # Add functions given directly
        if extFunctionMap:
            functions.update(extFunctionMap)
        self.functions = functions
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

