#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

#define Element_VerifyState(ob)                                     \
  if (!Element_Check(ob) ||                                         \
      Element_GET_NAMESPACE_URI(ob) == NULL ||                      \
      Element_GET_LOCAL_NAME(ob) == NULL ||                         \
      Element_GET_NODE_NAME(ob) == NULL ||                          \
      Element_GET_ATTRIBUTES(ob) == NULL) {                         \
     DOMException_InvalidStateErr("Element in inconsistent state"); \
     return NULL;                                                   \
  }

static PyObject *shared_empty_attributes;

Py_LOCAL_INLINE(int)
element_init(ElementObject *self, PyObject *namespaceURI, 
             PyObject *qualifiedName, PyObject *localName)
{
  if ((self == NULL || !Element_Check(self)) ||
      (namespaceURI == NULL || !XmlString_NullCheck(namespaceURI)) ||
      (qualifiedName == NULL || !XmlString_Check(qualifiedName)) ||
      (localName == NULL || !XmlString_Check(localName))) {
    PyErr_BadInternalCall();
    return -1;
  }

  Py_INCREF(namespaceURI);
  self->namespaceURI = namespaceURI;

  Py_INCREF(localName);
  self->localName = localName;

  Py_INCREF(qualifiedName);
  self->nodeName = qualifiedName;

  Py_INCREF(shared_empty_attributes);
  self->attributes = shared_empty_attributes;

  return 0;
}

Py_LOCAL_INLINE(PyObject *)
build_attr_key(AttrObject *attr)
{
  PyObject *key;
  PyObject *local;

  switch (PyObject_RichCompareBool(Attr_GET_NAMESPACE_URI(attr),
                                   g_xmlnsNamespace, Py_EQ)) {
  case 0:
    /* normal attribute */
    local = Attr_GET_LOCAL_NAME(attr);
    break;
  case 1:
    /* namespace attribute */
    if (PyUnicode_AS_UNICODE(Attr_GET_NODE_NAME(attr))[5] == ':') {
      /* xmlns:prefix = 'namespaceURI' */
      local = Attr_GET_LOCAL_NAME(attr);
    }
    else {
      /* xmlns = 'namespaceURI' */
      local = Py_None;
    }
    break;
  default:
    /* error */
    return NULL;
  }

  key = PyTuple_New(2);

  Py_INCREF(Attr_GET_NAMESPACE_URI(attr));
  PyTuple_SET_ITEM(key, 0, Attr_GET_NAMESPACE_URI(attr));

  Py_INCREF(local);
  PyTuple_SET_ITEM(key, 1, local);

  return key;
}

/** Public C API ******************************************************/

ElementObject *Element_New(PyObject *namespaceURI,
                           PyObject *qualifiedName,
                           PyObject *localName)
{
  ElementObject *self;

  self = Node_NewContainer(ElementObject, &DomletteElement_Type);
  if (self != NULL) {
    if (element_init(self, namespaceURI, qualifiedName, localName) < 0) {
      Node_Del(self);
      return NULL;
    }
  }

  PyObject_GC_Track(self);

  return self;
}

/* returns a new reference */
AttrObject *Element_SetAttributeNS(ElementObject *self,
                                   PyObject *namespaceURI,
                                   PyObject *qualifiedName,
                                   PyObject *localName,
                                   PyObject *value)
{
  PyObject *attributes, *key;
  AttrObject *attr;

  Element_VerifyState(self);

  attributes = self->attributes;
  if (attributes == shared_empty_attributes) {
    attributes = PyDict_New();
    if (attributes == NULL) return NULL;
    Py_DECREF(self->attributes);
    self->attributes = attributes;
  }

  /* new reference */
  attr = Attr_New(namespaceURI, qualifiedName, localName, value);
  if (attr == NULL) return NULL;
  Py_INCREF(self);
  assert(Node_GET_PARENT(attr) == NULL);
  Node_SET_PARENT(attr, (NodeObject *) self);

  key = build_attr_key(attr);
  if (key == NULL) {
    Py_DECREF(attr);
    return NULL;
  }
  if (PyDict_SetItem(attributes, key, (PyObject *)attr) < 0) {
    Py_DECREF(key);
    Py_DECREF(attr);
    return NULL;
  }
  return attr;
}

