########################################################################
# amara/bindery/nodes.py

"""
Bindery node implementations
"""

__all__ = [
'entity_base', 'element_base', 'element_base',
'ANY_NAMESPACE',
'PY_ID_ENCODING', 'RESERVED_NAMES'
]

from functools import *
import re
import sets
import itertools
import keyword
import warnings
import cStringIO
import bisect

from xml.dom import Node

from amara import tree
from amara.lib.xmlstring import *
from amara.xpath import datatypes

#Only need to list IDs that do not start with "xml", "XML", etc.
RESERVED_NAMES = [
    '__class__', '__delattr__', '__dict__', '__doc__', '__getattribute__',
    '__getitem__', '__hash__', '__init__', '__iter__', '__module__',
    '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__',
    '__str__', '__unicode__', '__weakref__', 'locals', 'None'
    ]

RESERVED_NAMES = frozenset(itertools.chain(keyword.kwlist, RESERVED_NAMES))

ANY_NAMESPACE = 'http://purl.xml3k.org/amara/reserved/any-namespace'
PY_ID_ENCODING = 'iso-8859-1'

#Uses the following neat pattern for partial function invokation in a property
#def a(x, instance):
#    #Call it "instance", not self since thanks to the combination of property on a partial, it's the last, not first positional arg
#    print instance.m, 0
#
#class b(object):
#    def __init__(self):
#        self.m = 0
#        setattr(self.__class__, "c", property(partial(a, 1)))
#
#t = b()
#t.c
##Prints: "0 1"

#Note the following bits of trivia:
#class b(object):
#    def __init__(self):
#        self.m = 0
#        setattr(self, "c", partial(self.a, 1))
#    def a(self, x, y, z):
#        print self.m, x, y, z
#
#t = b()
#t.c(2, 3)
##Prints: "0 1 2 3"

#def a(x, y, z):
#    print x, y, z
#
#class b(object):
#    def __init__(self):
#        setattr(self, "c", partial(a, 1))
#
#t = b()
#t.c(2, 3)
##Prints: "1 2 3"

class element_iterator:
    def __init__(self, parent, ns, local):
        self.children = iter(parent.xml_children)
        self.parent = parent
        self.ns, self.local = ns, local
        return

    def __iter__(self):
        return self

    def next(self):
        #if not self.curr:
        #    raise StopIteration()
        return self.parent.xml_find_named_child(self.ns, self.local, self.children)


def elem_getter(pname, parent):
    ns, local = parent.xml_model.element_types[pname]
    return parent.xml_find_named_child(ns, local)


#Note: one of the better explanations of descriptor magic is here: http://gnosis.cx/publish/programming/charming_python_b26.html
#Also: http://users.rcn.com/python/download/Descriptor.htm
#See also official docs here: http://docs.python.org/ref/descriptors.html

class bound_element(object):
    """
    A descriptor to support bound elements
    """
    #A descriptor to support elements that are not defined in the owner class's xml_model
    def __init__(self, ns, local):
        self.ns = ns
        self.local = local

    def __get__(self, obj, owner):
        return obj.xml_find_named_child(self.ns, self.local)

    def __set__(self, obj, value):
        #replicate old __delattr__ effects here
        return

    def __delete__(self, obj):
        #replicate old __delattr__ effects here
        return


class bound_attribute(object):
    """
    A descriptor to support bound attributes
    """
    #A descriptor to support attributes that are not defined in the owner class's xml_model
    def __init__(self, ns, local):
        self.ns = ns
        self.local = local

    def __get__(self, obj, owner):
        return node.xml_attributes[self.ns, self.local]

    def __set__(self, obj, value):
        node.xml_attributes[self.ns, self.local].xml_value = value
        return

    def __delete__(self, obj):
        del node.xml_attributes[self.ns, self.local]
        return


