__all__ = [
'binder', 'TOP', 'ANY_NAMESPACE', 'REMOVE_RULE',
'PY_REPLACE_PAT', 'RESERVED_NAMES'
]

from xml import Node
from amara import _domlette
import re
import sets
import itertools
import keyword
import warnings
import cStringIO
import bisect

#Only need to list IDs that do not start with "xml", "XML", etc.
RESERVED_NAMES = [
    '__class__', '__delattr__', '__dict__', '__doc__', '__getattribute__',
    '__getitem__', '__hash__', '__init__', '__iter__', '__module__',
    '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__',
    '__str__', '__unicode__', '__weakref__', '_childNodes', '_docIndex',
    '_localName', '_namespaceURI', '_parentNode', '_prefix', '_rootNode',
    'childNodes', 'docIndex', 
    'localName', 'namespaceURI', 'next_elem', 'nodeName', 'nodeType',
    'ownerDocument', 'parentNode', 'prefix', 'rootNode', 'locals',
    'None'
    ]

RESERVED_NAMES = frozenset(itertools.chain(keyword.kwlist, RESERVED_NAMES))

ANY_NAMESPACE = 'http://purl.xml3k.org/amara/reserved/any-namespace'

class element_iterator:
    def __init__(self, start):
        self.curr = start
        return

    def __iter__(self):
        return self

    def next(self):
        if not self.curr:
            raise StopIteration()
        result = self.curr
        if self.curr.xml_next_elem is not None:
            self.curr = self.curr.xml_next_elem
        else:
            self.curr = None
        return result


