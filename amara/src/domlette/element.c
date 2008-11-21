#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

static PyObject *attribute_factory_string;
static PyObject *xml_string;
static PyObject *xmlns_string;
static PyObject *xml_namespace;
static PyObject *xmlns_namespace;

Py_LOCAL_INLINE(ElementObject *)
element_init(ElementObject *self, PyObject *namespaceURI, 
             PyObject *qualifiedName, PyObject *localName)
{
  assert(self && Element_Check(self));
  if ((namespaceURI == NULL || !XmlString_NullCheck(namespaceURI)) ||
      (qualifiedName == NULL || !XmlString_Check(qualifiedName)) ||
      (localName == NULL || !XmlString_Check(localName))) {
    PyErr_BadInternalCall();
    Py_DECREF(self);
    return NULL;
  }
  Py_INCREF(namespaceURI);
  self->namespaceURI = namespaceURI;
  Py_INCREF(localName);
  self->localName = localName;
  Py_INCREF(qualifiedName);
  self->qname = qualifiedName;
  self->namespaces = NULL;
  self->attributes = NULL;
  return self;
}

Py_LOCAL_INLINE(PyObject *)
lookup_prefix(ElementObject *self, PyObject *namespace)
{
  NodeObject *current = (NodeObject *)self;
  PyObject *nodemap, *name, *value;
  Py_ssize_t pos;
  NamespaceObject *node;

  do {
    nodemap = Element_NAMESPACES(current);
    if (nodemap != NULL) {
      /* process the element's declared namespaces */
      pos = 0;
      while ((node = NamespaceMap_Next(nodemap, &pos))) {
        /* namespace attribute */
        name = Namespace_GET_NAME(node);
        value = Namespace_GET_VALUE(node);
        if (PyUnicode_GET_SIZE(value) == 0) {
          /* empty string; remove prefix binding */
          /* NOTE: in XML Namespaces 1.1 it would be possible to do this
              for all prefixes, for now just the default namespace */
          if (name == Py_None)
            continue;
        }
        switch (PyObject_RichCompareBool(namespace, value, Py_EQ)) {
        case 0:
          break;
        case 1:
          return name;
        default:
          return NULL;
        }
      }
    }
    current = Node_GET_PARENT(current);
  } while (current && Element_Check(current));

  PyErr_SetString(PyExc_ValueError, "undeclared namespace uri");
  return NULL;
}

Py_LOCAL_INLINE(PyObject *)
lookup_namespace(ElementObject *self, PyObject *prefix)
{
  NodeObject *current = (NodeObject *)self;
  PyObject *nodemap, *name, *namespace;
  Py_ssize_t pos;
  NamespaceObject *node;

  do {
    nodemap = Element_NAMESPACES(current);
    if (nodemap != NULL) {
      /* process the element's declared namespaces */
      pos = 0;
      while ((node = NamespaceMap_Next(nodemap, &pos))) {
        /* namespace attribute */
        name = Namespace_GET_NAME(node);
        namespace = Namespace_GET_VALUE(node);
        if (PyUnicode_GET_SIZE(namespace) == 0) {
          /* empty string; remove prefix binding */
          /* NOTE: in XML Namespaces 1.1 it would be possible to do this
              for all prefixes, for now just the default namespace */
          if (name == Py_None)
            namespace = Py_None;
          else
            continue;
        }
        switch (PyObject_RichCompareBool(prefix, name, Py_EQ)) {
        case 0:
          break;
        case 1:
          return namespace;
        default:
          return NULL;
        }
      }
    }
    current = Node_GET_PARENT(current);
  } while (current && Element_Check(current));

  /* if the default namespace is not declared, then it is the null namespace */
  if (prefix == Py_None)
    return Py_None;

  PyErr_SetString(PyExc_ValueError, "undeclared prefix");
  return NULL;
}

