########################################################################
# amara/writers/__init__.py

import sys
from amara import Error
from amara.lib.xmlstring import *

__all__ = ['WriterError', 'writer', 'streamwriter']

class WriterError(Error):

    ATTRIBUTE_ADDED_TOO_LATE = 1
    ATTRIBUTE_ADDED_TO_NON_ELEMENT = 2

    @classmethod
    def _load_messages(cls):
        from gettext import gettext as _
        return {
            WriterError.ATTRIBUTE_ADDED_TOO_LATE: _(
                'Children were added to the element'),
            WriterError.ATTRIBUTE_ADDED_TO_NON_ELEMENT: _(
                'Attempted to add attribute to non-element'),
        }


class writer(object):
    # Note, any changes to __slots__ require a change in treewriter.c as well
    __slots__ = ('output_parameters',)

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

    def text(self, data, disable_escaping=False):
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


class streamwriter(writer):

    def __init__(self, output_parameters, stream):
        """
        output_parameters - instance of
                            `amara.writers.outputparameters.outputparameters`
        stream - a stream that takes a byte stream (not a unicode object)
        """
        self.output_parameters = output_parameters
        self.stream = stream


class _userwriter(object):
    def start_element(self, name, namespace=None, namespaces=None,
                      attributes=None):
        """
        Create a start tag with optional attributes.  Must eventually
        be matched with an endElement call
        
        Note: all "strings" in these parameters must be unicode objects
        name - qualified name of the element (must be unicode)
        namespace - optional namespace URI
        attributes - optional dictionary mapping name to unicode value
                    the name can either be a unicode QName or a tuple
                    of (QName, namespace URI)
        namespaces - optional dictionary (defaults to an empty one) that
                   creates additional namespace declarations that the
                   user wants to place on the specific element. Each key
                   is a ns prefix, and each value a ns name (URI).
                   You do not need to use extraNss if you will be using
                   a similar namespace parameter.  In fact, most people
                   will never need this parameter.
        """
        name = U(name)
        normalized_attrs = {}
        if attributes is not None:
            normalized_attrs = dict((
                (((U(aname[0]), U(aname[1])), U(value))
                    if isinstance(aname, tuple) else ((U(aname), None), U(value)))
                for (aname, value) in attributes.iteritems()
            ))
        #Be careful, viz. http://fuhm.net/super-harmful/ but should be safe here
        super(_userwriter, self).start_element(name, namespace, namespaces, normalized_attrs)
        return

    def simple_element(self, name, namespace=None, namespaces=None,
                      attributes=None, content=u""):
        """
        Create a simple tag with optional attributes and content.  The
        complete element, start tag, optional text content, end tag, will
        all be generated by this one call.  Must *not* be matched with
        an endElement call.

        Note: all "strings" in these parameters must be unicode objects
        tagName - qualified name of the element
        namespace - optional namespace URI
        attributes - optional dictionary mapping name to unicode value
                    the name can either be a unicode QName or a tuple
                    of (QName, namespace URI)
        content   - optional unicode object with the text body of the
                    simple element
        namespaces - optional dictionary (defaults to an empty one) that
                   creates additional namespace declarations that the
                   user wants to place on the specific element. Each key
                   is a ns prefix, and each value a ns name (URI).
                   You do not need to use namespaces if you will be using
                   a similar namespace parameter.  In fact, most people
                   will never need this parameter.
        """
        if name.startswith('xml:'):
            #We can use such a raw test because of the very special case
            #nature of the XML prefix
            namespace = XML_NAMESPACE
        self.start_element(name, namespace, namespaces, attributes)
        if content:
            self.text(U(content))
        self.end_element(name, namespace)
        return

    def xml_fragment(self, fragment):
        """
        Incorporate a well-formed general entity into the output.
        fragment of
        fragment - string (must not be a Unicode object) to be incorporated
                   verbatim into the output, after testing for wellp-formedness
        """
        raise NotImplementedErr
