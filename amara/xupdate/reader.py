########################################################################
# amara/xupdate/reader.py
"""
XUpdate document reader
"""

from amara.xupdate import XUpdateError, XUPDATE_NAMESPACE

class handler(object):

    def startDocument(self):
        self._updates = []
        self._dispatch = {}
        self._new_namespaces = {}

    def startPrefixMapping(self, prefix, uri):
        self._new_namespaces[prefix] = uri

    def startElement(self, expandedName, tagName, attributes):
        parent_state = self._state_stack[-1]
        state = parsestate(**parent_state.__dict__)
        self._state_stack.append(state)

        # ------------------------------------------------------
        # udate in-scope namespaces
        namespaces = state.namespaces
        if self._new_namespaces:
            namespaces = state.namespaces = namespaces.copy()
            namespaces.update(self._new_namespaces)
            self._new_namespaces = {}

        # ------------------------------------------------------
        # get the class defining this element
        namespace, local = expandedName
        if namespace == XUPDATE_NAMESPACE:
            try:
                factory = state.dispatch[local]
            except KeyError:
                raise XUpdateError(XUpdateError.ILLEGAL_ELEMENT,
                                   element=tagName)
        else:
            pass
        return

    def endElement(self, expandedName, tagName):
        return

    def characters(self, data):
        return