Py_LOCAL_INLINE(int)
update_namespaces(ElementObject *self)
{
#if 0
  NodeObject *current = (NodeObject *)self;
  PyObject *nodemap, *name, *namespace;
  Py_ssize_t pos;
  NamespaceObject *node;

  do {
    nodemap = Element_NAMESPACES(current);
    if (nodemap != NULL) {
      /* process the element's declared namespaces */
      pos = 0;
      while ((node = NamespaceMap_Next(nodemap, &pos))) {
        /* namespace attribute */
        name = Namespace_GET_NAME(node);
        namespace = Namespace_GET_VALUE(node);
        if (PyUnicode_GET_SIZE(namespace) == 0) {
          /* empty string; remove prefix binding */
          /* NOTE: in XML Namespaces 1.1 it would be possible to do this
              for all prefixes, for now just the default namespace */
          if (name == Py_None)
            namespace = Py_None;
          else
            continue;
        }
        switch (PyObject_RichCompareBool(prefix, name, Py_EQ)) {
        case 0:
          break;
        case 1:
          return namespace;
        default:
          return NULL;
        }
      }
    }
    current = Node_GET_PARENT(current);
  } while (current && Element_Check(current));
#endif
  return 0;
}

Py_LOCAL_INLINE(PyObject *)
build_qname(PyObject *prefix, PyObject *local)
{
  PyObject *qualifiedName;
  Py_ssize_t size;

  assert(PyUnicode_Check(prefix) && PyUnicode_Check(local));

  size = PyUnicode_GET_SIZE(prefix) + 1 + PyUnicode_GET_SIZE(local);
  qualifiedName = PyUnicode_FromUnicode(NULL, size);
  if (qualifiedName) {
    /* copy the prefix to the qualifiedName string */
    size = PyUnicode_GET_SIZE(prefix);
    Py_UNICODE_COPY(PyUnicode_AS_UNICODE(qualifiedName),
                    PyUnicode_AS_UNICODE(prefix), size);
    /* add the ':' separator */
    PyUnicode_AS_UNICODE(qualifiedName)[size++] = (Py_UNICODE) ':';
    /* add the localName after the ':' to finish the qualifiedName */
    Py_UNICODE_COPY(PyUnicode_AS_UNICODE(qualifiedName) + size,
                    PyUnicode_AS_UNICODE(local), PyUnicode_GET_SIZE(local));
  }
  return qualifiedName;
}

/** Public C API ******************************************************/

ElementObject *Element_New(PyObject *namespaceURI,
                           PyObject *qualifiedName,
                           PyObject *localName)
{
  ElementObject *self;

  self = Container_New(ElementObject, &DomletteElement_Type);
  if (self != NULL) {
    self = element_init(self, namespaceURI, qualifiedName, localName);
  }
  return self;
}

/* returns a new reference */
NamespaceObject *
Element_AddNamespace(ElementObject *self, PyObject *prefix, PyObject *namespace)
{
  PyObject *namespaces;
  NamespaceObject *node;

  /* OPT: ensure the NamespaceMap exists */
  namespaces = self->namespaces;
  if (namespaces == NULL) {
    namespaces = self->namespaces = NamespaceMap_New(self);
    if (namespaces == NULL) 
      return NULL;
  }
  /* new reference */
  node = Namespace_New(prefix, namespace);
  if (node != NULL) {
    if (NamespaceMap_SetNode(namespaces, node) < 0)
      Py_CLEAR(node);
  }
  return node;
}

/* returns 0 on success, -1 on error */
int
Element_SetNamespace(ElementObject *self, NamespaceObject *node)
{
  PyObject *namespaces;

  /* OPT: ensure the NamespaceMap exists */
  namespaces = self->namespaces;
  if (namespaces == NULL) {
    namespaces = self->namespaces = NamespaceMap_New(self);
    if (namespaces == NULL) 
      return -1;
  }
  if (!Namespace_Check(node)) {
    PyErr_Format(PyExc_TypeError,
                 "can only add namespaces to %s.xmlns_attributes, not %s",
                 self->ob_type->tp_name, node->ob_type->tp_name);
    return -1;
  }
  /* add the namespace node */
  return NamespaceMap_SetNode(namespaces, node);
}

