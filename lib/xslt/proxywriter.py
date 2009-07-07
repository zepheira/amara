########################################################################
# amara/xslt/proxywriter.py
"""
Manages XSLT output parameters governed by the xsl:output instruction.
See also `amara.writers.outputparameters`.
"""

import new
import weakref
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

class proxymethod(object):
    __slots__ = ('_name', '_func', '_refs')
    def __init__(self, func):
        self._name = func.__name__
        self._func = func
        self._refs = []

    def update(self, obj, cls,
               _instancemethod=new.instancemethod,
               _members=operator.attrgetter('im_func', 'im_self', 'im_class',
                                             '__call__')):
        func = getattr(obj, self._name)
        try:
            func  = func.im_func
        except AttributeError:
            for ref in self._refs:
                proxy = ref()
                if proxy and proxy.im_self is obj:
                    class proxyfunction(object):
                        __call__ = func.__call__
                    proxy.__class__ = proxyfunction
        else:
            for ref in self._refs:
                proxy = ref()
                if proxy and proxy.im_self is obj:
                    method = _instancemethod(func, obj, cls)
                    class proxymethod(object):
                        im_func, im_self, im_class, __call__ = _members(method)
                    proxy.__class__ = proxymethod

    def __get__(self, obj, cls,
                _instancemethod=new.instancemethod,
                _members=operator.attrgetter('im_func', 'im_self', 'im_class',
                                             '__call__')):
        method = _instancemethod(self._func, obj, cls)
        class proxymethod(object):
            im_func, im_self, im_class, __call__ = _members(method)
        proxy = proxymethod()
        self._refs.append(weakref.ref(proxy, self._refs.remove))
        return proxy


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
    def _lookup(cls, output_parameters):
        method = output_parameters.method
        try:
            cls = cls._methods[method]
        except KeyError:
            if method[0] is None:
                # display only localName if in the null namespace
                method = method[1]
            raise XsltError(XsltError.UNKNOWN_OUTPUT_METHOD, str(method))
        if (cls is xmlwriter.xmlwriter and
            output_parameters.cdata_section_elements):
            cls = xmlwriter.cdatasectionwriter
        return cls

    def __new__(cls, output_parameters, stream):
        # Attempt to switch to the "true" writer as soon as possible
        if output_parameters.method:
            return cls._lookup(output_parameters)(output_parameters, stream)
        return object.__new__(cls)

    def __init__(self, output_parameters, stream):
        streamwriter.__init__(self, output_parameters, stream)
        self._stack = []
        return

    def _finalize(self, method):
        self.output_parameters.setdefault('method', method)
        writer_class = self._lookup(self.output_parameters)
        # Save our instance variables for use after reinitializing
        stack = self._stack
        del self._stack

        self.__class__ = writer_class
        for proxy in proxywriter.__proxymethods__:
            proxy.update(self, writer_class)

        # Do the saved callbacks
        get_command = self.__getattribute__
        for cmd, args, kw in stack:
            get_command(cmd)(*args, **kw)
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