/* returns a borrowed reference */
PyObject *Element_GetAttributeNodeNS(ElementObject *self,
                                     PyObject *namespaceURI,
                                     PyObject *localName)
{
  /* Returns a borrowed ref */
  PyObject *key;
  PyObject *attr;

  Element_VerifyState(self);

  Py_INCREF(namespaceURI);
  Py_INCREF(localName);
  /* steals reference */
  key = PyTuple_New(2);
  PyTuple_SetItem(key, 0, namespaceURI);
  PyTuple_SetItem(key, 1, localName);

  attr = PyDict_GetItem(self->attributes, key);
  Py_DECREF(key);

  return attr ? attr : Py_None;
}

/* returns a new reference */
PyObject *Element_SetAttributeNodeNS(ElementObject *self, AttrObject *attr)
{
  PyObject *key, *oldAttr;

  Element_VerifyState(self);

  /* Set the new attribute */
  if (self->attributes == shared_empty_attributes) {
    PyObject *attrs = PyDict_New();
    if (attrs == NULL) return NULL;
    Py_DECREF(self->attributes);
    self->attributes = attrs;
  }

  /* Get the return value */
  key = build_attr_key(attr);
  oldAttr = PyDict_GetItem(self->attributes, key);
  if (PyDict_SetItem(self->attributes, key, (PyObject *)attr) < 0) {
    Py_DECREF(key);
    return NULL;
  }
  Py_DECREF(key);

  /* Set the new attributes owner */
  Py_XDECREF(Node_GET_PARENT(attr));
  Py_INCREF(self);
  Node_SET_PARENT(attr, (NodeObject *)self);

  if (oldAttr == NULL) {
    /* new attribute */
    oldAttr = Py_None;
  } else {
    /* Reset the removed attributes owner */
    Py_DECREF(Node_GET_PARENT(oldAttr));
    Node_SET_PARENT(oldAttr, NULL);
  }

  Py_INCREF(oldAttr);
  return oldAttr;
}

ElementObject *Element_CloneNode(PyObject *node, int deep)
{
  ElementObject *element;
  PyObject *namespaceURI, *localName, *qualifiedName;
  PyObject *attributes;
  Py_ssize_t i, count;

  namespaceURI = PyObject_GetAttrString(node, "namespaceURI");
  namespaceURI = XmlString_FromObjectInPlace(namespaceURI);
  qualifiedName = PyObject_GetAttrString(node, "nodeName");
  qualifiedName = XmlString_FromObjectInPlace(qualifiedName);
  localName = PyObject_GetAttrString(node, "localName");
  localName = XmlString_FromObjectInPlace(localName);

  /* attributes are cloned regardless of the deep argument */
  attributes = PyObject_GetAttrString(node, "attributes");
  if (attributes) {
    /* get the actual attribute nodes from the attributes mapping */
    PyObject *values = PyMapping_Values(attributes);
    Py_DECREF(attributes);
    attributes = values;
  }
  if (namespaceURI == NULL || qualifiedName == NULL || localName == NULL ||
      attributes == NULL) {
    Py_XDECREF(attributes);
    Py_XDECREF(localName);
    Py_XDECREF(qualifiedName);
    Py_XDECREF(namespaceURI);
    return NULL;
  }

  /* We now have everything we need to create a shallow copy, do it */
  element = Element_New(namespaceURI, qualifiedName, localName);

  /* Done with these */
  Py_DECREF(namespaceURI);
  Py_DECREF(qualifiedName);
  Py_DECREF(localName);

  if (element == NULL) {
    Py_DECREF(attributes);
    return NULL;
  }

  /* copy the attributes */
  count = PySequence_Length(attributes);
  for (i = 0; i < count; i++) {
    PyObject *attr, *value;

    attr = PySequence_GetItem(attributes, i);
    if (attr == NULL) {
      Py_DECREF(element);
      Py_DECREF(attributes);
      return NULL;
    }

    namespaceURI = PyObject_GetAttrString(attr, "namespaceURI");
    namespaceURI = XmlString_FromObjectInPlace(namespaceURI);
    qualifiedName = PyObject_GetAttrString(attr, "nodeName");
    qualifiedName = XmlString_FromObjectInPlace(qualifiedName);
    localName = PyObject_GetAttrString(attr, "localName");
    localName = XmlString_FromObjectInPlace(localName);
    value = PyObject_GetAttrString(attr, "value");
    value = XmlString_FromObjectInPlace(value);
    Py_DECREF(attr);
    if (namespaceURI == NULL || localName == NULL || qualifiedName == NULL ||
        value == NULL) {
      Py_XDECREF(value);
      Py_XDECREF(qualifiedName);
      Py_XDECREF(localName);
      Py_XDECREF(namespaceURI);
      Py_DECREF(element);
      Py_DECREF(attributes);
      return NULL;
    }

    attr = (PyObject *)Element_SetAttributeNS(element, namespaceURI,
                                              qualifiedName, localName, value);
    Py_DECREF(value);
    Py_DECREF(localName);
    Py_DECREF(qualifiedName);
    Py_DECREF(namespaceURI);
    if (attr == NULL) {
      Py_DECREF(element);
      Py_DECREF(attributes);
      return NULL;
    }
    Py_DECREF(attr);
  }
  Py_DECREF(attributes);

  if (deep) {
    PyObject *childNodes;

    childNodes = PyObject_GetAttrString(node, "childNodes");
    if (childNodes == NULL) {
      Py_DECREF(element);
      return NULL;
    }
    count = PySequence_Length(childNodes);
    for (i = 0; i < count; i++) {
      PyObject *child;
      NodeObject *cloned_child;

      child = PySequence_GetItem(childNodes, i);
      if (child == NULL) {
        Py_DECREF(childNodes);
        Py_DECREF(element);
        return NULL;
      }

      cloned_child = Node_CloneNode(child, deep);
      Py_DECREF(child);
      if (cloned_child == NULL) {
        Py_DECREF(childNodes);
        Py_DECREF(element);
        return NULL;
      }

      if (Node_AppendChild((NodeObject *)element, cloned_child) < 0) {
        Py_DECREF(cloned_child);
        Py_DECREF(childNodes);
        Py_DECREF(element);
        return NULL;
      }
      Py_DECREF(cloned_child);
    }
    Py_DECREF(childNodes);
  }

  return element;
}

