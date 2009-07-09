#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

static PyObject *empty_string;
static PyObject *modified_event;

Py_LOCAL_INLINE(AttrObject *)
attr_init(AttrObject *self, PyObject *namespaceURI, PyObject *qualifiedName,
          PyObject *localName, PyObject *value)
{
  assert(self && Attr_Check(self));
  if ((namespaceURI == NULL || !XmlString_NullCheck(namespaceURI)) ||
      (qualifiedName == NULL || !XmlString_Check(qualifiedName)) ||
      (localName == NULL || !XmlString_Check(localName)) ||
      (value != NULL && !XmlString_Check(value))) {
    PyErr_BadInternalCall();
    Py_DECREF(self);
    return NULL;
  }
  if (value == NULL)
    value = empty_string;

  self->hash = AttributeMap_GetHash(namespaceURI, localName);
  if (self->hash == -1) {
    Py_DECREF(self);
    return NULL;
  }

  Py_INCREF(namespaceURI);
  self->namespaceURI = namespaceURI;

  Py_INCREF(localName);
  self->localName = localName;

  Py_INCREF(qualifiedName);
  self->qname = qualifiedName;

  Py_INCREF(value);
  self->value = value;

  self->type = ATTRIBUTE_TYPE_CDATA;

  return self;
}

/** Public C API ******************************************************/

AttrObject *Attr_New(PyObject *namespaceURI, PyObject *qualifiedName,
                     PyObject *localName, PyObject *value)
{
  AttrObject *self;

  self = Node_New(AttrObject, &DomletteAttr_Type);
  if (self != NULL) {
    self = attr_init(self, namespaceURI, qualifiedName, localName, value);
  }
  return self;
}

int Attr_SetValue(AttrObject *self, PyObject *value)
{
  NodeObject *owner;
  if (self == NULL || !Attr_Check(self)) {
    PyErr_BadInternalCall();
    return -1;
  }

  if (value == NULL) {
    value = empty_string;
    Py_INCREF(value);
  } else if (PyUnicode_Check(value)) {
    Py_INCREF(value);
  } else {
    value = XmlString_ConvertArgument(value, "value", 0);
    if (value == NULL)
      return -1;
  }
  Py_DECREF(Attr_GET_VALUE(self));
  Attr_SET_VALUE(self, value);

  owner = Node_GET_PARENT(self);
  if (owner == NULL || Element_CheckExact(owner))
    return 0;

  return Node_DispatchEvent(owner, modified_event, (NodeObject *)self);
}

/** Python Methods ****************************************************/

static PyObject *attr_getnewargs(PyObject *self, PyObject *noargs)
{
  return PyTuple_Pack(2, Attr_GET_NAMESPACE_URI(self), Attr_GET_QNAME(self));
}

static PyObject *attr_getstate(PyObject *self, PyObject *args)
{
  PyObject *deep=Py_True;

  if (!PyArg_ParseTuple(args, "|O:__getstate__", &deep))
    return NULL;

  return Py_BuildValue("OOi", Node_GET_PARENT(self), Attr_GET_VALUE(self),
                       Attr_GET_TYPE(self));
}

static PyObject *attr_setstate(PyObject *self, PyObject *state)
{
  NodeObject *parent, *node;
  PyObject *value, *temp;
  int type;

  if (!PyArg_ParseTuple(state, "O!Oi", &DomletteNode_Type, &parent, &value,
                        &type))
    return NULL;

  node = Node_GET_PARENT(self);
  Node_SET_PARENT(self, parent);
  Py_INCREF(parent);
  Py_XDECREF(node);

  temp = Attr_GET_VALUE(self);
  Attr_SET_VALUE(self, value);
  Py_INCREF(value);
  Py_XDECREF(temp);

  Attr_SET_TYPE(self, type);

  Py_INCREF(Py_None);
  return Py_None;
}

static PyMethodDef attr_methods[] = {
  { "__getnewargs__", attr_getnewargs, METH_NOARGS,  "helper for pickle" },
  { "__getstate__",   attr_getstate,   METH_VARARGS, "helper for pickle" },
  { "__setstate__",   attr_setstate,   METH_O,       "helper for pickle" },
  { NULL }
};

/** Python Members ****************************************************/

static PyMemberDef attr_members[] = {
  { "xml_qname",     T_OBJECT, offsetof(AttrObject, qname),        RO },
  { "xml_namespace", T_OBJECT, offsetof(AttrObject, namespaceURI), RO },
  { "xml_local",     T_OBJECT, offsetof(AttrObject, localName),    RO },
  { NULL }
};

