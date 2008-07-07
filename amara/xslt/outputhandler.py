########################################################################
# amara/xslt/outputhandler.py
"""
Manages XSLT output parameters governed by the xsl:output instruction
See also Ft.Xml.Xslt.OutputParameters

Copyright 2004 Fourthought, Inc. (USA).
Detailed license and copyright information: http://4suite.org/COPYRIGHT
Project home, documentation, distributions: http://4suite.org/
"""

from amara.namespaces import EXTENSION_NAMESPACE
from amara.writers import writer, textwriter, htmlwriter, xmlwriter
from amara.xslt import XsltError


_TEXT_METHOD = (None, 'text')
_HTML_METHOD = (None, 'html')
_XML_METHOD = (None, 'xml')
_XHTML_METHOD = (EXTENSION_NAMESPACE, 'xhtml') #Coming later
_C14N_METHOD = (EXTENSION_NAMESPACE, 'c14n') #Coming later

class output_handler(writer):

    _methods = {
        _TEXT_METHOD : textwriter.textwriter,
        _HTML_METHOD : htmlwriter.htmlwriter,
        _XML_METHOD : xmlwriter.xmlwriter,
        }

    def __init__(self, outputParams, stream, notifyFunc=None):
        nullwriter.null_writer.__init__(self, outputParams)
        self._stream = stream
        self._stack = []
        return

    def _finalize(self, method):
        try:
            writerClass = self._methods[method]
        except KeyError:
            if method[0] is None:
                # display only localName if in the null namespace
                method = method[1]
            raise XsltError(XsltError.UNKNOWN_OUTPUT_METHOD, str(method))
        else:
            self._outputParams.setDefault('method', method)

        if writerClass is xmlwriter.xml_writer and \
               self._outputParams.cdataSectionElements:
            writerClass = xmlwriter.cdata_section_xml_writer
        # Save our instance variables for use after reinitializing
        stream, stack = self._stream, self._stack
        del self._stream
        del self._stack
        self.__class__ = writer_class
        writerClass.__init__(self, self._outputParams, stream)

        # Do the saved callbacks
        self.startDocument()
        newline = 0
        for cmd, args, kw in stack:
            if newline:
                self.text(u'\n')
            else:
                newline = 1
            getattr(self, cmd)(*args, **kw)
        return

    def getStream(self):
        return self._stream

    def getResult(self):
        return ''

    def startDocument(self):
        method = self._outputParams.method
        if method:
            self._finalize(method)
        return

    def endDocument(self, *args, **kw):
        # We haven't chosen an output method yet, use default.
        self._stack.append(('endDocument', args, kw))
        self._finalize(_XML_METHOD)
        return

    def text(self, *args, **kw):
        self._stack.append(('text', args, kw))
        # Non-whitespace characters, cannot be HTML/XHTML
        if not IsXmlSpace(args[0]):
            self._finalize(_XML_METHOD)
        return

    def processingInstruction(self, *args, **kw):
        self._stack.append(('processingInstruction', args, kw))
        return

    def comment(self, *args, **kw):
        self._stack.append(('comment', args, kw))
        return

    def startElement(self, name, namespace=None, *args, **kw):
        self._stack.append(('startElement', (name, namespace) + args, kw))
        if name.lower() == 'html' and namespace is EMPTY_NAMESPACE:
            self._finalize(_HTML_METHOD)
        else:
            self._finalize(_XML_METHOD)
        return
