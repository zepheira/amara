#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

Py_LOCAL_INLINE(int)
attr_init(AttrObject *self, PyObject *namespaceURI, PyObject *qualifiedName,
          PyObject *localName, PyObject *value)
{
  if ((self == NULL || !Attr_Check(self)) ||
      (namespaceURI == NULL || !XmlString_NullCheck(namespaceURI)) ||
      (qualifiedName == NULL || !XmlString_Check(qualifiedName)) ||
      (localName == NULL || !XmlString_Check(localName)) ||
      (value != NULL && !XmlString_Check(value))) {
    PyErr_BadInternalCall();
    return -1;
  }

  if (value == NULL) {
    value = PyUnicode_FromUnicode(NULL, 0);
    if (value == NULL) return -1;
  } else {
    Py_INCREF(value);
  }

  Py_INCREF(namespaceURI);
  self->namespaceURI = namespaceURI;

  Py_INCREF(localName);
  self->localName = localName;

  Py_INCREF(qualifiedName);
  self->nodeName = qualifiedName;

  self->nodeValue = value;

  self->type = ATTRIBUTE_TYPE_CDATA;

  return 0;
}

/** Public C API ******************************************************/

AttrObject *Attr_New(PyObject *namespaceURI, PyObject *qualifiedName,
                     PyObject *localName, PyObject *value)
{
  AttrObject *self;

  self = Node_New(AttrObject, &DomletteAttr_Type);
  if (self != NULL) {
    if (attr_init(self, namespaceURI, qualifiedName, localName, value) < 0) {
      Node_Del(self);
      return NULL;
    }
  }

  PyObject_GC_Track(self);

  return self;
}


AttrObject *Attr_CloneNode(PyObject *node, int deep)
{
  PyObject *namespaceURI, *qualifiedName, *localName, *value;
  AttrObject *attr;

  namespaceURI = PyObject_GetAttrString(node, "namespaceURI");
  namespaceURI = XmlString_FromObjectInPlace(namespaceURI);
  qualifiedName = PyObject_GetAttrString(node, "nodeName");
  qualifiedName = XmlString_FromObjectInPlace(qualifiedName);
  localName = PyObject_GetAttrString(node, "localName");
  localName = XmlString_FromObjectInPlace(localName);
  value = PyObject_GetAttrString(node, "value");
  value = XmlString_FromObjectInPlace(value);
  if (namespaceURI == NULL || qualifiedName == NULL || localName == NULL ||
      value == NULL) {
    Py_XDECREF(value);
    Py_XDECREF(localName);
    Py_XDECREF(qualifiedName);
    Py_XDECREF(namespaceURI);
    return NULL;
  }

  attr = Attr_New(namespaceURI, qualifiedName, localName, value);
  Py_DECREF(value);
  Py_DECREF(localName);
  Py_DECREF(qualifiedName);
  Py_DECREF(namespaceURI);

  return attr;
}

/** Python Methods ****************************************************/

static PyMethodDef attr_methods[] = {
  { NULL }
};

/** Python Members ****************************************************/

static PyMemberDef attr_members[] = {
  { "xml_qname",         T_OBJECT, offsetof(AttrObject, nodeName),     RO },
  { "xml_namespace", T_OBJECT, offsetof(AttrObject, namespaceURI), RO },
  { "xml_name",    T_OBJECT, offsetof(AttrObject, localName),    RO },
  { "xml_parent", T_OBJECT, offsetof(AttrObject, parentNode),   RO },
  { NULL }
};

/** Python Computed Members *******************************************/

static PyObject *get_prefix(AttrObject *self, void *arg)
{
  Py_UNICODE *p = PyUnicode_AS_UNICODE(self->nodeName);
  Py_ssize_t i, size;

  size = PyUnicode_GET_SIZE(self->nodeName);
  for (i = 0; i < size; i++) {
    if (p[i] == ':') {
      return PyUnicode_FromUnicode(p, i);
    }
  }
  Py_INCREF(Py_None);
  return Py_None;
}