/** Python Methods ****************************************************/

static char element_getAttributeNodeNS_doc[] =
"Retrieves an Attr node by local name and namespace URI.";

static PyObject *element_getAttributeNodeNS(ElementObject *self,
                                            PyObject *args)
{
  PyObject *namespaceURI, *localName;
  PyObject *attr;

  Element_VerifyState(self);

  if (!PyArg_ParseTuple(args, "OO:getAttributeNodeNS",
                        &namespaceURI, &localName))
    return NULL;

  namespaceURI = XmlString_ConvertArgument(namespaceURI, "namespaceURI", 1);
  if (namespaceURI == NULL) {
    return NULL;
  }

  localName = XmlString_ConvertArgument(localName, "localName", 0);
  if (localName == NULL) {
    Py_DECREF(namespaceURI);
    return NULL;
  }

  attr = Element_GetAttributeNodeNS(self, namespaceURI, localName);
  Py_DECREF(namespaceURI);
  Py_DECREF(localName);

  Py_INCREF(attr);
  return attr;
}

static char element_getAttributeNS_doc[] =
"Retrieves an attribute value by local name and namespace URI.";

static PyObject *element_getAttributeNS(ElementObject *self, PyObject *args)
{
  PyObject *namespaceURI, *localName;
  PyObject *attr;

  Element_VerifyState(self);

  if (!PyArg_ParseTuple(args, "OO:getAttributeNS", &namespaceURI, &localName))
    return NULL;

  namespaceURI = XmlString_ConvertArgument(namespaceURI, "namespaceURI", 1);
  if (namespaceURI == NULL) {
    return NULL;
  }

  localName = XmlString_ConvertArgument(localName, "localName", 0);
  if (localName == NULL) {
    Py_DECREF(namespaceURI);
    return NULL;
  }

  attr = Element_GetAttributeNodeNS(self, namespaceURI, localName);
  Py_DECREF(namespaceURI);
  Py_DECREF(localName);

  if (attr == Py_None) {
    /* empty unicode string */
    return PyUnicode_FromUnicode(NULL, 0);
  } else {
    Py_INCREF(Attr_GET_NODE_VALUE(attr));
    return Attr_GET_NODE_VALUE(attr);
  }
}

