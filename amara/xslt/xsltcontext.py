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
from amara.xpath import context
#from amara.xslt import xsltfunctions, builtinextfunctions, exslt

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
                 mode=None, extmodules=(), extfunctions=None):
        context.__init__(self, node, position, size, variables, namespaces,
                         extmodules, extfunctions)
        self.global_variables = variables
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

    def splitQName(self, qualifiedName):
        if not qualifiedName: return None
        return SplitQName(qualifiedName)

    def expandQName(self, qualifiedName):
        if not qualifiedName: return None
        prefix, local = SplitQName(qualifiedName)
        if prefix:
            try:
                namespace = self.processorNss[prefix]
            except KeyError:
                raise RuntimeException(RuntimeException.UNDEFINED_PREFIX,
                                       prefix)
        else:
            namespace = None
        return (namespace, local)

    def clone(self):
        context = self.__class__(node=self.node,
                                 position=self.position,
                                 size=self.size,
                                 currentNode=self.currentNode,
                                 varBindings=self.varBindings.copy(),
                                 processorNss=self.processorNss,
                                 stylesheet=self.stylesheet,
                                 processor=self.processor,
                                 mode=self.mode)
        context.functions = self.functions
        return context

    def __repr__(self):
        ptr = id(self)
        if ptr < 0:
            ptr += 0x100000000L
        return ('<%s at 0x%x: node %r, position %d, size %d, mode %r>' %
                (self.__class__.__name__, ptr, self.node, self.position,
                 self.size, self.mode))