/* returns a new reference */
AttrObject *
Element_AddAttribute(ElementObject *self, PyObject *namespaceURI,
                     PyObject *qualifiedName, PyObject *localName,
                     PyObject *value)
{
  PyObject *attributes, *factory;
  AttrObject *node;

  if (qualifiedName == NULL) {
    if (namespaceURI == Py_None) {
      qualifiedName = localName;
      Py_INCREF(localName);
    } else {
      PyObject *prefix = lookup_prefix(self, namespaceURI);
      if (prefix == NULL)
        return NULL;
      if (prefix == Py_None) {
        PyErr_SetString(PyExc_ValueError,
                        "cannot use default namespace for attributes");
        return NULL;
      }
      qualifiedName = build_qname(prefix, localName);
      if (qualifiedName == NULL)
        return NULL;
    }
  }

  /* OPT: ensure the AttributeMap exists */
  attributes = self->attributes;
  if (attributes == NULL) {
    attributes = self->attributes = AttributeMap_New(self);
    if (attributes == NULL) return NULL;
  }
  /* find the factory used to create the new attribute node */
  if (!Element_CheckExact(self)) {
    factory = PyObject_GetAttr((PyObject *)self, attribute_factory_string);
    if (factory == NULL)
      return NULL;
    if (factory == (PyObject *)&DomletteAttr_Type)
      Py_CLEAR(factory);
  } else {
    factory = NULL;
  }
  /* create the attribute */
  if (factory == NULL) {
    node = Attr_New(namespaceURI, qualifiedName, localName, value);
  } else {
    node = (AttrObject *)PyObject_CallFunctionObjArgs(factory, namespaceURI,
                                                      qualifiedName, value,
                                                      NULL);
    Py_DECREF(factory);
    if (node && !Attr_Check(node)) {
      PyErr_Format(PyExc_TypeError,
                    "xml_attribute_factory should return attribute, not %s",
                    node->ob_type->tp_name);
      Py_DECREF(node);
      return NULL;
    }
  }
  /* save the node in the attributemap */
  if (node != NULL) {
    if (AttributeMap_SetNode(attributes, node) < 0) {
      Py_DECREF(node);
      return NULL;
    }
  }
  return node;
}

/* returns a borrowed reference */
AttrObject *
Element_GetAttribute(ElementObject *self, PyObject *namespaceURI,
                     PyObject *localName)
{
  PyObject *attributes;
  AttrObject *node;

  /* OPT: ensure the AttributeMap exists */
  attributes = self->attributes;
  if (attributes == NULL) {
    attributes = self->attributes = AttributeMap_New(self);
    if (attributes == NULL) return NULL;
  }
  /* new reference */
  node = AttributeMap_GetNode(attributes, namespaceURI, localName);
  Py_XINCREF(node);
  return node;
}

int
Element_SetAttribute(ElementObject *self, AttrObject *attr)
{
  PyObject *attributes;

  /* OPT: ensure the AttributeMap exists */
  attributes = self->attributes;
  if (attributes == NULL) {
    attributes = self->attributes = AttributeMap_New(self);
    if (attributes == NULL)
      return -1;
  }
  if (!Attr_Check(attr)) {
    PyErr_Format(PyExc_TypeError,
                 "can only add attributes to %s.xml_attributes, not %s",
                 self->ob_type->tp_name, attr->ob_type->tp_name);
    return -1;
  }
  /* Add the attribute */
  return AttributeMap_SetNode(attributes, attr);
}