static char element_hasAttributeNS_doc[] =
"Returns True when an attribute with a given local name and namespace URI\n\
is specified on this element or has a default value, False otherwise.";

static PyObject *element_hasAttributeNS(ElementObject *self, PyObject *args)
{
  PyObject *namespaceURI, *localName;
  PyObject *attr;

  Element_VerifyState(self);

  if (!PyArg_ParseTuple(args, "OO:hasAttributeNS", &namespaceURI, &localName))
    return NULL;

  namespaceURI = XmlString_ConvertArgument(namespaceURI, "namespaceURI", 1);
  if (namespaceURI == NULL) {
    return NULL;
  }

  localName = XmlString_ConvertArgument(localName, "localName", 0);
  if (localName == NULL) {
    Py_DECREF(namespaceURI);
    return NULL;
  }

  attr = Element_GetAttributeNodeNS(self, namespaceURI, localName);
  Py_DECREF(namespaceURI);
  Py_DECREF(localName);

  if (attr == Py_None) {
    Py_INCREF(Py_False);
    return Py_False;
  }

  Py_INCREF(Py_True);
  return Py_True;
}

static char element_setAttributeNS_doc[] =
"Adds a new attribute.  If an attribute with the same local name and\n\
namespace URI is already present on the element, its prefix is changed\n\
to be the prefix part of the qualifiedName, and its value is changed to\n\
be the value parameter.";

static PyObject *element_setAttributeNS(ElementObject *self, PyObject *args)
{
  PyObject *namespaceURI, *qualifiedName, *value, *prefix, *localName;
  PyObject *attr;

  Element_VerifyState(self);

  if (!PyArg_ParseTuple(args, "OOO:setAttributeNS",
                        &namespaceURI, &qualifiedName, &value))
    return NULL;

  namespaceURI = XmlString_ConvertArgument(namespaceURI, "namespaceURI", 1);
  if (namespaceURI == NULL) {
    return NULL;
  }

  qualifiedName = XmlString_ConvertArgument(qualifiedName, "qualifiedName", 0);
  if (qualifiedName == NULL) {
    Py_DECREF(namespaceURI);
    return NULL;
  }

  value = XmlString_ConvertArgument(value, "value", 0);
  if (value == NULL) {
    Py_DECREF(namespaceURI);
    Py_DECREF(qualifiedName);
    return NULL;
  }

  if (!XmlString_SplitQName(qualifiedName, &prefix, &localName)) {
    Py_DECREF(namespaceURI);
    Py_DECREF(qualifiedName);
    return NULL;
  }

  /* returns new reference */
  attr = (PyObject *)Element_SetAttributeNS(self, namespaceURI, qualifiedName,
                                            localName, value);
  Py_DECREF(namespaceURI);
  Py_DECREF(qualifiedName);
  Py_DECREF(prefix);
  Py_DECREF(localName);
  Py_DECREF(value);

  return attr;
}

static char element_setAttributeNodeNS_doc[] =
"Adds a new attribute. If an attribute with that local name and that\n\
namespace URI is already present in the element, it is replaced by the\n\
new one. Replacing an attribute node by itself has no effect.";

static PyObject *element_setAttributeNodeNS(ElementObject *self,
                                            PyObject *args)
{
  AttrObject *attr;

  Element_VerifyState(self);

  if (!PyArg_ParseTuple(args, "O!:setAttributeNodeNS", &DomletteAttr_Type,
                        &attr))
    return NULL;

  return Element_SetAttributeNodeNS(self, attr);
}

static char element_removeAttributeNode_doc[] =
"Removes the specified attribute node.";

