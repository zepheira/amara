########################################################################
# amara/writers/xmlwriter.py
"""
XML writer for XSLT output
"""

import operator
import itertools

from amara.lib import xmlstring
from amara.namespaces import XML_NAMESPACE, XMLNS_NAMESPACE
from amara.writers import WriterError, streamwriter
from amara.writers._xmlprinters import xmlprinter, xmlprettyprinter

DEFAULT_GENERATED_PREFIX = u"org.4suite.4xslt.ns"


class xmlwriter(streamwriter):
    """
    Takes events such as those generated by an XSLT processor and
    invokes a serializer to produce XML.
    """
    GENERATED_PREFIX = DEFAULT_GENERATED_PREFIX + "%s"

    _printer = None
    _canonical_form = None
    _need_doctype = True
    _element_name = None
    _element_namespace = None
    _namespaces = None
    _attributes = None

    def _complete_element(self,
                          _value_getter=operator.itemgetter(1),
                          _imap=itertools.imap):
        if self._element_name:
            if self._canonical_form:
                namespaces = sorted(self._namespaces[-1].items())
                attributes = sorted(self._attributes.items())
                attributes = _imap(_value_getter, attributes)
            else:
                namespaces = self._namespaces[-1].iteritems()
                attributes = self._attributes.itervalues()
            # Create a genexp of new namespaces for the printer
            inscope_namespaces = self._namespaces[-2]
            namespaces = ( (prefix, namespace or u'')
                           for prefix, namespace in namespaces
                           if prefix not in inscope_namespaces
                           or inscope_namespaces[prefix] != namespace
                           )
            self._printer.start_element(self._element_namespace,
                                        self._element_name, namespaces,
                                        attributes)

            self._element_name = self._element_namespace = None
            self._attributes = {}
        return

    def start_document(self):
        params = self.output_parameters
        version = params.setdefault('version', '1.0')
        media_type = params.setdefault('media_type', 'text/xml')
        self._canonical_form = params.setdefault('canonical_form', False)
        #FIXME bom and canonical_form not working now
        if self._canonical_form:
            self._need_doctype = False
            if version != '1.0':
                raise WriterError()
            # Override user-supplied values
            encoding = params.encoding = 'UTF-8'
            indent = params.indent = False
            bom = params.byte_order_mark = False
            omit_decl = params.omit_xml_declaration = True
        else:
            encoding = params.setdefault('encoding', 'UTF-8').encode('ascii')
            indent = params.setdefault('indent', False)
            bom = params.byte_order_mark
            omit_decl = params.setdefault('omit_xml_declaration', False)

        if indent:
            printer_class = xmlprettyprinter
        else:
            printer_class = xmlprinter
        #FIXME
        #self._printer = printer_class(self.stream, encoding, bom,
        #                              self._canonical_form)
        self._printer = printer_class(self.stream, encoding)

        if not omit_decl:
            standalone = self.output_parameters.standalone
            if standalone is not None:
                standalone = standalone and 'yes' or 'no'
            self._printer.start_document(version.encode('ascii'), standalone)

        self._namespaces = [{None: None,
                             'xml': XML_NAMESPACE,
                             'xmlns': XMLNS_NAMESPACE}]
        self._attributes = {}
        return

    def end_document(self):
        self._complete_element()
        self._printer.end_document()
        return

    def text(self, data, disable_escaping=False):
        self._complete_element()
        if self._canonical_form:
            data = data.replace('\r\n', '\r')
        self._printer.text(data, disable_escaping)
        return

    def attribute(self, name, value, namespace=None):
        """
        add an attribute to an element

        name - the qualified name of the attribute
        value - the attribute value: must be Unicode
        namespace - must be Unicode or None (the default)

        Strives for "sanity".  For brilliant definition thereof, c.f. Joe English
        http://lists.xml.org/archives/xml-dev/200204/msg00170.html
        Uses terminology from that article
        See also discussions starting
        http://lists.fourthought.com/pipermail/4suite-dev/2003-March/001294.html
        http://lists.fourthought.com/pipermail/4suite-dev/2003-March/001283.html

        Note: attribute output is computed as invoked.
        This means that the ugly case

        attribute(u"foo", u"bar", "http://some-ns/")
        attribute(u"x:foo", u"baz", "http://some-ns/")

        will result in the ugly
          xmlns:org.4suite.4xslt.ns0="http://some-ns/"
          org.4suite.4xslt.ns0:foo="baz"

        The user can easily correct this by reversing the
        order of the calls
        """
        if not self._element_name:
            if self._need_doctype:
                raise WriterError(WriterError.ATTRIBUTE_ADDED_TO_NON_ELEMENT)
            else:
                raise WriterError(WriterError.ATTRIBUTE_ADDED_TOO_LATE)
        prefix, local = xmlstring.splitqname(name)
        if namespace is None:
            name = local
        else:
            # The general approach is as follows:
            # - If the new namespace/prefix combo is unique in the scope, add
            #   it as is.
            #
            # - If the prefix is new, but the namespace already present, avoid
            #   psychosis by reusing the existing namespace (even if it means
            #   putting a formerly prefixed node into defaulted namespace form).
            #   Note that this can cause effective non-conformance in some cases
            #   because the XSLT spec says that all namespace nodes must be
            #   copied to the reslt tree (even if this causes psychosis).
            #   There is no mandate that all ns nodes must be manifestd as
            #   matching NS Decls in the serialization, but if the output is
            #   to result tree fragment, the required ns nodes will simply
            #   disappear.
            #
            # - If the prefix exists, but with a different namespace, generate
            #   a new (and probably rather ugly) prefix.
            namespaces = self._namespaces[-1]
            if not prefix or prefix == 'xmlns':
                # Find an existing namespace/prefix pair
                for prefix, inscope_namespace in namespaces.iteritems():
                    if prefix and inscope_namespace == namespace:
                        break
                else:
                    # Generate a new prefix
                    template = self.GENERATED_PREFIX
                    for suffix in itertools.count():
                        prefix = template % suffix
                        if prefix not in namespaces:
                            break
                    namespaces[prefix] = namespace
            elif prefix not in namespaces:
                # Find an existing namespace/prefix pair
                for inscope_prefix, inscope_namespace in namespaces.iteritems():
                    if inscope_prefix and inscope_namespace == namespace:
                        prefix = inscope_prefix
                        break
                else:
                    # Use given namespace/prefix pair
                    namespaces[prefix] = namespace
            elif namespaces[prefix] != namespace:
                # An existing prefix/namespace pair that doesn't match what
                # we're trying to use. First, try to reuse an existing namespace
                # declaration.
                for prefix, inscope_namespace in namespaces.iteritems():
                    if prefix and inscope_namespace == namespace:
                        break
                else:
                    # Generate a new prefix
                    template = self.GENERATED_PREFIX
                    for suffix in itertools.count():
                        prefix = template % suffix
                        if prefix not in namespaces:
                            break
                    namespaces[prefix] = namespace
            # Generate a new node name
            assert prefix, "'prefix' required for non-null namespace"
            name = prefix + ':' + local

        self._attributes[namespace, local] = (name, value)
        return

    def namespace(self, prefix, namespace):
        namespaces = self._namespaces[-1]
        if prefix not in namespaces:
            if (prefix is not None
                and namespace in namespaces.values()):
                prefix = self.changePrefix(namespace)
            else:
                namespaces[prefix] = namespace
        elif namespaces[prefix] != namespace:
            # An existing prefix/namespace pair that doesn't match what
            # we're trying to use.  Generate a new prefix.
            prefix = self.changePrefix(namespace)
        return

    def processing_instruction(self, target, data):
        self._complete_element()
        # I don't think this is correct per Canonical XML 1.0, but we
        # have a testcase explicitly for WS in data.
        # (http://www.w3.org/TR/xml-c14n#Example-OutsideDoc)
        self._printer.processing_instruction(target, xmlstring.strip(data))
        return

    def comment(self, data):
        self._complete_element()
        self._printer.comment(data)
        return

    def start_element(self, name, namespace=None, namespaces=None,
                      attributes=None):
        """
        attributes must be a mapping from (name, namespace) to value.  namespace can be None
        """
        self._complete_element()

        if self._need_doctype:
            self._printer.doctype(name,
                                    self.output_parameters.doctype_public,
                                    self.output_parameters.doctype_system)
            self._need_doctype = False

        self._element_name = name
        self._element_namespace = namespace
        prefix, local = xmlstring.splitqname(name)

        # Update in-scope namespaces
        inscope_namespaces = self._namespaces[-1].copy()
        if namespaces:
            inscope_namespaces.update(namespaces)
        inscope_namespaces[prefix] = namespace
        self._namespaces.append(inscope_namespaces)
        if attributes:
            for (name, namespace), value in attributes.iteritems():
                self.attribute(name, value, namespace)
        return

    def end_element(self, name, namespace=None):
        self._complete_element()
        self._printer.end_element(namespace, name)
        del self._namespaces[-1]
        return


