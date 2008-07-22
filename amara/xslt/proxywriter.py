########################################################################
# amara/xslt/proxywriter.py
"""
Manages XSLT output parameters governed by the xsl:output instruction.
See also `amara.writers.outputparamters`.
"""

import new
import operator

from amara.namespaces import EXTENSION_NAMESPACE
from amara.lib.xmlstring import isspace
from amara.writers import streamwriter, textwriter, htmlwriter, xmlwriter
from amara.xslt import XsltError


_TEXT_METHOD = (None, 'text')
_HTML_METHOD = (None, 'html')
_XML_METHOD = (None, 'xml')
_XHTML_METHOD = (EXTENSION_NAMESPACE, 'xhtml') #Coming later
_C14N_METHOD = (EXTENSION_NAMESPACE, 'c14n') #Coming later

def proxymethod_wrapper(func, obj, cls,
                _instancemethod=new.instancemethod,
                _members=operator.attrgetter('im_func', 'im_self', 'im_class',
                                             '__call__')):
    method = _instancemethod(func, obj, cls)
    class proxymethod(object):
        im_func, im_self, im_class, __call__ = _members(method)
    return proxymethod()


class proxymethod(object):
    __slots__ = ('_name', '_func', '_refs')
    def __init__(self, func):
        self._name = func.__name__
        self._func = func
        self._refs = []

    def update(self, obj, cls):
        func = getattr(obj, self._name)
        try:
            func  = func.im_func
        except AttributeError:
            for ref in self._refs:
                if ref.im_self is obj:
                    class proxyfunction(object):
                        __call__ = func.__call__
                    ref.__class__ = proxyfunction
        else:
            for ref in self._refs:
                if ref.im_self is obj:
                    ref.__class__ = proxymethod_wrapper(func, obj, cls)

    def __get__(self, obj, cls):
        method = proxymethod_wrapper(self._func, obj, cls)
        self._refs.append(weakref.proxy(method, self._refs.remove))
        return method


class proxywriter(streamwriter):

    _methods = {
        _TEXT_METHOD : textwriter.textwriter,
        _HTML_METHOD : htmlwriter.htmlwriter,
        _XML_METHOD : xmlwriter.xmlwriter,
        }

    class __metaclass__(type):
        def __init__(cls, name, bases, namespace):
            cls.__proxymethods__ = tuple(
                obj for obj in namespace.itervalues()
                if isinstance(obj, proxymethod))

    @classmethod
    def _lookup(cls, output_paramters):
        method = output_paramters.method
        if method is not None:
            try:
                cls = cls._methods[method]
            except KeyError:
                if method[0] is None:
                    # display only localName if in the null namespace
                    method = method[1]
                raise XsltError(XsltError.UNKNOWN_OUTPUT_METHOD, str(method))
            if (cls is xmlwriter.xmlwriter and
                output_paramters.cdata_section_elements):
                cls = xmlwriter.cdatasectionwriter
        return cls

    def __new__(cls, output_paramters, stream):
        # Attempt to switch to the "true" writer as soon as possible
        cls = cls._lookup(output_paramters)
        return streamwriter.__new__(cls, output_paramters, stream)

    def __init__(self, output_paramters, stream):
        streamwriter.__init__(self, output_paramters, stream)
        self._stack = []
        return

    def _finalize(self, method):
        self.output_paramters.setdefault('method', method)
        writer_class = self._lookup(self.output_paramters)
        # Save our instance variables for use after reinitializing
        stack = self._stack
        del self._stack

        self.__class__ = writer_class
        for proxy in proxywriter.__proxymethods__:
            proxy.update(self, writer_class)

        # Do the saved callbacks
        newline = 0
        for cmd, args, kw in stack:
            if newline:
                self.text(u'\n')
            else:
                newline = 1
            getattr(self, cmd)(*args, **kw)
        return

    @proxymethod
    def start_document(self, *args, **kwds):
        self._stack.append(('start_document', args, kwds))
        return

    @proxymethod
    def end_document(self, *args, **kw):
        # We haven't chosen an output method yet, use default.
        self._stack.append(('end_document', args, kw))
        self._finalize(_XML_METHOD)
        return

    @proxymethod
    def start_element(self, name, namespace=None, *args, **kw):
        self._stack.append(('start_element', (name, namespace) + args, kw))
        if namespace is None and name.lower() == 'html':
            self._finalize(_HTML_METHOD)
        else:
            self._finalize(_XML_METHOD)
        return

    @proxymethod
    def end_element(self, *args, **kw):
        self._stack.append(('end_element', args, kw))
        return

    @proxymethod
    def namespace(self, *args, **kw):
        self._stack.append(('namespace', args, kw))
        return

    @proxymethod
    def attribute(self, *args, **kw):
        self._stack.append(('attribute', args, kw))
        return

    @proxymethod
    def text(self, *args, **kw):
        self._stack.append(('text', args, kw))
        # Non-whitespace characters, cannot be HTML/XHTML
        if not isspace(args[0]):
            self._finalize(_XML_METHOD)
        return

    @proxymethod
    def processing_instruction(self, *args, **kw):
        self._stack.append(('processing_instruction', args, kw))
        return

    @proxymethod
    def comment(self, *args, **kw):
        self._stack.append(('comment', args, kw))
        return