static PyObject *element_removeAttributeNode(ElementObject *self,
                                             PyObject *args)
{
  AttrObject *attr;
  PyObject *key;

  Element_VerifyState(self);

  if (!PyArg_ParseTuple(args, "O!:removeAttributeNode", &DomletteAttr_Type,
                        &attr))
    return NULL;

  key = build_attr_key(attr);
  if (PyDict_DelItem(self->attributes, key) == -1) {
    if (PyErr_ExceptionMatches(PyExc_KeyError)) {
      DOMException_NotFoundErr("attribute not found");
    }
    Py_DECREF(key);
    return NULL;
  }
  Py_DECREF(key);

  /* Reset the removed attributes owner */
  assert(Node_GET_PARENT(attr) == (NodeObject *)self);
  Py_DECREF(Node_GET_PARENT(attr));
  Node_SET_PARENT(attr, NULL);

  Py_INCREF(Py_None);
  return Py_None;
}


static char element_removeAttributeNS_doc[] =
"Removes an attribute by local name and namespace URI.";

static PyObject *element_removeAttributeNS(ElementObject *self, PyObject *args)
{
  PyObject *namespaceURI, *qualifiedName, *prefix, *localName, *key, *attr;

  Element_VerifyState(self);

  if (!PyArg_ParseTuple(args, "OO:removeAttributeNS",
                        &namespaceURI, &qualifiedName))
    return NULL;

  namespaceURI = XmlString_ConvertArgument(namespaceURI, "namespaceURI", 1);
  if (namespaceURI == NULL) {
    return NULL;
  }

  qualifiedName = XmlString_ConvertArgument(qualifiedName, "qualifiedName", 0);
  if (qualifiedName == NULL) {
    Py_DECREF(namespaceURI);
    return NULL;
  }

  if (!XmlString_SplitQName(qualifiedName, &prefix, &localName)) {
    Py_DECREF(namespaceURI);
    Py_DECREF(qualifiedName);
    return NULL;
  }

  /* Done with these */
  Py_DECREF(qualifiedName);
  Py_DECREF(prefix);

  key = PyTuple_New(2);
  /* Let the tuple own these */
  PyTuple_SetItem(key, 0, namespaceURI);
  PyTuple_SetItem(key, 1, localName);

  attr = PyDict_GetItem(self->attributes, key);
  if (attr) {
    assert(Node_GET_PARENT(attr) == (NodeObject *)self);
    /* Unset the parent node relationship */
    Py_DECREF(Node_GET_PARENT(attr));
    Node_SET_PARENT(attr, NULL);

    /* Remove the entry from the attributes mapping */
    if (PyDict_DelItem(self->attributes, key) == -1) {
      Py_DECREF(key);
      return NULL;
    }
  }

  /* Destroy the key */
  Py_DECREF(key);

  Py_INCREF(Py_None);
  return Py_None;
}

