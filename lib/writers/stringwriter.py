########################################################################
# amara/xslt/stringwriter.py
"""
A specialized XSLT output writer that only captures text output events

Copyright 2005 Fourthought, Inc. (USA).
Detailed license and copyright information: http://4suite.org/COPYRIGHT
Project home, documentation, distributions: http://4suite.org/
"""

from amara.writers import writer

class stringwriter(writer):

    _result = u''

    def __init__(self, parameters, errors=True):
        writer.__init__(self, parameters)
        self._errors = errors

    def start_document(self):
        self._data = []

    def end_document(self):
        self._result = u''.join(self._data)

    def get_result(self):
        return self._result

    def text(self, data, disable_escaping=False):
        self._data.append(data)
        return

    def start_element(self, name, namespace=None, namespaces=None,
                      attributes=None):
        if self._errors:
            raise RuntimeError("cannot create 'element' nodes")

    def end_element(self, name, namespace=None):
        if self._errors:
            raise RuntimeError("cannot create 'element' nodes")

    def namespace(self, prefix, namespace):
        if self._errors:
            raise RuntimeError("cannot create 'namespace' nodes")

    def attribute(self, name, value, namespace=None):
        if self._errors:
            raise RuntimeError("cannot create 'attribute' nodes")

    def processingInstruction(self, target, data):
        if self._errors:
            raise RuntimeError("cannot create 'processing-instruction' nodes")

    def comment(self, body):
        if self._errors:
            raise RuntimeError("cannot create 'comment' nodes")