class container_mixin(object):
    @property
    def xml_element_pnames(self):
        return itertools.chain(self.xml_model.element_types.itervalues(),
                               (self.xml_extra_children or {}).iterkeys())

    @property
    def xml_element_xnames(self):
        return itertools.chain(self.xml_model.element_types.iterkeys(),
                               (self.xml_extra_children or {}).itervalue())

    @property
    def xml_child_text(self):
        return u''.join([ ch for ch in self.xml_children if isinstance(ch, unicode)])

    def xml_child_inserted(self, child):
        """
        called after the node has been added to `self.xml_children`
        """
        if isinstance(child, tree.element):
            fe = getattr(self, 'factory_entity', self)
            name_chosen = False
            exclusions = []
            while not name_chosen:
                pname = fe.pyname(child.xml_namespace, child.xml_qname, exclusions)
                existing = getattr(self, pname, None)
                if existing is None or existing.xml_name == child.xml_name:
                    name_chosen = True
            if existing is None:
                setattr(self.__class__, pname, bound_element(child.xml_namespace, child.xml_local))
#            if isinstance(child, tree.element):
#                #FIXME: A property is just a standard construct that implements the descriptor protocol, so this is a silly distinction.  Just use descriptors.
#                #Need to treat it using element binding rules
#                if pname in self.xml_model.element_types:
#                    #Then this is a declared type of element; add it as a property
#                    setattr(self.__class__, pname, partial(self.xml_getter, pname))
#                else:
#                    #An ad-hoc member, for this instance only.
#                    setattr(self.__class__, pname, ad_hoc_element(child.xml_namespace, child.xml_local))
        return

    def xml_child_removed(self, child):
        """
        called after the node has been removed from `self.xml_children` (i.e. child.xml_parent is now None)
        """
        #Nothing really to do: we don't want to remove the descriptor from the class, since other instances might be using it
        return

    def xml_find_named_child(self, ns, local, childiter=None):
        found = False
        #could use dropwhile (with negation)...
        #self.children = dropwhile(lambda c, n=self.name: (c.xml_namespace, c.xml_name) != n, self.children)
        childiter = iter(self.xml_children) if childiter is None else childiter
        while not found:
            child = childiter.next() #Will raise StopIteration when siblings are exhausted
            found = child.xml_type == tree.element.xml_type and child.xml_name == (ns, local)
        return child