#define Element_METHOD(NAME) \
  { #NAME, (PyCFunction) element_##NAME, METH_VARARGS, element_##NAME##_doc }

static PyMethodDef element_methods[] = {
  Element_METHOD(getAttributeNS),
  Element_METHOD(getAttributeNodeNS),
  Element_METHOD(setAttributeNS),
  Element_METHOD(setAttributeNodeNS),
  Element_METHOD(removeAttributeNS),
  Element_METHOD(removeAttributeNode),
  Element_METHOD(hasAttributeNS),
  { NULL }
};

/** Python Members ****************************************************/

#define Element_MEMBER(name, member) \
  { name, T_OBJECT, offsetof(ElementObject, member), RO }

static PyMemberDef element_members[] = {
  Element_MEMBER("tagName", nodeName),
  Element_MEMBER("nodeName", nodeName),
  Element_MEMBER("localName", localName),
  Element_MEMBER("namespaceURI", namespaceURI),
  { NULL }
};

/** Python Computed Members *******************************************/

static PyObject *get_prefix(ElementObject *self, void *arg)
{
  Py_UNICODE *p;
  Py_ssize_t size, i;

  p = PyUnicode_AS_UNICODE(self->nodeName);
  size = PyUnicode_GET_SIZE(self->nodeName);
  for (i = 0; i < size; i++) {
    if (p[i] == ':') {
      return PyUnicode_FromUnicode(p, i);
    }
  }
  Py_INCREF(Py_None);
  return Py_None;
}

static int set_prefix(ElementObject *self, PyObject *v, void *arg)
{
  PyObject *qualifiedName, *prefix;
  Py_ssize_t size;

  prefix = XmlString_ConvertArgument(v, (char *)arg, 1);
  if (prefix == NULL) {
    return -1;
  } else if (prefix == Py_None) {
    Py_DECREF(self->nodeName);
    Py_INCREF(self->localName);
    self->nodeName = self->localName;
    return 0;
  }

  /* rebuild the qualifiedName */
  size = PyUnicode_GET_SIZE(prefix) + 1 + PyUnicode_GET_SIZE(self->localName);
  qualifiedName = PyUnicode_FromUnicode(NULL, size);
  if (qualifiedName == NULL) {
    Py_DECREF(prefix);
    return -1;
  }

  /* copy the prefix to the qualifiedName string */
  size = PyUnicode_GET_SIZE(prefix);
  Py_UNICODE_COPY(PyUnicode_AS_UNICODE(qualifiedName),
                  PyUnicode_AS_UNICODE(prefix), size);
  Py_DECREF(prefix);

  /* add the ':' separator */
  PyUnicode_AS_UNICODE(qualifiedName)[size++] = (Py_UNICODE) ':';

  /* add the localName after the ':' to finish the qualifiedName */
  Py_UNICODE_COPY(PyUnicode_AS_UNICODE(qualifiedName) + size,
                  PyUnicode_AS_UNICODE(self->localName),
                  PyUnicode_GET_SIZE(self->localName));

  Py_DECREF(self->nodeName);
  self->nodeName = qualifiedName;
  return 0;
}

static PyObject *get_attributes(ElementObject *self, void *arg)
{
  return NamedNodeMap_New(self->attributes);
}

static PyObject *get_xpath_attributes(ElementObject *self, void *arg)
{
  PyObject *attributes = PyList_New(0);
  if (attributes != NULL) {
    PyObject *key, *attr;
    Py_ssize_t pos = 0;
    while (PyDict_Next(self->attributes, &pos, &key, &attr)) {
      switch (PyObject_RichCompareBool(Attr_GET_NAMESPACE_URI(attr),
                                       g_xmlnsNamespace, Py_NE)) {
      case 0: /* namespace attribute */
        break;
      case 1: /* normal attribute */
        if (PyList_Append(attributes, attr) == -1) {
          Py_DECREF(attributes);
          return NULL;
        }
        break;
      default: /* error */
        Py_DECREF(attributes);
        return NULL;
      }
    }
  }
  return attributes;
}

static PyObject *get_xpath_namespaces(ElementObject *self, void *arg)
{
  PyObject *namespaces;
  PyObject *nss = Domlette_GetNamespaces((NodeObject *) self);
  if (nss == NULL) return NULL;

  namespaces = PyList_New(0);
  if (namespaces != NULL) {
    PyObject *xns, *prefix, *uri;
    Py_ssize_t pos = 0;
    while (PyDict_Next(nss, &pos, &prefix, &uri)) {
      xns = (PyObject *) XPathNamespace_New(self, prefix, uri);
      if (xns == NULL) {
        Py_DECREF(nss);
        Py_DECREF(namespaces);
        return NULL;
      }
      if (PyList_Append(namespaces, xns) == -1) {
        Py_DECREF(nss);
        Py_DECREF(namespaces);
        Py_DECREF(xns);
        return NULL;
      }
      Py_DECREF(xns);
    }
  }
  Py_DECREF(nss);
  return namespaces;
}

static PyGetSetDef element_getset[] = {
  { "prefix", (getter)get_prefix, (setter)set_prefix, NULL, "prefix" },
  { "attributes", (getter) get_attributes },
  /* XPath-specific accessors */
  { "xpathAttributes", (getter) get_xpath_attributes },
  { "xpathNamespaces", (getter) get_xpath_namespaces },
  { NULL }
};

/** Type Object ********************************************************/

static void element_dealloc(ElementObject *self)
{
  PyObject_GC_UnTrack((PyObject *) self);
  Py_CLEAR(self->namespaceURI);
  Py_CLEAR(self->localName);
  Py_CLEAR(self->nodeName);
  Py_CLEAR(self->attributes);
  Node_Del(self);
}

static PyObject *element_repr(ElementObject *element)
{
  PyObject *repr, *name = PyObject_Repr(element->nodeName);
  if (name == NULL) return NULL;

  repr = PyString_FromFormat("<Element at %p: name %s, "
                             "%" PY_FORMAT_SIZE_T "d attributes, "
                             "%" PY_FORMAT_SIZE_T "d children>",
                             element, PyString_AsString(name),
                             PyDict_Size(element->attributes),
                             ContainerNode_GET_COUNT(element));
  Py_DECREF(name);
  return repr;
}

static int element_traverse(ElementObject *self, visitproc visit, void *arg)
{
  if (self->attributes != shared_empty_attributes) {
    Py_VISIT(self->attributes);
  }
  return DomletteNode_Type.tp_traverse((PyObject *)self, visit, arg);
}

static int element_clear(ElementObject *self)
{
  Py_CLEAR(self->attributes);
  return DomletteNode_Type.tp_clear((PyObject *)self);
}

static PyObject *element_new(PyTypeObject *type, PyObject *args,
                             PyObject *kwds)
{
  PyObject *namespaceURI, *qualifiedName, *prefix, *localName;
  static char *kwlist[] = { "namespaceURI", "qualifiedName", NULL };
  ElementObject *self;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO:Element", kwlist,
                                   &namespaceURI, &qualifiedName)) {
    return NULL;
  }

  namespaceURI = XmlString_ConvertArgument(namespaceURI, "namespaceURI", 1);
  if (namespaceURI == NULL) return NULL;

  qualifiedName = XmlString_ConvertArgument(qualifiedName, "qualifiedName", 0);
  if (qualifiedName == NULL) {
    Py_DECREF(namespaceURI);
    return NULL;
  }

  if (!XmlString_SplitQName(qualifiedName, &prefix, &localName)) {
    Py_DECREF(namespaceURI);
    Py_DECREF(qualifiedName);
    return NULL;
  }

  if (namespaceURI == Py_None && prefix != Py_None) {
    DOMException_NamespaceErr("prefix requires non-null namespaceURI");
    Py_DECREF(namespaceURI);
    Py_DECREF(prefix);
    return NULL;
  }
  Py_DECREF(prefix);

  if (type != &DomletteElement_Type) {
    self = Element(type->tp_alloc(type, 0));
    if (self != NULL) {
      _Node_INIT_CONTAINER(self);
      if (element_init(self, namespaceURI, qualifiedName, localName) < 0) {
        Py_DECREF(self);
        self = NULL;
      }
    }
  } else {
    self = Element_New(namespaceURI, qualifiedName, localName);
  }
  Py_DECREF(namespaceURI);
  Py_DECREF(qualifiedName);
  Py_DECREF(localName);

  return (PyObject *) self;
}