class default_container_node(object):
    def is_attribute(self, pyname):
        #Only elements can have attributes.  element_base overrides to check
        return False

    #Mutation
    def xml_clear(self):
        "Remove all children"
        #Tempting to do
        #for c in self.xml_children: self.xml_remove_child(c)
        #But that would just be a pig
        self.xml_children = []
        delete_attrs = []
        for attr in self.__dict__:
            if not (attr in self.xml_ignore_members or attr.startswith('xml')):
                if getattr(self.__dict__[attr], 'next_elem', None):
                    delete_attrs.append(attr)
        for attr in delete_attrs:
            #Does not unlink all the way down the next_elem chain,
            #But GC should take care of them once the first is unlinked
            del self.__dict__[attr]
        return

    def xml_append(self, new):
        """
        Append element or text
        Returns the added child
        """
        if isinstance(new, unicode):
            self.xml_children.append(new)
        elif new.nodeType == Node.ELEMENT_NODE:
            bind_instance(new, self)
        elif hasattr(new, 'nodeType'):
            new.xml_parent = self
            self.xml_children.append(new)
        return new

    def xml_insert_after(self, ref, new):
        """
        Insert an object (element or text) after another child
        ref - the existing child that marks the position for insert
        new - the new child to be inserted
        Returns the added child
        """
        index = self.xml_children.index(ref)+1
        if isinstance(new, unicode):
            self.xml_children[index:index] = [new]
        elif new.nodeType == Node.ELEMENT_NODE:
            bind_instance(new, self, index)
        elif hasattr(new, 'nodeType'):
            new.xml_parent = self
            self.xml_children[index:index] = [new]
        return new

    def xml_insert_before(self, ref, new):
        """
        Insert an object (element or text) before another child
        ref - the existing child that marks the position for insert
        new - the new child to be inserted
        Returns the added child
        """
        index = self.xml_children.index(ref)
        if isinstance(new, unicode):
            self.xml_children[index:index] = [new]
        elif new.nodeType == Node.ELEMENT_NODE:
            bind_instance(new, self, index)
        elif hasattr(new, 'nodeType'):
            new.xml_parent = self
            self.xml_children[index:index] = [new]
        return new

    def xml_append_fragment(self, text, encoding=None):
        """
        Append chunk of literal XML to the children of the node instance
        text - string (not Unicode, since this is a parse operation) fragment
               of literal XML to be parsed.  This XML fragment must be
               a well-formed external parsed entity.  Basically, multiple
               root elements are allowed, but they must be properly balanced,
               special characters escaped, and doctype declaration is
               prohibited.  According to XML rules, the encoded string is
               assumed to be UTF-8 or UTF-16, but you can override this with
               an XML text declaration ('<?xml version="1.0" encoding="ENC"?>')
               or by passing in an encoding parameter to this function.
        encoding - optional string with the encoding to be used in parsing the
               XML fragment.  Default to the standard XML rules (i.e. UTF-8,
               UTF-16, or any encoding specified in text declaration).  If this
               parameter is specified, it overrrides any text declaration in
               the XML fragment.
        """
        from Ft.Xml.Domlette import EntityReader, GetAllNs, ParseFragment
        from Ft.Xml import Sax, InputSource
        #if encoding:
            #text = '<?xml version="1.0" encoding="%s"?>'%(encoding) + text
        isrc = InputSource.DefaultFactory.fromString(text, 'urn:x-amara:amara-xml-template')
        if encoding:
            isrc.encoding = encoding
        nss = self.rootNode.xmlns_prefixes
        nss.update(GetAllNs(self))
        docfrag = ParseFragment(isrc, nss)
        def walk_domlette(node, target):
            if node.nodeType == Node.ELEMENT_NODE:
                attrs = {}
                for attr in node.xpathAttributes:
                    attrs[(attr.nodeName, attr.namespaceURI)] = attr.value
                elem = target.xml_create_element(qname=node.nodeName, ns=node.namespaceURI, attributes=attrs)
                target.xml_append(elem)
                for child in node.childNodes:
                    walk_domlette(child, elem)
            elif node.nodeType == Node.TEXT_NODE:
                target.xml_append(node.data)
            else:
                for child in node.childNodes:
                    walk_domlette(child, target)
            return
        walk_domlette(docfrag, self)
        return

    def xml_create_element(self, qname, ns=None, content=None, attributes=None):
        "Create a new, empty element (no attrs)"
        instance = create_element(self.xml_naming_rule, qname, ns)
        if content:
            if not isinstance(content, list):
                content = [ content ]
            instance.xml_children = content
        if attributes:
            instance.xml_attributes = {}
            for aname in attributes:
                if isinstance(aname, tuple):
                    aqname, ans = aname
                else:
                    aqname, ans = aname, None
                avalue = attributes[aname]
                apyname = self.xml_naming_rule.xml_to_python(
                    SplitQName(aqname)[1], ans,
                    check_clashes=dir(instance))
                #Bypass __setattr__
                instance.__dict__[apyname] = avalue
                instance.xml_attributes[apyname] = (aqname, ans)
        return instance    

    def xml_remove_child(self, obj):
        """
        Remove the child equal to the given object
        obj - any object valid as a bound element child
        returns the removed child
        """
        index = self.xml_children.index(obj)
        return self.xml_remove_child_at(index)

    def xml_remove_child_at(self, index=-1):
        """
        Remove child object at a given index
        index - optional, 0-based index of child to remove (defaults to the last child)
        returns the removed child
        """
        obj = self.xml_children[index]
        if isinstance(obj, unicode):
            removed = self.xml_children[index]
            del self.xml_children[index]
        else:
            #Remove references to the object
            #Probably a slow way to go about this
            for attr, val in self.__dict__.items():
                if not (attr.startswith('xml') or attr in self.xml_ignore_members):
                    next = getattr(val, 'next_elem', None)
                    if val == obj:
                        del self.__dict__[attr]
                        if next: self.__dict__[attr] = next
                        break
                    while next:
                        prev, val = val, next
                        next = getattr(val, 'next_elem', None)
                        if val == obj:
                            prev.next_elem = next
                            break
            removed = self.xml_children[index]
            del self.xml_children[index]
        return removed

    @property
    def xml_properties(self):
        """
        Return a dictionary whose keys are Python properties on this
        object that represent XML attributes and elements, and whose vaues
        are the corresponding objects (a subset of __dict__)
        """
        properties = {}
        for attr in self.__dict__:
            if (not (attr.startswith('xml')
                or attr in self.xml_ignore_members)):
                properties[attr] = self.__dict__[attr]
        return properties

    @property
    def xml_child_elements(self):
        child_elements = {}
        for attr, val in self.xml_properties.items():
            if is_element(val):
                child_elements[attr] = val
        return child_elements

    def xml_doc(self):
        msg = []
        xml_attrs = []
        if hasattr(self, 'xml_attributes'):
            msg.append('Object references based on XML attributes:')
            for apyname in self.xml_attributes:
                local, ns = self.xml_attributes[apyname]
                if ns:
                    source_phrase = " based on '{%s}%s' in XML"%(ns, local)
                else:
                    source_phrase = " based on '%s' in XML"%(local)
                msg.append(apyname+source_phrase)
                xml_attrs.append(apyname)
        msg.append('Object references based on XML child elements:')
        for attr, val in self.__dict__.items():
            if not (attr.startswith('xml') or attr in self.xml_ignore_members):
                if attr not in xml_attrs:
                    count = len(list(getattr(self, attr)))
                    if count == 1:
                        count_phrase = " (%s element)"%count
                    else:
                        count_phrase = " (%s elements)"%count
                    local, ns = val.localName, val.namespaceURI
                    if ns:
                        source_phrase = " based on '{%s}%s' in XML"%(ns, local)
                    else:
                        source_phrase = " based on '%s' in XML"%(local)
                    msg.append(attr+count_phrase+source_phrase)
        return u'\n'.join(msg)

    def __getitem__(self, key):
        if isinstance(key, int):
            result = list(self)[key]
        else:
            force_type = None
            if isinstance(key, tuple):
                if len(key) == 3:
                    force_type, key = key[0], key[1:]
            elif isinstance(key, basestring):
                key = (None, key)
            else:
                raise TypeError('Inappropriate key (%s)'%(key))
            for attr, obj in self.xml_properties.items():
                if self.is_attribute(attr):
                    qname, ns = self.xml_attributes.get(attr)
                    if (force_type in (None, Node.ATTRIBUTE_NODE)
                        and key == (ns, SplitQName(qname)[1])):
                        #The key references an XML attribute
                        #Bypass __setattr__
                        result = obj
                        break
                elif is_element(obj):
                    if (force_type in (None, Node.ELEMENT_NODE)
                        and key == (obj.namespaceURI, obj.localName)):
                        result = obj
                        break
            else:
                raise KeyError('namespace/local name combination not found (%s)'%(str(key)))
        return result

    def __setitem__(self, key, value):
        if isinstance(key, int):
            child = self.__getitem__(key)
            child.xml_clear()
            child.xml_children = [value]
        else:
            force_type = None
            if isinstance(key, tuple):
                if len(key) == 3:
                    force_type, key = key[0], key[1:]
            elif isinstance(key, basestring):
                key = (None, key)
            else:
                raise TypeError('Inappropriate key (%s)'%(key))
            for attr, obj in self.xml_properties.items():
                if self.is_attribute(attr):
                    qname, ns = self.xml_attributes.get(attr)
                    if (force_type in (None, Node.ATTRIBUTE_NODE)
                        and key == (ns, SplitQName(qname)[1])):
                        #The key references an XML attribute
                        #Bypass __setattr__
                        self.__dict__[attr] = value
                        break
                elif is_element(obj):
                    if (force_type in (None, Node.ELEMENT_NODE)
                        and key == (obj.namespaceURI, obj.localName)):
                        obj.xml_clear()
                        obj.xml_children = [value]
                        break
            else:
                raise KeyError('namespace/local name combination not found (%s)'%(str(key)))
        return 

    def __delitem__(self, key):
        if isinstance(key, int):
            #child = self.__getitem__(key)
            #index = self.xml_parent.xml_children.index(child)
            self.xml_parent.xml_remove_child_at(key)
        else:
            force_type = None
            if isinstance(key, tuple):
                if len(key) == 3:
                    force_type, key = key[0], key[1:]
            elif isinstance(key, basestring):
                key = (None, key)
            else:
                raise TypeError('Inappropriate key (%s)'%(key))
            for attr, obj in self.xml_properties.items():
                if self.is_attribute(attr):
                    qname, ns = self.xml_attributes.get(attr)
                    if (force_type in (None, Node.ATTRIBUTE_NODE)
                        and key == (ns, SplitQName(qname)[1])):
                        #The key references an XML attribute
                        del self.xml_attributes[attr]
                        #Bypass __delattr__
                        del self.__dict__[attr]
                        break
                elif is_element(obj):
                    if (force_type in (None, Node.ELEMENT_NODE)
                        and key == (obj.namespaceURI, obj.localName)):
                        self.xml_remove_child(obj)
                        break
            else:
                raise KeyError('namespace/local name combination not found (%s)'%(str(key)))
        return 

    def xml_xslt(self, transform, params=None, output=None):
        """
        Apply an XSLT transform directly to the bindery object
        This function is quite limited, and will only handle the
        simplest transforms.  If you find your transform does not work with it,
        serialize using xml() then use Ft.Xml.Xslt.transform, which is fully
        XSLT compliant.

        output - optional file-like object to which output is written
            (incrementally, as processed)
        if stream is given, output to stream, and return value is None
        If stream is not given return value is the transform result
        as a Python string (not Unicode)
        params - optional dictionary of stylesheet parameters, the keys of
            which may be given as unicode objects if they have no namespace,
            or as (uri, localname) tuples if they do.
        """
        from Ft.Xml.Xslt import Processor, _AttachStylesheetToProcessor
        from Ft.Xml import InputSource
        from Ft.Lib import Uri, Uuid
        from Ft.Xml.Lib.XmlString import IsXml

        params = params or {}
        processor = Processor.Processor()
        _AttachStylesheetToProcessor(transform, processor)

        return processor.runNode(self, topLevelParams=params,
                                 outputStream=output)