/* returns a new reference */
PyObject *
Element_InscopeNamespaces(ElementObject *self)
{
  NodeObject *current = (NodeObject *)self;
  PyObject *namespaces, *nodemap, *name, *value;
  Py_ssize_t pos;
  NamespaceObject *node;

  namespaces = NamespaceMap_New(self);
  if (namespaces == NULL) 
    return NULL;

  /* add the XML namespace */
  node = Namespace_New(xml_string, xml_namespace);
  if (node == NULL) {
    Py_DECREF(namespaces);
    return NULL;
  }
  if (NamespaceMap_SetNode(namespaces, node) < 0) {
    Py_DECREF(node);
    Py_DECREF(namespaces);
    return NULL;
  }
  Py_DECREF(node);

  do {
    nodemap = Element_NAMESPACES(current);
    if (nodemap != NULL) {
      /* process the element's declared namespaces */
      pos = 0;
      while ((node = NamespaceMap_Next(nodemap, &pos))) {
        /* namespace attribute */
        name = Namespace_GET_NAME(node);
        value = Namespace_GET_VALUE(node);
        if (PyUnicode_GET_SIZE(value) == 0) {
          /* empty string; remove prefix binding */
          /* NOTE: in XML Namespaces 1.1 it would be possible to do this
              for all prefixes, for now just the default namespace */
          if (name == Py_None)
            continue;
        }
        /* add the declaration if prefix is not already defined */
        if (NamespaceMap_GetNode(namespaces, name) == NULL) {
          if (NamespaceMap_SetNode(namespaces, node) < 0) {
            Py_DECREF(namespaces);
            return NULL;
          }
        }
      }
    }
    current = Node_GET_PARENT(current);
  } while (current && Element_Check(current));

  return namespaces;
}

/** Python Methods ****************************************************/

static PyObject *element_getnewargs(PyObject *self, PyObject *noargs)
{
  return PyTuple_Pack(2, Element_NAMESPACE_URI(self), Element_QNAME(self));
}

static PyObject *element_getstate(PyObject *self, PyObject *args)
{
  PyObject *deep=Py_True, *dict, *nodemap, *namespaces, *attributes, *children;
  Py_ssize_t pos, i;

  if (!PyArg_ParseTuple(args, "|O:__getstate__", &deep))
    return NULL;

  if (PyType_HasFeature(self->ob_type, Py_TPFLAGS_HEAPTYPE)) {
    dict = PyObject_GetAttrString(self, "__dict__");
    if (dict == NULL)
      return NULL;
  } else {
    Py_INCREF(Py_None);
    dict = Py_None;
  }
  /* save the namespace nodes as a tuple of pairwise prefix/uri items */
  nodemap = Element_NAMESPACES(self);
  if (nodemap == NULL) {
    namespaces = Py_None;
    Py_INCREF(namespaces);
  } else {
    NamespaceObject *node;
    namespaces = PyTuple_New(NamespaceMap_GET_SIZE(nodemap));
    if (namespaces == NULL) {
      Py_DECREF(dict);
      return NULL;
    }
    i = 0;
    pos = 0;
    while ((node = NamespaceMap_Next(nodemap, &pos)) != NULL) {
      PyTuple_SET_ITEM(namespaces, i++, (PyObject *)node);
      Py_INCREF(node);
    }
  }
  /* save the attributes nodes in a tuple */
  nodemap = Element_ATTRIBUTES(self);
  if (nodemap == NULL) {
    attributes = Py_None;
    Py_INCREF(attributes);
  } else {
    AttrObject *node;
    attributes = PyTuple_New(AttributeMap_GET_SIZE(nodemap));
    if (attributes == NULL) {
      Py_DECREF(namespaces);
      Py_DECREF(dict);
      return NULL;
    }
    i = 0;
    pos = 0;
    while ((node = AttributeMap_Next(nodemap, &pos)) != NULL) {
      PyTuple_SET_ITEM(attributes, i++, (PyObject *)node);
      Py_INCREF(node);
    }
  }
  /* save the child nodes in a tuple */
  switch (PyObject_IsTrue(deep)) {
    case 0:
      children = Py_None;
      Py_INCREF(children);
      break;
    case 1:
      children = PyTuple_New(Container_GET_COUNT(self));
      if (children != NULL) {
        for (i = 0; i < Container_GET_COUNT(self); i++) {
          PyObject *item = (PyObject *)Container_GET_CHILD(self, i);
          PyTuple_SET_ITEM(children, i, item);
          Py_INCREF(item);
        }
        break;
      }
      /* error; fall through */
    default:
      Py_DECREF(attributes);
      Py_DECREF(namespaces);
      Py_DECREF(dict);
      return NULL;
  }
  return Py_BuildValue("NNNN", dict, namespaces, attributes, children);
}