static char element_doc[] = "\
Element(namespaceURI, qualifiedName) -> Element object\n\
\n\
The Element interface represents an element in an XML document.";

PyTypeObject DomletteElement_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "Element",
  /* tp_basicsize      */ sizeof(ElementObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) element_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) element_repr,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) 0,
  /* tp_as_mapping     */ (PyMappingMethods *) 0,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) 0,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT |
                           Py_TPFLAGS_BASETYPE |
                           Py_TPFLAGS_HAVE_GC),
  /* tp_doc            */ (char *) element_doc,
  /* tp_traverse       */ (traverseproc) element_traverse,
  /* tp_clear          */ (inquiry) element_clear,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) element_methods,
  /* tp_members        */ (PyMemberDef *) element_members,
  /* tp_getset         */ (PyGetSetDef *) element_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) element_new,
  /* tp_free           */ 0,
};

/** Module Interface **************************************************/

int DomletteElement_Init(PyObject *module)
{
  PyObject *value;

  DomletteElement_Type.tp_base = &DomletteNode_Type;
  if (PyType_Ready(&DomletteElement_Type) < 0)
    return -1;

  value = PyInt_FromLong(ELEMENT_NODE);
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(DomletteElement_Type.tp_dict, "nodeType", value))
    return -1;
  Py_DECREF(value);

  shared_empty_attributes = PyDict_New();
  if (shared_empty_attributes == NULL) return -1;

  Py_INCREF(&DomletteElement_Type);
  return PyModule_AddObject(module, "Element",
                            (PyObject*) &DomletteElement_Type);
}


void DomletteElement_Fini(void)
{
  Py_DECREF(shared_empty_attributes);

  PyType_CLEAR(&DomletteElement_Type);
}