class root_base(default_container_node, xpath_wrapper_container_mixin):
    """
    Base class for root nodes (similar to DOM documents
    and document fragments)
    """
    nodeType = Node.DOCUMENT_NODE
    xml_ignore_members = RESERVED_NAMES
    def __init__(self, naming_rule=None, doctype_name=None,
                 pubid=None, sysid=None, xmlns_prefixes=None):
        if not naming_rule: naming_rule = default_naming_rule()
        self.xml_children = []
        self.nodeName = u'#document'
        self.xml_naming_rule = naming_rule
        self.xmlns_prefixes = xmlns_prefixes or {}
        if doctype_name:
            self.xml_pubid = pubid
            self.xml_sysid = sysid
            self.xml_doctype_name = doctype_name
        return

    def xml(self, stream=None, writer=None, force_nsdecls=None, **wargs):
        """
        serialize back to XML
        if stream is given, output to stream.  Function return value is None
        You can then set the following output parameters (among others):
            encoding - output encoding: default UTF-8
            omitXmlDeclaration - u'yes' to omit the XML decl (default u'no')
            cdataSectionElements - A list of element (namespace, local-name)
                                   And all matching elements are outptu as
                                   CDATA sections
            indent - u'yes' to pretty-print the XML (default u'no')
        other output parameters are supported, based on XSLT 1.0's xsl:output
        instruction, but use fo the others is encouraged only for very advanced
        users

        You can also just pass in your own writer instance, which might
        be useful if you want to output a SAX stream or DOM nodes

        If writer is given, use it directly (encoding can be set on the writer)
        if neither a stream nor a writer is given, return the output text
        as a Python string (not Unicode) encoded as UTF-8
        
        You can force Amara to emit particular namespace declarations on the
        top-level element using the optional force_nsdecls argument.  This
        is a dictionary with unicode prefix as the key and unicode namespace URI
        as the value.  You can, for example, use the xmlns_prefixes dictionary from
        any root node.
        """
        temp_stream = None
        if not writer:
            #As a convenience, allow cdata section element defs to be simple QName
            if wargs.get('cdataSectionElements'):
                cdses = wargs['cdataSectionElements']
                cdses = [ isinstance(e, tuple) and e or (None, e)
                          for e in cdses ]
                wargs['cdataSectionElements'] = cdses
            if stream:
                writer = create_writer(stream, wargs)
            else:
                temp_stream = cStringIO.StringIO()
                writer = create_writer(temp_stream, wargs)

        writer.startDocument()
        for child in self.xml_children:
            if isinstance(child, unicode):
                writer.text(child)
            else:
                child.xml(writer=writer, force_nsdecls=force_nsdecls)
        writer.endDocument()
        return temp_stream and temp_stream.getvalue()

    #Needed for Print and PrettyPrint
    #But should we support these, since we have xml(),
    #which can take a writer with indent="yes?"
    def _doctype(self):
        class doctype_wrapper(object):
            def __init__(self, name, pubid, sysid):
                self.name = name
                self.publicId = pubid
                self.systemId = sysid
                return
        if hasattr(self, "xml_sysid"):
            return doctype_wrapper(self.xml_doctype_name, self.xml_pubid,
                                   self.xml_sysid)
        else:
            return None

    doctype = property(_doctype)

