.. This document is in reST, and used with Sphinx. For a reST primer see http://sphinx.pocoo.org/rest.html
****************************
Amara Manual, version 2.0a3
****************************

:Author: Uche Ogbuji
:Release: |release|
:Date: |today|

`Amara 2.0 <http://wiki.xml3k.org/Amara2>`_ is the core XML processing library for `Akara <http://wiki.xml3k.org/Akara>`_.


Core node API
=============

Amara has at its core ``amara.tree``, a simple node API that makes available the information in an XML document.  It is similar to DOM (or the W3C InfoSet)[#CNA1]_, but easier to use, more expressive and more in line with Python conventions.  The main quirk with the core node API is that node methods are prepended with ``xml_`` in order to support the bindery subclass which exposes XML constructs as Python attributes.

Amara also provides a couple of tree APIs derived from the core: Bindery and DOM.  Everything in this section applies to those, as well.

Reading XML documents
---------------------

Parse to create a tree object as follows::

  from amara import *
  doc = parse(source) #source can be file, URI, stream or string

You can specialize the parse using flags::

  doc = parse(source, validate=True) #Enable DTD validation

The flags are (mutually exclusive at present):

* ``validate`` - include external entities & perform DTD validation
* ``standalone`` - no parsed external entities (or external DTD subset)

You can specialize the generated node classes as follows:

.. #!code python
  from amara import tree
  class myattribute(tree.attribute)
      #Specialize any aspects of attribute here
      pass

  class myelement(tree.element)
      xml_attribute_factory = myattribute #factory callable for attributes.  If omitted defaults to amara.tree.attribute
      #Specialize any other aspects of element here

  class myentity(tree.entity)
      #If you don't specify a factory for any node type it defaults to the tree.x class
      xml_element_factory = myelement #factory callable for elements
      #xml_comment_factory = tree.comment
      #xml_processing_instruction_factory = tree.processing_instruction
      #xml_text_factory = tree.text

  doc = parse(source, entity_factory=myentity)

``myentity`` is a subclass of entity with class properties that override factory behavior.

Creating nodes from scratch
---------------------------

You can construct core tree nodes as regular Python objects, using factory functions (note: Factory callables in derived classes **must** have matching signatures):

||'''base Amara tree type'''||'''factory callable signature'''||
||`tree.entity`||`entity(document_uri=None)`||
||`tree.element`||`element(ns, local)`||
||`tree.comment`||`comment(data)`||
||`tree.processing_instruction(`||`processing_instruction(target, data)`||
||`tree.text`||`text(data)`||
||`tree.attribute`||`attribute(ns, local, value=u'')`||

.. If your callable is a class, then of course the `__init__` can have the usual `self`.

Use the factory callables to create documents, and other nodes::

  from amara import tree
  from amara import xml_print
  doc = tree.entity()
  doc.xml_append(tree.element(None, u'spam'))
  xml_print(doc)    #<?xml version="1.0" encoding="UTF-8"?>\n<spam/>



.. rubric:: Footnotes

.. [#CNA1] The data model defines Python-friendly conventions taken from XPath data model followed by XML Infoset followed by DOM Level 3.

Bindery API
=============


Input sources
=============

Amara makes it easy to manage data sources for XML and such with typical Web usage patterns in mind.  The basic construct is an input source

inputsouce





== Writing ==

'''Note: the methods defined in this section are not yet available for nodes.  Use {{{python amara.xml_print(node)}}} until they are ready'''

Use the `xml_write()` method to re-serialize to XML to as stream (`sys.stdout` by default).  Use the `xml_encode()` method to re-serialize to XML, returning string.


{{{#!code python
node.xml_write(amara.writer.html, indent=True) #Write out an XML document as pretty-printed HTML
node.xml_encode() #Return an XML string
node.xml_encode(amara.writer.html, indent=True) #Return an indented HTML string
}}}

There are special methods to look up a writer class from strings such as "xml" and "html"

{{{#!code python
from amara.writer import lookup
XML_W = lookup("xml")
HTML_W = lookup("html")

node.xml_write(XML_W) #Write out an XML document
node.xml_encode(HTML_W) #Return an HTML string
}}}

The default writer is the XML writer (i.e. `amara.writer.lookup("xml")`)

##There is a convenience `xml()` method, which handles the most common case where you just want to emit XML.
##
##{{{#!code python
##node.xml() #shortcut for node.xml_write(amara.writer.xml)
##node.xml('iso-8859-1') #shortcut for node.xml_write(amara.writer.xml, encoding='iso-8859-1)
##}}}

== Porting from domlette ==

Here are the brief details for how to port from 4Suite domlette API to Amara 2.x tree nodes.

=== All node types ===

Note: All properties discussed are mutable unless otherwise noted.

 * Amara tree nodes don't have the equivalent of DOM ownerDocument.
 * `node.nodeType` becomes `node.xml_type`

   <!> `node.xml_type` is now a string rather than an integer.

   {i} It is recommended to use `isinstance()` checks whenever possible instead of comparing `xml_type` values. Use of `xml_type` is best suited as a key for dispatch tables.

 * There is no longer universal `node.nodeName`, `node.nodeValue`, `node.namespaceURI`, `node.localName`, `node.prefix` and `node.childNodes` (and all the other child-related members) on all node types.  See each note type section below for more details. 

 * `node1.isSameNode(node2)` is now `node1 is node2`

 * `node.xpath()` becomes `node.xml_select()`

   {i} Note: the old Amara node.xml_xslt method is now available on all nodes as node.xml_transform

 * `node.rootNode` becomes `node.xml_root` (which is almost equivalent to `node.xml_select(u"/")`)

   <!> `node.xml_root` will return None for an unattached node whereas `node.xml_select(u"/")` will return empty node set

   {i} `node.xml_root` is equivalent to: `while node.xml_parent: node = node.xml_parent`

   <!> In general the path of least surprise is to not run XPath on unattached nodes.  Note that an unattached node is not the common case because it means the element tree was constructed by hand.  If you use any of Amara's parse methods or such high level APIs, you should always have a Document/Entity at the root.  Otherwise, we assume you really know what you're doing.

 * `node.baseURI` and `node.xmlBase` become `node.xml_base`

   <!> The `doc.xml_system_id` on an Entity is different from `doc.xml_base`.  It is equiv to the `systemId` property of the `DocumentType` node in DOM L3 (There is similar correspondence between `doc.xml_public_id` and publicId DOM property).

 * `node.cloneNode()` becomes `from copy import copy; copy(node)`; `node.cloneNode(True)` becomes `from copy import deepcopy; deepcopy(node)`

=== Attribute nodes ===

==== Changes ====
 * `attr.nodeName` becomes `attr.xml_qname` (an immutable property -- to change, update xml_local and xml_namespace)
 * `attr.nodeValue` becomes `attr.xml_value`
 * `attr.qualifiedName` becomes `attr.xml_qname` (an immutable property)
 * `attr.value` becomes `attr.xml_value`
 * `attr.namespaceURI` becomes `attr.xml_namespace` 
 * `attr.localName` becomes `attr.xml_local`
 * `attr.prefix` becomes `attr.xml_prefix`
 * `attr.specified` becomes `attr.xml_specified` (an immutable property)

==== New Features ====
 * `attr.xml_name` returns a 2-item tuple of `(namespace, local)`  (an immutable property)

=== CharacterData (Text and Comment) nodes ===

 * `node.length`, `node.substringData()`, `node.insertData()`, `node.replaceData()`, `node.appendData()` and `node.deleteData()` are eliminated.  Just use string manipulation on `node.xml_value`

   {i} `node.length` becomes `len(node.xml_value)`

   {i} `node.substringData(start, stop)` becomes `data = node.xml_value[start:stop]`

   {i} `node.appendData(data)` becomes `node.xml_value += data`

 * `node.nodeValue` becomes `node.xml_value`
 * `node.data` becomes `node.xml_value`
 * `node.nextSibling` becomes `node.xml_following_sibling`  (an immutable property)
 * `node.previousSibling` becomes `node.xml_preceding_sibling` (an immutable property)

=== Element nodes ===

==== Changes ====
 * `node.nodeName`, `node.tagName` and `node.qualifiedName` become `node.xml_qname`  (an immutable property)
 * `node.namespaceURI` becomes `node.xml_namespace`  (an immutable property)
 * `node.localName` becomes `node.xml_local`
 * `node.prefix` becomes `node.xml_prefix`
 * `node.childNodes` becomes `node.xml_children` (an immutable property)
 * `node.hasChildNodes()` becomes `bool(node.xml_children)`
 * `node.firstChild` becomes `node.xml_first_child` (an immutable property)
 * `node.lastChild` becomes `node.xml_last_child` (an immutable property)
 * `node.normalize()` becomes `node.xml_normalize()`
 * `node.nextSibling` becomes `node.xml_following_sibling` (an immutable property)
   (!) Another option is node.xml_select(u'following-sibling:￼:*')
 * `node.previousSibling` becomes `node.xml_preceding_sibling` (an immutable property)
   (!) Another option is node.xml_select(u'preceding-sibling:￼:*')
 * `node.getElementById(u'foo')` becomes `node.xml_lookup(u'foo')`
 * `node.getElementByTagNameNS()` was never provided in 4Suite.  As before just use `node.xml_select`
 * `node.attributes` becomes `node.xml_attributes` (an immutable property)
 * `node.getAttributeNodeNS(ns, localname)` becomes `node.xml_attributes.getnode(ns, localname)`
 * `node.setAttributeNodeNS(attr_node)` becomes `node.xml_attributes[ns, localname] = attr_node` (the local name and the namespace of the given object must not conflict with ns and localname)
   (!) Another option would be `node.xml_attributes.setnode(attr_node)` to remove the redundant expanded-name key
 * `node.getAttributeNS(ns, localname)` becomes `node.xml_attributes[ns, localname]`
 * `node.setAttributeNS(ns, qname, value)` becomes `node.xml_attributes[ns, localname] = value`
   <!> To set an explicit prefix, one must retrieve the attribute node: {{{
   E.xml_attributes[ns, localname] = value
   E.xml_attributes.getnode(ns, localname).xml_prefix = prefix}}}
 * `node.hasAttributeNS(ns, localname)` becomes `(ns, localname) in node.xml_attributes`
 * `node.removeAttributeNode(attr_node)` becomes `node.parent.xml_remove(attr_node)`
   (!) Another option would be `del node.xml_attributes[attr_node]`
 * `node.removeAttribute(ns, localname)` becomes `del node.xml_attributes[ns, localname]`
 * namespace attributes are now accessed by `E.xmlns_attributes` (as namespace nodes)
 * `E.xml_namespaces` is a `NamespaceMap` (akin to NamedNodeMap, only for namespace nodes) of all inscope namespaces

 * `node.appendChild(newnode)` becomes `node.xml_append(newnode)`
   /!\ If newnode is an entity, this is a destructive act that will take all children of that entity and leave it empty, appending them to node.  If you want to preserve newnode, copy it first: `copy.deepcopy(newnode)`.
 * `node.removeChild(oldnode)` becomes `node.xml_remove(oldnode)`
 * `node.insertBefore(newnode, refnode)` becomes `offset = node.xml_index(refnode);  node.xml_insert(offset, newnode)`
 * `node.replaceChild(newnode, oldnode)` becomes `node.xml_replace(oldnode, newnode)`

We're considering adding an equivalent to list.extend

==== New Features ====
 * `element.xml_name` returns a 2-item tuple of `(namespace, local)`
 * `element.xml_index(node[, start[, stop]])` which is equivalent to `list.index()`
 * `iter(element.xml_attributes)` -> an iterator of `(ns, localname)`
 * `element.xml_attributes.keys()` -> an iterator of `(ns, localname)`
 * `element.xml_attributes.values()` -> an iterator of node values
 * `element.xml_attributes.nodes()` -> an iterator of nodes

=== Processing Instructions ===

 * `node.nodeName` becomes `node.xml_target`
 * `node.nodeValue` becomes `node.xml_data`
 * `node.target` becomes `node.xml_target`
 * `node.data` becomes `node.xml_data`
 * `node.nextSibling` becomes `node.xml_following_sibling` (an immutable property)
 * `node.previousSibling` becomes `node.xml_preceding_sibling` (an immutable property)

=== Document, DocumentFragment, Entity ===

`DocumentFragment` nodes are no more.  Whether you parse an XML document or an external parsed entity (which may have more than one root node, may have text at the root level, etc.), you get a Document.  The type name is really a misnomer--it's an entity, and the name will be changed in a later version to reflect this fact.  Note: Amara Entity does '''not''' correspond to DOM L3 Entity--some of the properties have different semantics.

The Document/Entity type always has xml_parent of None.  Other nodes can have xml_parent of None if they are unappended node fragments.  The Document/Entity is much like an XPath data model root node type (as elaborated a bit further in XSLT).

Note lexical information based on doc type definitions (such as the use of entities in the serialization of text nodes) is generally lost, as it was for 4Suite and Amara 1.x, and in most other XML rocessing software.  We might in future add features to retain som of this information.

==== Changes ====

 * `node.documentURI` becomes `node.xml_base`
 * `node.documentElement` is removed as entities can have multiple element children.  use e.g. node.xml_first_child or some operation on node.xml_children
 * `node.childNodes` becomes `node.xml_children` (an immutable property)
 * `node.hasChildNodes()` becomes `bool(node.xml_children)`
 * `node.firstChild` becomes `node.xml_first_child` (an immutable property)
 * `node.lastChild` becomes `node.xml_last_child` (an immutable property)
 * `node.normalize` becomes `node.xml_normalize`
 * `node.getElementById(u'foo')` becomes `node.xml_lookup(u'foo')`
 * `node.getElementByTagNameNS()` was never provided in 4Suite.  As before just use `node.xml_select`

 * `node.appendChild(newnode)` becomes `node.xml_append(newnode)`
   (!) Note ther is a new convenience method node.xml_merge(other), which destructively appends all the children of other to node
 * `node.removeChild(oldnode)` becomes `node.xml_remove(oldnode)`
 * `node.insertBefore(newnode, refnode)` becomes `offset = node.xml_index(ref_node);  node.xml_insert(offset, newnode)`
 * `node.replaceChild(newnode, oldnode)` becomes `node.xml_replace(newnode, oldnode)`

==== New Features ====

 * `entity.xml_index(node[, start[, stop]])` which is equivalent to `list.index()`

= Working with namespaces =

On each element you have the following properties related to XML namespace.

 * `node.xml_prefix` ''(elements and attributes)'' -- The node's namespace prefix
 * `node.xml_namespace` ''(elements and attributes)'' -- The node's namespace URI
 * `node.xml_attributes` ''(elements only)'' -- All attributes on this element '''excluding namespace declarations'''
 * `node.xmlns_attributes` ''(elements only)'' -- The namespace declaration attributes on this element
 * `node.xml_namespaces` ''(read-only)'' ''(elements and documents)'' -- (equivalent to XPath namespace nodes) sequence of all in-scope namespaces as nodes
   /!\ `GetAllNs()` has been superseded by the `xml_namespaces` property (use `dict([(n.xml_local, n.xml_value) for n in doc.xml_namespaces])`)

In general these concepts are similar to those in [[http://www.w3.org/TR/xml-infoset/#infoitem.element|XML Infoset "2.2. Element Information Items"]]

If you work with XML namespaces you will probably need to create namespace declarations at some point.  You can do so as follows:

{{{#!code python
node.xmlns_attributes[prefix] = nsuri
}}}

Where `node` is an element or document node and `prefix` and `nsuri` are Unicode objects.  If in modifying an element's or attribute's `xml_prefix` or `xml_namespace`, you create a mapping that does no correspond to any in scope namespace existing declaration you will get an error.  The best way to avoid this error is to make an explicit declaration first, as above.

If you manipulate a node's `xml_prefix` and `xml_namespace` property directly, Amara offers a trick to ensure consistency.  Take the following document.

{{{#!code xml
<doc xmlns:a="urn:bogus:a" xmlns:b="urn:bogus:b">
  <a:monty/>
</doc>
}}}

Say you want to put a:monty element into the `urn:bogus:b`.  You can do so as follows:

{{{#!code python
doc.monty.xml_namespace = u"urn:bogus:b"
#Side-effect is doc.monty.xml_prefix = u"b"
}}}

Or as follows:

{{{#!code python
doc.monty.xml_prefix = u"b"
#Side-effect is doc.monty.xml_namespace = u"urn:bogus:b"
}}}

Amara is thus careful to maintain namespace integrity for you.  The above is also the only way to change the parts of an element or attribute's universal name.  Properties such as `xml_name` and `xml_qname` are immutable (as an implementation detail, they're computed).  In effect, Amara allows you to declare namespaces as you see fit (either directly or by creating new nodes which don't conform to any existing declarations in that scope) but then it enforces those declarations upon any existing nodes within a particular scope.


= Mutation events =

Amara tree now has a system for signaling mutation of the tree.

Note: this is not really based on [[[http://www.w3.org/TR/2003/NOTE-DOM-Level-3-Events-20031107/|DOM|L3 events]]]

 * `node.xml_child_inserted(child)` -- called '''after''' the node has been added to `node.xml_children`
 * `node.xml_child_removed(child)` -- called '''before''' the node is removed from `node.xml_children`
 * `element.xml_attribute_added(attr_node)` -- called after the attribute node has been added to `element.xml_attributes`
 * `element.xml_attribute_removed(attr_node)` -- called after the attribute node has been removed `element.xml_attributes`
 * `element.xml_attribute_modified(attr_node)` -- called after the attribute node's value has been updated

Note: we are probably going to add more mutation events in future versions.  We're researching related efforts as rough guidance, including:

 * DOM L3 Events
 * [[http://www.gnu.org/software/classpathx/jaxp/apidoc/gnu/xml/dom/DomNode.html|Mutation|events on GNU's JAXP impl]]

== Exceptions in mutation events ==

<!> We propagate all exceptions from mutation event handlers, in order to allow you to catch bugs in these.  In general, though you should avoid as much as possible raising exceptions from mutation event handlers, as these can lead to problems with data consistency.  We do as much as we can to make mutation transactional, but there are some very hard cases that you get into when dealing with exceptions from handlers.


= DOM =

Amara 2 offers a purer analogue to W3C DOM than the old 4Suite Domlette.  Amara DOM is a wrapper of Amara tree.  Note that most people will want to use Amara tree.  Only use Amara DOM if you really need the (rather clumsy and non-pythonic) W3C interfaces.

== Reading ==

You now parse to domlette as follows:

{{{#!code python
from amara.domlette import *
...
doc = parse(source) #source can be file, URI, stream or string
}}}


= Bindery =

Bindery is now a subclass of Domlette, so you should also review the Domlette section above.

A quick note on what's not new: you still parse using `amara.parse` (which is an alias for `amara.bindery.parse`).  Amara of course now supports other types of parse e.g. domlette or saxlette, and you just use more detailed paths for these (`amara.domlette.parse`), etc.

{{{#!code python
import amara
...
doc = amara.parse(source) #source can be file, URI, stream or string
print doc.spam.eggs.xml()
}}}

== Creating a bindery document from scratch ==

Because of the special nature of bindery, it's a bit fiddly to create a document from scratch.  It's probably better to just parse a document.  You can use the bindery entity base class:

{{{#!code python
from amara import bindery
from amara import xml_print
doc = bindery.nodes.entity_base()
doc.xml_append(doc.xml_element_factory(None, u'spam'))
xml_print(doc)    #<?xml version="1.0" encoding="UTF-8"?>\n<spam/>
}}}

You can also use xml_append_fragment

{{{#!code python
from amara import bindery
from amara import xml_print
doc = bindery.nodes.entity_base()
doc.xml_append_fragment('<a><b/></a>')
xml_print(doc)    #<?xml version="1.0" encoding="UTF-8"?>\n<a><b/></a>
}}}

== Accessing elements/attributes that may not be in the XML ==

In Amara 1.x accessing an element or attribute missing from the source XML gives AttributeError so that:

{{{#!code python
X = """\
<monty>
  <python spam="eggs">What do you mean "bleh"</python>
  <python ministry="abuse">But I was looking for argument</python>
</monty>
"""
import amara
doc = amara.parse(X)
print doc.monty.python.spam
print doc.monty.python.ministry
}}}

results in:

{{{#!code pytb
eggs
Traceback (most recent call last):
  File "/tmp/foo.py", line 10, in <module>
    print doc.monty.python.ministry
AttributeError: 'python' object has no attribute 'ministry'
}}}

The first element has a `spam` attribute, but not `ministry`.  Since an index was not specified Amara returns the first python element, which is missing the attribute.

There has been some complaint about this, because it means you have to employ a "look before you leap" approach, or use a lot of exception handling to deal with common situations such as optional elements or attributes.  You could also use XPath (`doc.xml_select(u'monty/python/ministry')`) which returns [] (you can use the `string` function to return Unicode) or the Pythonic approach of `getattr(doc.monty.python, 'ministry', u'')`.

Amara 2.x will offer users several conveniences.  First of all, a parse rule that allows you to set defaults for missing XML nodes.  This would, for example, create a value of `u''` for each `ministry` attribute missing from a `python` element.  You can also use a subclass that implements create-on-get semantics.  This means that `print doc.monty.python.ministry` could automatically create and return an empty element `ministry` as the last child of `python`.  Alternatively it will not create anything, and will just return None in cases that lead to AttributeError.  Neither approach is really recommended because the complexities of balancing XML and Python data structure semantics can be even more confusing.  Explicit is better, where you use XPath for its explicitly known forgiving semantics, and Python for its normal, strict behavior.  The best approach, if you need to probe entire substructures that you are not sure exists is to use XPath.  If you want a shallow, safe attribute access, you can use the new xml_get (new in 2.0). `doc.monty.python.xml_get('ministry')` is similar to `getattr(doc.monty.python, 'ministry', u'')`.

=== Convenience API ===

There is a new, more consistent API for navigating the skew between XML and Python names.

##node.xml_elements             #iterator of child element nodes (not the dict from Amara 1.x); equiv of Amara 1.x `( e for e in node.xml_children if e.nodeType == Node.ELEMENT_NODE)`
##node.xml_attributes           #iterator of attributes nodes (not the dict from Amara 1.x)

{{{#!code python
node.xml_element_pnames       #iterator of child element property names; near-replacement for Amara 1.x node.xml_elements
node.xml_element_xnames       #iterator of child element XML universal names (namespace, local)
node.xml_attribute_pnames     #iterator of attributes property names; near-replacement for  Amara 1.x node.xml_attributes
node.xml_attribute_xnames     #iterator of attributes XML universal names (namespace, local)
}}}

The Amara 1.x properties xml_elements and xml_attributes were too incongruous, and are no more.

The old node.xml_attributes behavior can be had with:

{{{#!code python
from itertools import *
dict([x, (node.namespaceURI, getattr(node, x)) for x in node.xml_attribute_pnames])
}}}

The old node.xml_elements can be had with:

{{{#!code python
from itertools import *
dict([x, getattr(node, x) for x in node.xml_element_pnames])
}}}

##This assumes the above are not much necessary with the new API.  If it turns put they are we might add ##`node.xml_model.attribute_pname_dict` (from Python name to tuple of XML Universal name and value) and similar ##`node.xml_model.element_pname_dict`.

node.xml_child_text is no more.  It's equivalent to:

{{{#!code python
u''.join(node.xml_select(u'text()'))
}}}

Note: as above, if you want to iterate using XML node types, use XPath
## (you'll now get an iterator rather than a list):

{{{#!code python
node.xml_select(u'*')          #iterator of child elements
node.xml_select(u'@*')         #iterator of attributes
node.xml_select(u'text()')     #iterator of child text nodes
node.xml_select(u'comment()')  #iterator of child comment nodes
node.xml_select(u'processing-instruction()')  #iterator of child processing instruction nodes
}}}

Discussion:

 * http://lists.fourthought.com/pipermail/4suite/2008-March/008387.html
 * http://groups.google.com/group/amara-user/browse_thread/thread/602df975b12a8509

For more on this see [[Amara2/Modeling]]

== Managing the XML model ==

Related to the above issue is the question of how you can query and manage aspects of the XML model in Python.  Can you discover what data members come from where in the XML (e.g. to distinguish XML elements from attributes, or these from mixed-in Python data members)?  Can you work with schema or constraint information?

Amara 1.x provided a human-readable synopsis in node.xml_doc()

Amara 2.X provides formalized XML model information, opening up some powerful capabilities.  The key is in the binding classes.  Now binding classes are differentiated not only by name, but also by what constraints they support.  If there is no guidance on the XML model every node will use generic bindings.  Such guidance can come in several ways:

 * Register an XML schema (RELAX NG or Schematron)
 * Set up constraints in a special structure for the purpose
 * Set constraints after the parse

You access the constraint information in the new class property xml_model.  It's based at the core on the Schematron model of assertions, though there are many conveniences for dealing with constraints in alternate ways.  Here are some of the low-level primitives:

{{{#!code python
node.xml_model.element_types    #Known child element types for this node's class as a dict from XML universal name to Python name
node.xml_model.attribute_types  #Known attribute types for this node's class as a dict from XML universal name to Python name
}}}

The above combine required and optional node types, derived from the constraints, and additional information about optional node types.

If you try to access an element or attribute on `node` which is in `node.xml_model.element_types` but does not exist on the present instance, you get None rather than AttributeError.  This is a key change from Amara 1.x, and discussed further below.

{{{#!code python
node.xml_model.element_types    #Known child element types for this node's class as a dict from XML universal name to Python name
node.xml_model.attribute_types  #Known attribute types for this node's class as a dict from XML universal name to Python name
}}}

You can access and manipulate constraints as follows:

{{{#!code python
node.xml_model.constraints      #A list of constraint objects 
}}}

Each constraint object is essentially a Schematron assertion, with some convenience bits.

{{{#!code python
node.xml_model.constraints.append(u'@xml:id', validate=True)      #Make xml:id required.  Will throw a constraint violation right away if there is not one.  Affects all instances of this class.
node.xml_model.validate(recurse=True)     #Recursively validate constraints on node and all children
}}}

Notice that manipulating constraints affect all nodes that are instances of that class.  If you want to specialize the constraints, for example add a constraint if an element occurs at top level, you have to use a new class for that instance.  Amara 2.x does provide handy facilities to make this easier:

{{{#!code python
node.xml_specialize_model()                  #Clone the node using a new node class that's a copy of the original constraints; substitute the node in place wit the clone, and return the clone.
node.xml_specialize_model(replace=False)     #Clone the node using a new node class that's a copy of the original constraints; Do not replace the node in with the clone, and return the clone.
node.xml_specialize_model(newclass)          #Clone the node using the provided node class.  This will throw an exception if the clone does not meet the constraints defined in newclass. Return the clone.
}}}

You can get a class to pass in using the usual `node.__class__`.

=== Disambiguation rules ===

The rules for disambiguation when converting XML to Python names have been refined.  First of all known names get precedence over unknown names.  By default, if there is information in the model about an element or attribute, and another element or attribute is found which would result in the same Python name, the latter is mangled e.g. with a trailing `_`.

{{{#!code python
<a.1 b.1=""><b.1/></a.1>
}}}

If you parse the above document and the class for a.1 has b.1 among known attributes, and not a known element b.1, assuming it's an open model (i.e. no constraints forbid unknown elements), the resulting binding would have a_1.b_1 as the binding of the attribute rather than the element.

You can also specify how disambiguation proceeds.  You could do so in Amara 1.x, with much difficulty.  In Amara 2.x, it's a matter of specializing the python_name() method.  You could for example prepend "xhtml_" to the Python name of all elements in the XHTML namespace.

{{{#!code python
}}}


= XPath =

Most people will now use the convenience methods on Domlette nodes.

{{{#!code python
result = node.xml_select(expr)
}}}

`node` is used for XPath context.  You can tweak any other parts of the context by providing a context object.  `result` is one of the objects that map the XPath data model to Python.

{{{#!code python
ctx = amara.xpath.context(prefixes={u'html': u'http://www.w3.org/1999/xhtml'})
result = node.xml_select(u'/html:html/html:head/html:title', context=ctx)
}}}

Note: if you specify context node for ctx it overrides the `node` used to call `xml_select`.  You can also use the `evaluate()` method of a amara.xpath.context object.  Pass it the XPath expression string (unicode) to execute.  The above code is equivalent to:

{{{#!code python
ctx = amara.xpath.context(node, prefixes={u'html': u'http://www.w3.org/1999/xhtml'})
result ctx.evaluate(u'/html:html/html:head/html:title')
}}}

There is no longer a global function to evaluate XPath (the old Ft.Xml.XPath.Evaluate).

= XSLT =

There is a similar convenience method for XSLT

{{{#!code python
result node.xml_transform(transforms, params=None, writer=None) ##, use_pis=True
}}}

 * transforms is either a single inputsource or an iterator of inputsources representing the XSLT
 * params is what used to be called topLevelParams
 * use_pis is the inverse of what used to be ignorePis
 * the old outputStream is now replaced by creating a generic writer object on which the user only sets the stream attribute

The result is an instance of one of the subclasses of `amara.xslt.result`.  These are `stringresult`, `streamresult`, and `treeresult` Key properties:

 `result.stream` :: stream buffer of the processor #Not available on stringresult and treeresult instances
 `result.method :: xsl:method encoding parameter
 `result.encoding` :: xsl:output encoding parameter
 `result.media_type` :: xsl:output mediaType parameter
 `result.parameters` :: all other parameters set during transform execution

##Other xsl:output parameters are similarly available.

There is also the global transform API:

{{{#!code python
from amara.xslt import transform
result transform(source, transforms, params=None) ##, use_pis=True
}}}

You can specialize the result, for example to set an output stream:

{{{#!code python
from amara.xslt import transform, streamresult
r = streamresult(sys.stderr, u'http://example.org/myresult') #The URI passed in is the base URI of the result, particularly used for EXSLT document element
new_result = transform(source, transforms, params=None, result=r)
}}}

<!> The result returned to you may not be the same object that you passed in

== Setting up parameters ==

There is a new function `amara.xpath.parameterize`, which takes a dictionary and turns it into a set of parameters suitable for passing into an XSLT transform.  It's basically a convenience function to make it fairly easy to pass Python data into transforms.

{{{#!code python
from amara import parse
from amara.xpath.util import parameterize
doc = parse('<monty spam="1"><python/></monty>')
e1 = doc.documentElement
e2 = e1.firstChild  #doc.xml_select(u'//python')
a1 = e1.getAttributeNodeNS(None, u'spam')  #e1.xml_select(u'@spam')
D = {'p1': 1, 'p2': e1, 'p3': e2, 'p4': a1}
print parameterize(D)

#Result is something like
#{u'p2': <Element at 0x63cc30: name u'monty', 1 attributes, 1 children>,
#  u'p3': <Element at 0x63cc70: name u'python', 0 attributes, 0 children>,
#  u'p1': 1, u'p4': <Attr at 0x63e260: name u'spam', value u'1'>}
}}}

== The detailed API ==

Some users will need closer control.  Usually this will be for those who want to get a performance boost by reusing processor objects.

{{{#!code python
proc = amara.xslt.processor()
proc.append_transform(transform) #transform can be file, URI, stream or string
result = proc.run(source1) #source1 can be file, URI, stream or string
print result.stream.read()
#Reuse the processor
result = proc.run(source2, params={u'name': u'Joe'})
print result.stream.read()
}}}

== XSLT on non-root nodes ==

The new API allows you to run XSLT on a non-root node.  

{{{#!code python
elem.xml_transform(source, tr) # XSLT starts with elem as initial context
}}}

In this case the initial context for template dispatch will be `elem`, as the sole item in the node list, with position of 1.  In plain English that's probably exactly what you'd expect.  The same goes for global variables and parameters.

For the XSLT lawyers out there, we in effect generate an implied root node with that element as the only child in this case.

And yes, you can always do things the traditional way by navigating to the root node yourself:

{{{#!code python
elem.rootnode.xml_transform(source, tr) # XSLT starts with root of elem as initial context
}}}

== Extension functions and elements ==

See: [[Amara2/XSLT_Extensions]]

= Generating XML =

== Struct writer ==

...Add link here...

{{{#!code python
}}}

{{{#!code python
}}}

= XUpdate =

See [[Amara2/XUpdate]]

= See also =

 * Some examples at [[Amara2/Scratchpad]]

= Notes =

 * See [[Amara2/Whatsnew/Scratch]]

