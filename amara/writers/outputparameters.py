########################################################################
# amara/writers/outputparameters.py
"""
Represents XSLT output parameters governed by the xsl:output instruction
"""

class outputparameters(object):
    boolean_attribues = [
        'omit_xml_declaration', 'standalone', 'indent', 'byte_order_mark',
        ]
    string_attributes = [
        'method', 'version', 'encoding', 'doctype_system', 'doctype_public',
        'media_type',
        ]
    sequence_attributes = [
        'cdata_section_elements',
        ]
    class __metaclass__(type):
        def __new__(cls, name, bases, members):
            attrs = []
            if 'boolean_attribues' in members:
                attrs += members['boolean_attribues']
            if 'string_attributes' in members:
                attrs += members['string_attributes']
            if 'sequence_attributes' in members:
                attrs += members['sequence_attributes']
            members['__slots__'] = tuple(attrs)
            return type.__new__(cls, name, bases, members)

    def __init__(self, method=None, version=None, encoding=None,
                 omit_xml_declaration=None, standalone=None,
                 doctype_public=None, doctype_system=None,
                 cdata_section_elements=(), indent=None, media_type=None,
                 byte_order_mark=None):
        self.method = method
        self.version = version
        self.encoding = encoding
        self.omit_xml_declaration = omit_xml_declaration
        self.standalone = standalone
        self.doctype_public = doctype_public
        self.doctype_system = doctype_system
        if cdata_section_elements:
            cdata_section_elements = tuple(cdata_section_elements)
        self.cdata_section_elements = cdata_section_elements
        self.indent = indent
        self.media_type = media_type
        self.byte_order_mark = byte_order_mark

    def clone(self):
        attrs = {}
        for name in self.__slots__:
            value = getattr(self, name)
            if value is not None:
                attrs[name] = value
                setattr(clone, name, value)
        return self.__class__(**attrs)

    def setdefault(self, attr, value):
        if getattr(self, attr) is None:
            setattr(self, attr, value)
        return