class cdatasectionwriter(xmlwriter):
    """
    Converts character data to CDATA sections if the character data
    occurs within an element defined as outputting CDATA sections.
    """

    _element_names = ()
    _use_cdata_section = (False,)
    _buffer = None

    def start_document(self):
        xmlwriter.start_document(self)
        self._element_names = self.output_parameters.cdata_section_elements
        self._use_cdata_section = [0]
        self._buffer = []
        return

    def _complete_element(self):
        xmlwriter._complete_element(self)
        if self._use_cdata_section[-1] and self._buffer:
            # Write out queued text
            self._printer.cdata_section(u''.join(self._buffer))
            del self._buffer[:]
        return

    def start_element(self, name, namespace=None, namespaces=None,
                      attributes=None):
        xmlwriter.start_element(self, name, namespace, namespaces, attributes)
        prefix, local = SplitQName(name)
        use_cdata_section = (namespace, local) in self._element_names
        self._use_cdata_section.append(use_cdata_section)
        return

    def end_element(self, name, namespace=None):
        xmlwriter.end_element(self, name, namespace)
        del self._use_cdata_section[-1]
        return

    def text(self, data, disable_escaping=False):
        # Only queue text writes when in a cdata section flagged element
        if self._use_cdata_section[-1]:
            # CDATA Sections do not escape, so no need to save flag
            self._buffer.append(text)
        else:
            xmlwriter.text(self, data, disable_escaping)
        return


from amara.writers import _userwriter

class _xmluserwriter(_userwriter, xmlwriter):
    def __init__(self, oparams, stream):
        xmlwriter.__init__(self, oparams, stream)