/** Python Computed Members *******************************************/

static PyObject *get_name(AttrObject *self, void *arg)
{
  return PyTuple_Pack(2, self->namespaceURI, self->localName);
}

static PyObject *get_prefix(AttrObject *self, void *arg)
{
  Py_UNICODE *p = PyUnicode_AS_UNICODE(self->qname);
  Py_ssize_t i, size;

  size = PyUnicode_GET_SIZE(self->qname);
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
    Py_DECREF(self->qname);
    Py_INCREF(self->localName);
    self->qname = self->localName;
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

  Py_DECREF(self->qname);
  self->qname = qualifiedName;
  return 0;
}

static PyObject *get_value(AttrObject *self, char *arg)
{
  Py_INCREF(self->value);
  return self->value;
}

static int set_value(AttrObject *self, PyObject *v, char *arg)
{
  PyObject *value = XmlString_ConvertArgument(v, "xml_value", 0);
  if (value == NULL)
    return -1;
  return Attr_SetValue(self, value);
}

static PyGetSetDef attr_getset[] = {
  { "xml_name",   (getter)get_name },
  { "xml_prefix", (getter)get_prefix, (setter)set_prefix },
  { "xml_value",  (getter)get_value,  (setter)set_value },
  { NULL }
};

/** Type Object ********************************************************/

static void attr_dealloc(AttrObject *self)
{
  PyObject_GC_UnTrack((PyObject *)self);
  Py_CLEAR(self->namespaceURI);
  Py_CLEAR(self->localName);
  Py_CLEAR(self->qname);
  Py_CLEAR(self->value);
  Node_Del(self);
}

static PyObject *attr_repr(AttrObject *self)
{
  PyObject *repr;
  PyObject *name = PyObject_Repr(self->qname);
  PyObject *value = PyObject_Repr(self->value);
  if (name == NULL || value == NULL) {
    Py_XDECREF(name);
    Py_XDECREF(value);
    return NULL;
  }
  repr = PyString_FromFormat("<attribute at %p: name %s, value %s>", self,
                             PyString_AsString(name),
                             PyString_AsString(value));
  Py_DECREF(name);
  Py_DECREF(value);
  return repr;
}

static PyObject *attr_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  PyObject *namespaceURI, *qualifiedName, *prefix, *localName, *value=NULL;
  static char *kwlist[] = { "namespace", "qname", "value",
                            NULL };
  AttrObject *attr;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|O:attribute", kwlist,
                                   &namespaceURI, &qualifiedName, &value)) {
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

  if (value) {
    value = XmlString_ConvertArgument(value, "value", 0);
    if (value == NULL) {
      Py_DECREF(namespaceURI);
      Py_DECREF(qualifiedName);
      Py_DECREF(localName);
      return NULL;
    }
  }

  if (type != &DomletteAttr_Type) {
    attr = (AttrObject *) type->tp_alloc(type, 0);
    if (attr != NULL) {
      attr = attr_init(attr, namespaceURI, qualifiedName, localName, value);
    }
  } else {
    attr = Attr_New(namespaceURI, qualifiedName, localName, value);
  }
  Py_DECREF(namespaceURI);
  Py_DECREF(qualifiedName);
  Py_DECREF(localName);
  Py_XDECREF(value);

  return (PyObject *) attr;
}

static char attr_doc[] = "\
attribute(namespace, qname[, value]) -> attribute object\n\
\n\
The `attribute` interface represents an attribute in an `element` object.";

PyTypeObject DomletteAttr_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME ".attribute",
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

  empty_string = XmlString_FromASCII("");
  if (empty_string == NULL)
    return -1;

  modified_event = PyString_FromString("xml_attribute_modified");
  if (modified_event == NULL)
    return -1;

  dict = DomletteAttr_Type.tp_dict;

  value = PyString_FromString("attribute");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_type", value))
    return -1;
  Py_DECREF(value);
  /* add the "typecode" character for use with `xml_nodeid` */
  value = PyString_FromString("a");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_typecode", value) < 0)
    return -1;
  Py_DECREF(value);

  /* Until the DTD information is used, assume it was from the document */
  if (PyDict_SetItemString(dict, "xml_specified", Py_True))
    return -1;

  Py_INCREF(&DomletteAttr_Type);
  return PyModule_AddObject(module, "attribute",
                            (PyObject *)&DomletteAttr_Type);
}

void DomletteAttr_Fini(void)
{
  Py_DECREF(empty_string);
  Py_DECREF(modified_event);
  PyType_CLEAR(&DomletteAttr_Type);
}