class element_iterator:
    def __init__(self, start):
        self.curr = start
        return

    def __iter__(self):
        return self

    def next(self):
        if not self.curr:
            raise StopIteration()
        result = self.curr
        if self.curr.next_elem is not None:
            self.curr = self.curr.next_elem
        else:
            self.curr = None
        return result

class element_base(_domlette.Element, container_mixin):
    xml_ignore_members = RESERVED_NAMES
    def __init__(self, name):
        self.xml_children = []
        self.xml_next_elem = None
        if isinstance(name, tuple):
            ns, qname = name
        else:
            ns, qname = None, name #FIXME: Actually name must not have a prefix.  SHould probably error check here
        _domlette.Element.__init__(self, ns, qname)
        return

    def __iter__(self):
        return element_iterator(self)

    def __len__(self):
        count = 1
        curr = self
        while curr.next_elem is not None:
            count += 1
            curr = curr.next_elem
        return count

    def __delattr__(self, key):
        if key.startswith('xml') or key in RESERVED_NAMES:
            del self.__dict__[key]
            return
        ref = getattr(self, key)
        if is_element(ref):
            self.xml_remove_child(ref)
        elif isinstance(ref, unicode):
            del self.__dict__[key]
            del self.xml_attributes[key]
        return

    def __setattr__(self, key, value):
        if key.startswith('xml') or key in RESERVED_NAMES:
            self.__dict__[key] = value
            return
        if hasattr(self, key):
            ref = getattr(self, key)
            if is_element(ref):
                ref.xml_clear()
                ref.xml_children = [value]
            #elif isinstance(ref, unicode):
            else:
                self.__dict__[key] = value
            return
        elif isinstance(value, unicode):
            self.__dict__[key] = value
            if not hasattr(self, 'xml_attributes'):
                self.xml_attributes = {}
            self.xml_attributes[key] = (key.decode('iso-8859-1'), None)
        else:
            raise ValueError('Inappropriate set attribute request: key (%s), value (%s)'%(key, value))
        return

    def xml_set_attribute(self, aname, avalue):
        "Set (or create) an attribute on ana element"
        if isinstance(aname, tuple):
            aqname, ans = aname
        else:
            aqname, ans = aname, None
        prefix, local = SplitQName(aqname)
        if prefix == u'xml':
            ans = XML_NS
        elif ans and not prefix and ans in self.rootNode.xmlns_prefixes.values():
            #If the user specified a namespace URI and not a prefix, they would
            #Usually get an ugly generated prefix.  Check the document for a nicer
            #Alternative
            #Note: this could cause spurious namespace declarations if the document is not sane
            prefix = [ p for p, u in self.rootNode.xmlns_prefixes.items() if u == ans ][0]
            aqname = prefix + u':' + local
        apyname = self.xml_naming_rule.xml_to_python(
            local, ans,
            check_clashes=dir(self))
        #Bypass __setattr__
        self.__dict__[apyname] = avalue
        if not hasattr(self, 'xml_attributes'):
            self.xml_attributes = {}
        self.xml_attributes[apyname] = (aqname, ans)
        return apyname

    #def __setattr__(self, attr, value):
        #Equivalent to creating a bound attribute
    #    self.__dict__[attr] = value
    #    return

    #def count(self):
    #    return len(list(self))

    def is_attribute(self, pyname):
         #Test a Python property (specified by name) to see whether it comes
         #from and XML attribute
         return (hasattr(self, 'xml_attributes') and self.xml_attributes.has_key(pyname))

    @property
    def xml_index_on_parent(self):
        try:
            index = self.xml_parent.xml_children.index(self)
        except ValueError: #Not found
            raise
        return index

    @property
    def xml_child_text(self):
        return u''.join([ ch for ch in self.xml_children
                            if isinstance(ch, unicode)])

    @property
    def xml_text_content(self):
        warnings.warn('This property will be eliminated soon.  Please use the unicode conversion function instead')
        return self.xml_child_text

    def __unicode__(self):
        '''
        Returns a Unicode object with the text contents of this node and
        its descendants, if any.
        Equivalent to DOM .textContent or XPath string() conversion
        '''
        return u''.join([ unicode(ch) for ch in self.xml_children
                          if not isinstance(ch, pi_base) and not isinstance(ch, comment_base)])

    def __str__(self):
        #Should we make the encoding configurable? (self.defencoding?)
        return unicode(self).encode('utf-8')

    def xml(self, stream=None, writer=None, force_nsdecls=None, **wargs):
        """
        serialize back to XML
        if stream is given, output to stream.  Function return value is None
        You can then set the following output parameters (among others):
            encoding - output encoding: default u'UTF-8'
            omitXmlDeclaration - u'no' to include an XML decl (default u'yes')
            cdataSectionElements - A list of element (namespace, local-name)
                                   And all matching elements are outptu as
                                   CDATA sections
            indent - u'yes' to pretty-print the XML (default u'no')
        other output parameters are supported, based on XSLT 1.0's xsl:output
        instruction, but use fo the others is encouraged only for very advanced
        users

        You can also just pass in your own writer instance, which might
        be useful if you want to output a SAX stream or DOM nodes

        If writer is given, use it directly (encoding can be set on the writer)
        if neither a stream nor a writer is given, return the output text
        as a Python string (not Unicode) encoded as UTF-8
        
        You can force Amara to emit particular namespace declarations on the
        top-level element using the optional force_nsdecls argument.  This
        is a dictionary with unicode prefix as the key and unicode namespace URI
        as the value.  You can, for example, use the xmlns_prefixes dictionary from
        any root node.
        """
        temp_stream = None
        close_document = 0
        if not writer:
            #Change the default to *not* generating an XML decl
            if not wargs.get('omitXmlDeclaration'):
                wargs['omitXmlDeclaration'] = u'yes'
            if stream:
                writer = create_writer(stream, wargs)
            else:
                temp_stream = cStringIO.StringIO()
                writer = create_writer(temp_stream, wargs)

            writer.startDocument()
            close_document = 1
        writer.startElement(self.nodeName, self.namespaceURI,
                            extraNss=force_nsdecls)
        if hasattr(self, 'xml_attributes'):
            for apyname in self.xml_attributes:
                aqname, ans = self.xml_attributes[apyname]
                val = self.__dict__[apyname]
                writer.attribute(aqname, val, ans)
        for child in self.xml_children:
            if isinstance(child, unicode):
                writer.text(child)
            else:
                child.xml(writer=writer)
        writer.endElement(self.nodeName, self.namespaceURI)
        if close_document:
            writer.endDocument()
        return temp_stream and temp_stream.getvalue()
    




FACTORIES = {Node.ELEMENT_NODE_TYPE: element_factory}

