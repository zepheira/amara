########################################################################
# amara/xupdate/writers.py
"""
XUpdate output writers
"""

class text_writer(object):
    __slots__ = ('_data', '_write')
    def __init__(self):
        self._data = []
        self._write = self._data.append

    def get_result(self):
        return u''.join(self._data)

    def start_element(self, namespace, name, attributes=()):
        pass

    def end_element(self, namespace, name):
        pass

    def attribute(self, namespace, name, value):
        pass

    def text(self, data):
        self._write(data)

    def processing_instruction(self, target, data):
        pass

    def comment(self, data):
        pass


class node_writer(object):
    __slots__ = ()
    def __init__(self, parent, refnode=None):
        self._parent = parent
        #FIXME: Use regular constructor. No more DOM factory
        self._factory = parent.rootNode
        self._nodes = []
        self._last = parent

    def get_result(self):
        return self._nodes

    def start_element(self, namespace, name, attributes=()):
        pass

    def end_element(self, namespace, name):
        node = self._nodes[-1]

    def attribute(self, namespace, name, value):
        try:
            self._last.xml_attributes[namespace, name] = value
        except AttributeError:
            raise XUpdateError(XUpdateError.ATTRIBUTE_NOT_ALLOWED)

    def text(self, data):
        if self._last.nodeType == Node.TEXT_NODE:
            self._last.appendData(data)
        else:
            node = self._last = self._factory.createTextNode(data)
            self._nodes.append(node)

    def processing_instruction(self, target, data):
        pass

    def comment(self, data):
        pass
