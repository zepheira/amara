########################################################################
# amara/xslt/xsltcontext.py
"""
Context and state information for XSLT processing

Copyright 2006 Fourthought, Inc. (USA).
Detailed license and copyright information: http://4suite.org/COPYRIGHT
Project home, documentation, distributions: http://4suite.org/
"""

from amara._xmlstring import splitqname
from amara.lib.iri import uridict
from amara.xpath import XPathError, context
#from amara.xslt import xsltfunctions, builtinextfunctions, exslt

try:
    import ctypes
except ImportError:
    def dictproxy(dict):
        return dict
else:
    dictproxy = ctypes.pythonapi.PyDictProxy_New
    dictproxy.restype = ctypes.py_object
    dictproxy.argtypes = (ctypes.py_object,)

__all__ = ['xsltcontext']

class xsltcontext(context):

    functions = context.functions.copy()
    #functions.update(xsltfunctions.corefunctions)
    #functions.update(exslt.extfunctions)
    #functions.update(builtinextfunctions.extfunctions)

    instruction = None
    template = None
    recursive_parameters = None

    def __init__(self, node, position=1, size=1,
                 variables=None, namespaces=None,
                 current_node=None, transform=None, processor=None,
                 mode=None, extmodules=(), extfunctions=None,
                 output_parameters=None):
        context.__init__(self, node, position, size, variables, namespaces,
                         extmodules, extfunctions, output_parameters)
        self.global_variables = dictproxy(self.variables)
        self.current_node = current_node
        self.transform = transform
        self.processor = processor
        self.mode = mode
        self.documents = uridict()
        return

    def get(self):
        return self._current_instruction
    def set(self, value):
        self._current_instruction = value
        self.namespaces = value.namespaces
    current_instruction = property(get, set)
    del get, set

    def add_document(self, document, document_uri=None):
        # RTF documents do not have a documentUri
        if document_uri:
            self.documents[document_uri] = document
        return

    def message(self, message):
        self.processor.message(message)

    def expandname(self, name):
        if not name: return None
        prefix, name = splitqname(name)
        if prefix:
            try:
                namespace = self.namespaces[prefix]
            except KeyError:
                raise XPathError(XPathError.UNDEFINED_PREFIX, prefix=prefix)
        else:
            namespace = None
        return (namespace, name)

    def __repr__(self):
        ptr = id(self)
        if ptr < 0:
            ptr += 0x100000000L
        return ('<%s at 0x%x: node %r, position %d, size %d, mode %r>' %
                (self.__class__.__name__, ptr, self.node, self.position,
                 self.size, self.mode))