Py_LOCAL_INLINE(int)
convert_arg(int item, PyTypeObject *type, PyObject **arg)
{
  PyObject *obj = *arg;
  if (obj->ob_type == type)
    return 1;
  if (obj == Py_None) {
    *arg = NULL;
    return 1;
  }
  PyErr_Format(PyExc_TypeError,
               "__setstate__() argument 1, item %d must be %s, not %s",
               item, type->tp_name, obj->ob_type->tp_name);
  return 0;
}

static PyObject *element_setstate(PyObject *obj, PyObject *state)
{
  ElementObject *self = (ElementObject *)obj;
  PyObject *dict, *namespaces, *attributes, *children, *temp;
  Py_ssize_t i, n;

  if (!PyArg_UnpackTuple(state, NULL, 4, 4,
                         &dict, &namespaces, &attributes, &children))
    return NULL;
  if (!convert_arg(0, &PyDict_Type, &dict))
    return NULL;
  if (!convert_arg(1, &PyTuple_Type, &namespaces))
    return NULL;
  if (!convert_arg(2, &PyTuple_Type, &attributes))
    return NULL;
  if (!convert_arg(3, &PyTuple_Type, &children))
    return NULL;

  if (dict) {
    if (PyType_HasFeature(self->ob_type, Py_TPFLAGS_HEAPTYPE)) {
      temp = PyObject_GetAttrString((PyObject *)self, "__dict__");
      if (temp == NULL)
        return NULL;
      if (PyDict_Update(temp, dict) < 0) {
        Py_DECREF(temp);
        return NULL;
      }
      Py_DECREF(temp);
    }
  }
  if (namespaces) {
    for (i = 0, n = PyTuple_GET_SIZE(namespaces); i < n; i++) {
      temp = PyTuple_GET_ITEM(namespaces, i);
      if (Element_SetNamespace(self, (NamespaceObject *)temp) < 0)
        return NULL;
    }
  }
  if (attributes) {
    for (i = 0, n = PyTuple_GET_SIZE(attributes); i < n; i++) {
      temp = PyTuple_GET_ITEM(attributes, i);
      if (Element_SetAttribute(self, (AttrObject *)temp) < 0)
        return NULL;
    }
  }
  if (children) {
    for (i = 0, n = PyTuple_GET_SIZE(children); i < n; i++) {
      temp = PyTuple_GET_ITEM(children, i);
      if (Container_Append((NodeObject *)self, (NodeObject *)temp) < 0)
        return NULL;
    }
  }
  Py_RETURN_NONE;
}

static char xml_attribute_added_doc[] = "xml_attribute_added(target)\n\n\
An attribute has been added to this element. This event is dispatched\n\
after the addition has taken place. The `target` node of this event is the\n\
attribute being added.";

static PyObject *xml_attribute_added(PyObject *self, PyObject *child)
{
  Py_RETURN_NONE;
}

static char xml_attribute_modified_doc[] = "xml_attribute_modified(target)\n\n\
An attribute's value has been changed. This event is dispatched after the\n\
attribute value has been modified. The `target` node of this event is the\n\
attribute whose value has been modified.";

static PyObject *xml_attribute_modified(PyObject *self, PyObject *child)
{
  Py_RETURN_NONE;
}

static char xml_attribute_removed_doc[] = "xml_attribute_removed(target)\n\n\
An attribute is being removed from this element. This event is dispatched\n\
before the attribute is removed from the tree. The `target` node of this\n\
event is the attribute being removed.";

static PyObject *xml_attribute_removed(PyObject *self, PyObject *child)
{
  Py_RETURN_NONE;
}

