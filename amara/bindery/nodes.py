__all__ = [
'binder', 'TOP', 'ANY_NAMESPACE', 'REMOVE_RULE',
'PY_REPLACE_PAT', 'RESERVED_NAMES'
]

from xml import Node
from functools import *
from amara import _domlette
from amara import tree
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
    '__str__', '__unicode__', '__weakref__', 'locals', 'None'
    ]

RESERVED_NAMES = frozenset(itertools.chain(keyword.kwlist, RESERVED_NAMES))

ANY_NAMESPACE = 'http://purl.xml3k.org/amara/reserved/any-namespace'

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
        self.children = parent.xml_children
        self.parent = parent
        self.name = (ns, local)
        return

    def __iter__(self):
        return self

    def next(self):
        if not self.curr:
            raise StopIteration()
        found = False
        #could use dropwhile (with negation)...
        #self.children = dropwhile(lambda c, n=self.name: (c.xml_namespace, c.xml_name) != n, self.children)
        while not found:
            child = self.children.next() #Will raise StopIteration when siblings are exhausted
            found = (child.xml_namespace, child.xml_name) == self.name
        return child


def elem_getter(pname, parent):
    ns, local = parent.xml_model.element_types[pname]
    return element_iterator(parent, ns, local)

#Note: one of the better explanations of descriptor magic is here: http://gnosis.cx/publish/programming/charming_python_b26.html
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
        return element_iterator(obj, self.ns, self.local)

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
            pname = self.xml_factory.pyname(child.xml_namespace, child.xml_name, dir(self))
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


PY_ID_ENCODING = 'iso-8859-1'

class element_base(tree.element, container_mixin):
    xml_model = None
    def __init__(self, name):
        #These are the children that do not come from schema information
        self.xml_extra_children = None
        self.xml_extra_attributes = None
        #self.xml_iter_next = None
        if isinstance(name, tuple):
            ns, qname = name
        else:
            ns, qname = None, name #FIXME: Actually name must not have a prefix.  Should probably error check here
        tree.element.__init__(self, ns, qname)
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
        return self.xml_select(u'string(.)')

    def __str__(self):
        #Amara 1 note: Should we make the encoding configurable? (self.defencoding?)
        #For Amara 2, consider using the document node encoding property
        return unicode(self).encode('utf-8')



class entity_base(tree.entity, container_mixin):
    """
    Base class for entity nodes (root nodes--similar to DOM documents and document fragments)
    """
    def __init__(self):
        #These are the children that do not come from schema information
        self.xml_extra_children = None
        #self.xml_iter_next = None
        tree.entity.__init__(self, ns, qname)
        return


FACTORIES = {Node.ELEMENT_NODE_TYPE: element_factory}

