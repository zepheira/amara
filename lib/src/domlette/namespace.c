#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

static PyObject *empty_string;

Py_LOCAL_INLINE(NamespaceObject *)
namespace_init(NamespaceObject *self, PyObject *prefix, PyObject *namespaceURI)
{
  assert(self && Namespace_Check(self));
  if ((prefix == NULL || !XmlString_NullCheck(prefix)) ||
      (namespaceURI == NULL || !XmlString_Check(namespaceURI))) {
    PyErr_BadInternalCall();
    Py_DECREF(self);
    return NULL;
  }
  self->hash = NamespaceMap_GetHash(prefix);
  if (self->hash == -1) {
    Py_DECREF(self);
    return NULL;
  }

  Py_INCREF(prefix);
  self->name = prefix;

  Py_INCREF(namespaceURI);
  self->value = namespaceURI;

  return self;
}

/** C API *************************************************************/

NamespaceObject *Namespace_New(PyObject *prefix, PyObject *namespaceURI)
{
  NamespaceObject *self;

  self = Node_New(NamespaceObject, &DomletteNamespace_Type);
  if (self != NULL) {
    self = namespace_init(self, prefix, namespaceURI);
  }
  return self;
}

/** Python Methods ****************************************************/

static PyObject *namespace_getnewargs(PyObject *self, PyObject *noargs)
{
  return PyTuple_Pack(2, Namespace_GET_NAME(self), Namespace_GET_VALUE(self));
}

static PyMethodDef namespace_methods[] = {
  { "__getnewargs__", namespace_getnewargs, METH_NOARGS,  "helper for pickle" },
  { NULL }
};

/** Python Members ****************************************************/

#define Namespace_MEMBER(name, member) \
  { #name, T_OBJECT, offsetof(NamespaceObject, member), RO }

static PyMemberDef namespace_members[] = {
  Namespace_MEMBER(xml_name, name),
  Namespace_MEMBER(xml_value, value),
  { NULL }
};

/** Python Computed Members *******************************************/

static PyGetSetDef namespace_getset[] = {
  { NULL }
};

/** Type Object *******************************************************/

static void namespace_dealloc(NamespaceObject *self)
{
  PyObject_GC_UnTrack((PyObject *) self);
  Py_CLEAR(self->value);
  Py_CLEAR(self->name);
  Node_Del(self);
}

static PyObject *namespace_repr(NamespaceObject *self)
{
  PyObject *repr;
  PyObject *name = PyObject_Repr(self->name);
  PyObject *value = PyObject_Repr(self->value);
  if (name == NULL || value == NULL) {
    Py_XDECREF(name);
    Py_XDECREF(value);
    return NULL;
  }
  repr = PyString_FromFormat("<Namespace at %p: name %s, value %s>",
                             self,
                             PyString_AsString(name),
                             PyString_AsString(value));
  Py_DECREF(name);
  Py_DECREF(value);
  return repr;
}

static PyObject *
namespace_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  PyObject *prefix, *namespaceURI;
  static char *kwlist[] = { "prefix", "namespace", NULL };
  NamespaceObject *self;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO:namespace", kwlist,
                                   &prefix, &namespaceURI)) {
    return NULL;
  }

  prefix = XmlString_ConvertArgument(prefix, "prefix", 1);
  if (prefix == NULL)
    return NULL;
  namespaceURI = XmlString_ConvertArgument(namespaceURI, "namespace", 0);
  if (namespaceURI == NULL) {
    Py_DECREF(prefix);
    return NULL;
  }

  if (type != &DomletteNamespace_Type) {
    self = Namespace(type->tp_alloc(type, 0));
    if (self != NULL) {
      self = namespace_init(self, prefix, namespaceURI);
    }
  } else {
    self = Namespace_New(prefix, namespaceURI);
  }
  Py_DECREF(prefix);
  Py_DECREF(namespaceURI);

  return (PyObject *)self;
}

static char namespace_doc[] = "\
namespace(prefix, namespace) -> namespace object\n\
\n\
The `namespace` interface represents the XPath namespace node type\n\
that DOM lacks.";

PyTypeObject DomletteNamespace_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "namespace",
  /* tp_basicsize      */ sizeof(NamespaceObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) namespace_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) namespace_repr,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) 0,
  /* tp_as_mapping     */ (PyMappingMethods *) 0,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) 0,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ Py_TPFLAGS_DEFAULT,
  /* tp_doc            */ (char *) namespace_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) namespace_methods,
  /* tp_members        */ (PyMemberDef *) namespace_members,
  /* tp_getset         */ (PyGetSetDef *) namespace_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) namespace_new,
  /* tp_free           */ 0,
};

/** Module Interface **************************************************/

int DomletteNamespace_Init(PyObject *module)
{
  PyObject *dict, *value;

  DomletteNamespace_Type.tp_base = &DomletteNode_Type;
  if (PyType_Ready(&DomletteNamespace_Type) < 0)
    return -1;

  empty_string = XmlString_FromASCII("");
  if (empty_string == NULL)
    return -1;

  dict = DomletteNamespace_Type.tp_dict;

  value = PyString_FromString("namespace");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_type", value))
    return -1;
  Py_DECREF(value);
  /* add the "typecode" character for use with `xml_nodeid` */
  value = PyString_FromString("n");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_typecode", value) < 0)
    return -1;
  Py_DECREF(value);

  Py_INCREF(&DomletteNamespace_Type);
  return PyModule_AddObject(module, "namespace",
                            (PyObject*)&DomletteNamespace_Type);
}

void DomletteNamespace_Fini(void)
{
  Py_DECREF(empty_string);
  PyType_CLEAR(&DomletteNamespace_Type);
}