#define PyMethod_INIT(NAME, FLAGS) \
  { #NAME, (PyCFunction)NAME, FLAGS, NAME##_doc }

static PyMethodDef element_methods[] = {
  /* mutation events */
  PyMethod_INIT(xml_attribute_added,    METH_O),
  PyMethod_INIT(xml_attribute_modified, METH_O),
  PyMethod_INIT(xml_attribute_removed,  METH_O),
  /* copy/deepcopy/pickle support */
  { "__getnewargs__", element_getnewargs, METH_NOARGS,  "helper for pickle" },
  { "__getstate__",   element_getstate,   METH_VARARGS, "helper for pickle" },
  { "__setstate__",   element_setstate,   METH_O,       "helper for pickle" },
  { NULL }
};

/** Python Members ****************************************************/

static PyMemberDef element_members[] = {
  { NULL }
};

/** Python Computed Members *******************************************/

/* (RO) element.xml_name */
static PyObject *get_name(PyObject *self, void *arg)
{
  return PyTuple_Pack(2, Element_NAMESPACE_URI(self),
                      Element_LOCAL_NAME(self));
}

/* (RO) element.xml_qname */
static PyObject *get_qname(PyObject *self, void *arg)
{
  PyObject *result = Element_QNAME(self);
  Py_INCREF(result);
  return result;
}

/* (RW) element.xml_prefix */
static PyObject *get_prefix(PyObject *self, void *arg)
{
  Py_UNICODE *p;
  Py_ssize_t size, i;

  p = PyUnicode_AS_UNICODE(Element_QNAME(self));
  size = PyUnicode_GET_SIZE(Element_QNAME(self));
  for (i = 0; i < size; i++) {
    if (p[i] == ':')
      return PyUnicode_FromUnicode(p, i);
  }
  Py_INCREF(Py_None);
  return Py_None;
}

static int set_prefix(PyObject *self, PyObject *v, void *arg)
{
  PyObject *qname, *prefix, *namespace;

  prefix = XmlString_ConvertArgument(v, "xml_prefix", 1);
  if (prefix == NULL)
    return -1;
  if (prefix == Py_None) {
    qname = Element_LOCAL_NAME(self);
    Py_INCREF(qname);
  } else {
    qname = build_qname(prefix, Element_LOCAL_NAME(self));
    if (qname == NULL) {
      Py_DECREF(prefix);
      return -1;
    }
  }
  namespace = lookup_namespace(Element(self), prefix);
  if (namespace == NULL) {
    Py_DECREF(prefix);
    Py_DECREF(qname);
    return -1;
  }
  Py_DECREF(prefix);

  Py_DECREF(Element_QNAME(self));
  Element_QNAME(self) = qname;
  Py_DECREF(Element_NAMESPACE_URI(self));
  Py_INCREF(namespace);
  Element_NAMESPACE_URI(self) = namespace;
  return 0;
}

/* (RW) element.xml_local */
static PyObject *get_local(PyObject *self, void *arg)
{
  PyObject *result = Element_LOCAL_NAME(self);
  Py_INCREF(result);
  return result;
}

static int set_local(PyObject *self, PyObject *v, void *arg)
{
  PyObject *local, *qname;
  Py_ssize_t size, i;
  Py_UNICODE *p;

  local = XmlString_ConvertArgument(v, "xml_local", 0);
  if (local == NULL)
    return -1;

  qname = Element_QNAME(self);
  size = PyUnicode_GET_SIZE(qname);
  p = PyUnicode_AS_UNICODE(qname);
  for (i = 0; i < size; i++) {
    if (p[i] == ':') {
      i++;
      size = i + PyUnicode_GET_SIZE(local);
      qname = PyUnicode_FromUnicode(NULL, size);
      if (qname == NULL) {
        Py_DECREF(local);
        return -1;
      }
      Py_UNICODE_COPY(PyUnicode_AS_UNICODE(qname),
                      PyUnicode_AS_UNICODE(Element_QNAME(self)), i);
      Py_UNICODE_COPY(PyUnicode_AS_UNICODE(qname) + i,
                      PyUnicode_AS_UNICODE(local),
                      PyUnicode_GET_SIZE(local));
      goto finally;
    }
  }
  /* No prefix found in the existing qname; just use the local name */
  Py_INCREF(local);
  qname = local;
finally:
  Py_DECREF(Element_LOCAL_NAME(self));
  Element_LOCAL_NAME(self) = local;
  Py_DECREF(Element_QNAME(self));
  Element_QNAME(self) = qname;
  return 0;
}

/* (RW) element.xml_namespace */
static PyObject *get_namespace(PyObject *self, void *arg)
{
  PyObject *result = Element_NAMESPACE_URI(self);
  Py_INCREF(result);
  return result;
}

static int set_namespace(PyObject *self, PyObject *v, void *arg)
{
  PyObject *namespace, *prefix, *qname;
  namespace = XmlString_ConvertArgument(v, "xml_namespace", 1);
  if (namespace == NULL)
    return -1;
  prefix = lookup_prefix(Element(self), namespace);
  if (prefix == NULL) {
    Py_DECREF(namespace);
    return -1;
  }
  if (prefix == Py_None) {
    qname = Element_LOCAL_NAME(self);
    Py_INCREF(qname);
  } else {
    qname = build_qname(prefix, Element_LOCAL_NAME(self));
    if (qname == NULL) {
      Py_DECREF(namespace);
      return -1;
    }
  }

  Py_DECREF(Element_NAMESPACE_URI(self));
  Element_NAMESPACE_URI(self) = namespace;
  Py_DECREF(Element_QNAME(self));
  Element_QNAME(self) = qname;
  return 0;
}

/* (RO) element.xml_attributes */
static PyObject *
get_xml_attributes(ElementObject *self, void *arg)
{
  if (self->attributes == NULL)
    self->attributes = AttributeMap_New(self);
  Py_XINCREF(self->attributes);
  return self->attributes;
}

/* (RO) element.xmlns_attributes */
static PyObject *
get_xmlns_attributes(ElementObject *self, void *arg)
{
  if (self->namespaces == NULL)
    self->namespaces = NamespaceMap_New(self);
  Py_XINCREF(self->namespaces);
  return self->namespaces;
}

/* (RO) element.xml_namespaces */
static PyObject *
get_xml_namespaces(PyObject *self, void *arg)
{
  return Element_InscopeNamespaces(Element(self));
}

static PyGetSetDef element_getset[] = {
  { "xml_name", get_name },
  { "xml_qname", get_qname },
  { "xml_prefix", get_prefix, set_prefix},
  { "xml_local", get_local, set_local },
  { "xml_namespace", get_namespace, set_namespace },
  { "xml_attributes", (getter)get_xml_attributes },
  { "xmlns_attributes", (getter)get_xmlns_attributes },
  { "xml_namespaces", get_xml_namespaces },
  { NULL }
};

/** Type Object ********************************************************/

static void element_dealloc(ElementObject *self)
{
  PyObject_GC_UnTrack((PyObject *) self);
  Py_CLEAR(self->namespaceURI);
  Py_CLEAR(self->localName);
  Py_CLEAR(self->qname);
  Py_CLEAR(self->attributes);
  Py_CLEAR(self->namespaces);
  Node_Del(self);
}

static PyObject *element_repr(ElementObject *self)
{
  PyObject *repr, *name;
  Py_ssize_t num_namespaces=0, num_attributes=0;
  name = PyObject_Repr(self->qname);
  if (name == NULL)
    return NULL;
  if (Element_NAMESPACES(self))
    num_namespaces = NamespaceMap_GET_SIZE(Element_NAMESPACES(self));
  if (Element_ATTRIBUTES(self))
    num_attributes = AttributeMap_GET_SIZE(Element_ATTRIBUTES(self));
  repr = PyString_FromFormat("<%s at %p: name %s, %zd namespaces, "
                             "%zd attributes, %zd children>",
                             self->ob_type->tp_name, self, 
                             PyString_AsString(name),
                             num_namespaces, num_attributes,
                             Container_GET_COUNT(self));
  Py_DECREF(name);
  return repr;
}

static int element_traverse(ElementObject *self, visitproc visit, void *arg)
{
  Py_VISIT(self->attributes);
  Py_VISIT(self->namespaces);
  return DomletteContainer_Type.tp_traverse((PyObject *)self, visit, arg);
}

static int element_clear(ElementObject *self)
{
  Py_CLEAR(self->attributes);
  Py_CLEAR(self->namespaces);
  return DomletteContainer_Type.tp_clear((PyObject *)self);
}

static PyObject *element_new(PyTypeObject *type, PyObject *args,
                             PyObject *kwds)
{
  PyObject *namespaceURI, *qualifiedName, *prefix, *localName;
  static char *kwlist[] = { "namespace", "qname", NULL };
  ElementObject *self;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO:element", kwlist,
                                   &namespaceURI, &qualifiedName)) {
    return NULL;
  }

  namespaceURI = XmlString_ConvertArgument(namespaceURI, "namespace", 1);
  if (namespaceURI == NULL) return NULL;

  qualifiedName = XmlString_ConvertArgument(qualifiedName, "qname", 0);
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
    DOMException_NamespaceErr("If you have a prefix in your qname you must have a non-null namespace");
    Py_DECREF(namespaceURI);
    Py_DECREF(prefix);
    return NULL;
  }
  Py_DECREF(prefix);

  if (type != &DomletteElement_Type) {
    self = Element(type->tp_alloc(type, 0));
    if (self != NULL) {
      self = element_init(self, namespaceURI, qualifiedName, localName);
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
element(namespaceURI, qualifiedName) -> element object\n\
\n\
The `element` interface represents an element in an XML document.";

PyTypeObject DomletteElement_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "element",
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
  PyObject *import, *dict, *value;

  attribute_factory_string = PyString_FromString("xml_attribute_factory");
  if (attribute_factory_string == NULL)
    return -1;
  xml_string = XmlString_FromASCII("xml");
  if (xml_string == NULL)
    return -1;
  xmlns_string = XmlString_FromASCII("xmlns");
  if (xmlns_string == NULL)
    return -1;
  import = PyImport_ImportModule("amara.namespaces");
  if (import == NULL)
    return -1;
  xml_namespace = PyObject_GetAttrString(import, "XML_NAMESPACE");
  xml_namespace = XmlString_FromObjectInPlace(xml_namespace);
  if (xml_namespace == NULL)
    return -1;
  xmlns_namespace = PyObject_GetAttrString(import, "XMLNS_NAMESPACE");
  xmlns_namespace = XmlString_FromObjectInPlace(xmlns_namespace);
  if (xmlns_namespace == NULL)
    return -1;
  Py_DECREF(import);

  DomletteElement_Type.tp_base = &DomletteContainer_Type;
  if (PyType_Ready(&DomletteElement_Type) < 0)
    return -1;
  dict = DomletteElement_Type.tp_dict;
  value = PyString_FromString("element");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_type", value))
    return -1;
  Py_DECREF(value);
  /* add the "typecode" character for use with `xml_nodeid` */
  value = PyString_FromString("e");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_typecode", value) < 0)
    return -1;
  Py_DECREF(value);
  value = (PyObject *)&DomletteAttr_Type;
  if (PyDict_SetItemString(dict, "xml_attribute_factory", value))
    return -1;

  Py_INCREF(&DomletteElement_Type);
  return PyModule_AddObject(module, "element",
                            (PyObject*) &DomletteElement_Type);
}


void DomletteElement_Fini(void)
{
  Py_DECREF(attribute_factory_string);
  Py_DECREF(xml_string);
  Py_DECREF(xmlns_string);
  Py_DECREF(xml_namespace);
  Py_DECREF(xmlns_namespace);

  PyType_CLEAR(&DomletteElement_Type);
}
