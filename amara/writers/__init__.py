########################################################################
# amara/writers/__init__.py

class writer(object):
    # Note, any changes to __slots__ require a change in treewriter.c as well
    __slots__ = ('output_parameters',)

    class __metaclass__(type):
        def __init__(cls, name, bases, members):
            if 'characters' in members:
                if 'text' not in members:
                    cls.text = cls.characters
            elif 'text' in members:
                if 'characters' not in members:
                    cls.characters = cls.text

    def __init__(self, output_parameters):
        self.output_parameters = output_parameters

    def get_result(self):
        return None

    def start_document(self):
        """
        Called once at the beginning of output writing.
        """
        return

    def end_document(self):
        """
        Called once at the end of output writing.
        """
        return

    def start_element(self, name, namespace=None, namespaces=None,
                      attributes=None):
        """
        Called when an element node is generated in the result tree.
        Subsequent method calls generate the element's attributes and content.

        name - the local name.
        namespace - the namespace URI.
        namespaces - new namespace bindings (dictionary of prefixes to URIs)
                     established by this element.
        attributes - mapping of qualified-name to attribute-value
        """
        return

    def end_element(self, name, namespace=None):
        """
        Called at the end of element node generation.

        name - the local name.
        namespace - the namespace URI.
        """
        return

    def namespace(self, prefix, namespace):
        """
        Called when a namespace node is explicitly generated in the result tree
        (as by the xsl:namespace instruction).

        prefix - the prefix.
        namespace - the namespace URI.
        """
        return

    def attribute(self, name, value, namespace=None):
        """
        Called when an attribute node is generated in the result tree.

        name - the local name.
        value - the attribute value.
        namespace - the namespace URI.
        """
        return

    def characters(self, data, disable_escaping=False):
        """
        Called when a text node is generated in the result tree.

        data - content of the text node
        disable_escaping - if true, no escaping of characters is performed
        """
        return

    def processing_instruction(self, target, data):
        """
        Called when an processing instruction node is generated in the result tree.

        target - the instruction target.
        data - the instruction.
        """
        return

    def comment(self, body):
        """
        Called when a comment node is generated in the result tree.

        body - comment text.
        """
        return