class element_base(container_mixin, tree.element):
    xml_attribute_factory = tree.attribute #factory callable for attributes

    xml_model = None
    def __init__(self, ns, qname):
        #These are the children that do not come from schema information
        self.xml_extra_children = None
        self.xml_extra_attributes = None
        #self.xml_iter_next = None
        #if isinstance(name, tuple):
        #    ns, qname = name
        #else:
        #    ns, qname = None, name #FIXME: Actually name must not have a prefix.  Should probably error check here
        #tree.element.__init__(self, ns, qname)
        return

    def xml_attribute_added(self, attr_node):
        """
        called after the attribute has been added to `self.xml_attributes`
        """
        pname = self.xml_factory.pyname(attr_node.xml_namespace, attr_node.xml_name, dir(self))
        setattr(self.__class__, pname, bound_attribute(attr_node.xml_namespace, attr_node.xml_local))
        return

    def xml_attribute_removed(self, attr_node):
        """
        called after the attribute has been removed `self.xml_attributes`
        """
        #Nothing really to do: we don't want to remove the descriptor from the class, since other instances might be using it
        return

    @property
    def xml_attribute_pnames(self):
        return itertools.chain(self.xml_model.attribute_types.itervalues(),
                               (self.xml_extra_attributes or {}).iterkeys())

    @property
    def xml_pnames(self):
        return itertools.chain(self.xml_attribute_pnames, self.xml_element_pnames)

    @property
    def xml_attribute_xnames(self):
        return itertools.chain(self.xml_model.attribute_types.iterkeys(),
                               (self.xml_extra_attributes or {}).itervalue())

    @property
    def xml_index_on_parent(self):
        try:
            index = self.xml_parent.xml_children.index(self)
        except ValueError: #Not found
            raise
        return index

    def __unicode__(self):
        '''
        Returns a Unicode object with the text contents of this node and
        its descendants, if any.
        Equivalent to XPath string() conversion
        '''
        #return self.xml_select(u'string(.)')
        return datatypes.string(self)

    def __str__(self):
        #Amara 1 note: Should we make the encoding configurable? (self.defencoding?)
        #For Amara 2, consider using the document node encoding property
        return unicode(self).encode('utf-8')

    def __iter__(self):
        return element_iterator(self.xml_parent, self.xml_namespace, self.xml_qname)

    def __len__(self):
        return len(list(element_iterator(self.xml_parent, self.xml_namespace, self.xml_qname)))

    def __getitem__(self, key):
        #$ python -c "from amara.bindery import parse; from itertools import *; doc = parse('<x><a b=\"1\"/><a b=\"2\"/><a b=\"3\"/><a b=\"4\"/></x>'); print list(islice(doc.x.a, 2,3))[0].xml_attributes.items()"
        # => [((None, u'b'), u'3')]
        if isinstance(key, int):
            result = list(itertools.islice(element_iterator(self.xml_parent, self.xml_namespace, self.xml_qname), key, key+1))[0]
        else:
            force_type = None
            if isinstance(key, tuple):
                if len(key) == 3:
                    force_type, key = key[0], key[1:]
            elif isinstance(key, basestring):
                key = (None, key)
            else:
                raise TypeError('Inappropriate key (%s)'%(key))
            if force_type in (None, tree.attribute.xml_type) and key in self.xml_attributes:
                return self.xml_attributes[key]
            if force_type in (None, tree.element.xml_type):
                return self.xml_find_named_child(self, key[0], key[1])
            else:
                raise KeyError('namespace/local name combination not found (%s)'%(str(key)))
        return result


#This class also serves as the factory for specializing the core Amara tree parse

class entity_base(container_mixin, tree.entity):
    """
    Base class for entity nodes (root nodes--similar to DOM documents and document fragments)
    """
    PY_REPLACE_PAT = re.compile(u'[^a-zA-Z0-9_]')
    #xml_comment_factory = tree.comment
    #xml_processing_instruction_factory = tree.processing_instruction
    #xml_text_factory = tree.text

    def __init__(self, document_uri=None):
        #These are the children that do not come from schema information
        self.xml_extra_children = None
        #self.xml_iter_next = None
        #tree.entity.__init__(self, document_uri=document_uri)
        #Should we share the following across documents, perhaps by using an auxilliary class,
        #Of which one global, default instance is created/used
        #Answer: probably yes
        self._eclasses = {}
        self._class_names = {}
        self._names = {}
        return

    def pyname(self, ns, local, exclude=None):
        '''
        generate a Python ID (as a *string*) from an XML universal name

        ns - the XML namespace
        local - the XML local name
        exclude - iterator of names not to use (e.g. to avoid clashes)
        '''
        python_id = self._names.get((local, ns))
        if not python_id:
            python_id = self.PY_REPLACE_PAT.sub('_', local.encode('utf-8'))
            if python_id in RESERVED_NAMES:
                python_id = python_id + '_'
            self._names[(local, ns)] = python_id
        if exclude:
            while python_id in exclude:
                python_id += '_'
        return python_id

    def xname(self, python_id):
        #XML NMTOKENS are a superset of Python IDs
        return python_id

    def xml_element_factory(self, ns, qname, pname=None):
        prefix, local = splitqname(qname)
        if not pname: pname = self.pyname(ns, local)
        if (ns, local) not in self._eclasses:
            class_name = pname
            eclass = type(class_name, (element_base,), {})
            self._eclasses[(ns, local)] = eclass
        else:
            eclass = self._eclasses[(ns, local)]
        e = eclass(ns, qname)
        e.factory_entity = self
        return e


#class myattribute(tree.attribute)
#    #Specialize any aspects of attribute here
#    pass