static int set_prefix(AttrObject *self, PyObject *v, char *arg)
{
  PyObject *qualifiedName, *prefix;
  Py_ssize_t size;

  prefix = XmlString_ConvertArgument(v, "xml_prefix", 1);
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

static PyObject *get_value(AttrObject *self, char *arg)
{
  Py_INCREF(self->nodeValue);
  return self->nodeValue;
}

static int set_value(AttrObject *self, PyObject *v, char *arg)
{
  PyObject *nodeValue = XmlString_ConvertArgument(v, "xml_value", 0);
  if (nodeValue == NULL) return -1;

  Py_DECREF(self->nodeValue);
  self->nodeValue = nodeValue;
  return 0;
}

static PyGetSetDef attr_getset[] = {
  { "xml_prefix",    (getter)get_prefix, (setter)set_prefix},
  { "xml_value",     (getter)get_value,  (setter)set_value},
  { NULL }
};

/** Type Object ********************************************************/

static void attr_dealloc(AttrObject *self)
{
  PyObject_GC_UnTrack((PyObject *)self);
  Py_CLEAR(self->namespaceURI);
  Py_CLEAR(self->localName);
  Py_CLEAR(self->nodeName);
  Py_CLEAR(self->nodeValue);
  Node_Del(self);
}

static PyObject *attr_repr(AttrObject *self)
{
  PyObject *repr;
  PyObject *name = PyObject_Repr(self->nodeName);
  PyObject *value = PyObject_Repr(self->nodeValue);
  if (name == NULL || value == NULL) {
    Py_XDECREF(name);
    Py_XDECREF(value);
    return NULL;
  }
  repr = PyString_FromFormat("<Attr at %p: name %s, value %s>", self,
                             PyString_AsString(name),
                             PyString_AsString(value));
  Py_DECREF(name);
  Py_DECREF(value);
  return repr;
}

static PyObject *attr_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  PyObject *namespaceURI, *qualifiedName, *prefix, *localName;
  static char *kwlist[] = { "namespace", "qname",
                            NULL };
  AttrObject *attr;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO:Attr", kwlist,
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

  if (type != &DomletteAttr_Type) {
    attr = (AttrObject *) type->tp_alloc(type, 0);
    if (attr != NULL) {
      _Node_INIT(attr);
      if (attr_init(attr, namespaceURI, qualifiedName, localName, NULL) < 0) {
        Py_DECREF(attr);
        attr = NULL;
      }
    }
  } else {
    attr = Attr_New(namespaceURI, qualifiedName, localName, NULL);
  }
  Py_DECREF(namespaceURI);
  Py_DECREF(qualifiedName);
  Py_DECREF(localName);

  return (PyObject *) attr;
}

static char attr_doc[] = "\
Attr(namespace, qname) -> Attr object\n\
\n\
The Attr interface represents an attribute in an Element object.";

PyTypeObject DomletteAttr_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "Attr",
  /* tp_basicsize      */ sizeof(AttrObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) attr_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) attr_repr,
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
                           Py_TPFLAGS_BASETYPE),
  /* tp_doc            */ (char *) attr_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) attr_methods,
  /* tp_members        */ (PyMemberDef *) attr_members,
  /* tp_getset         */ (PyGetSetDef *) attr_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) attr_new,
  /* tp_free           */ 0,
};

/** Module Interface **************************************************/

int DomletteAttr_Init(PyObject *module)
{
  PyObject *dict, *value;

  DomletteAttr_Type.tp_base = &DomletteNode_Type;
  if (PyType_Ready(&DomletteAttr_Type) < 0)
    return -1;

  dict = DomletteAttr_Type.tp_dict;

  value = PyInt_FromLong(ATTRIBUTE_NODE);
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_node_type", value))
    return -1;
  Py_DECREF(value);

  /* Override default behavior from Node */
  if (PyDict_SetItemString(dict, "xml_previous_sibling", Py_None))
    return -1;

  /* Override default behavior from Node */
  if (PyDict_SetItemString(dict, "xml_next_sibling", Py_None))
    return -1;

  /* Until the DTD information is used, assume it was from the document */
  value = PyInt_FromLong(1);
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_specified", value))
    return -1;
  Py_DECREF(value);

  Py_INCREF(&DomletteAttr_Type);
  return PyModule_AddObject(module, "Attr", (PyObject*) &DomletteAttr_Type);
}

void DomletteAttr_Fini(void)
{
  PyType_CLEAR(&DomletteAttr_Type);
}
