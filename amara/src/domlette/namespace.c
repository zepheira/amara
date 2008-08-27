#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

Py_LOCAL_INLINE(int)
namespace_init(NamespaceObject *self, ElementObject *parentNode,
               PyObject *prefix, PyObject *namespaceURI)
{
  if ((self == NULL || !Namespace_Check(self)) ||
      (parentNode == NULL || !Element_Check(parentNode)) ||
      (prefix == NULL || !XmlString_NullCheck(prefix)) ||
      (namespaceURI == NULL || !XmlString_Check(namespaceURI))) {
    PyErr_BadInternalCall();
    return -1;
  }

  if (prefix == Py_None) {
    prefix = PyUnicode_FromUnicode(NULL, 0);
    if (prefix == NULL) return -1;
  } else {
    Py_INCREF(prefix);
  }
  self->nodeName = prefix;

  Py_INCREF(namespaceURI);
  self->nodeValue = namespaceURI;

  assert(Node_GET_PARENT(self) == NULL);
  Py_INCREF(parentNode);
  Node_SET_PARENT(self, (NodeObject *)parentNode);

  return 0;
}

/** C API *************************************************************/

NamespaceObject *Namespace_New(ElementObject *parentNode,
                               PyObject *prefix,
                               PyObject *namespaceURI)
{
  NamespaceObject *self;

  if (parentNode == NULL || !Element_Check(parentNode)) {
    PyErr_BadInternalCall();
    return NULL;
  }

  self = Node_New(NamespaceObject, &DomletteNamespace_Type);
  if (self != NULL) {
    if (namespace_init(self, parentNode, prefix, namespaceURI) < 0) {
      Node_Del(self);
      return NULL;
    }
  }

  PyObject_GC_Track(self);

  return self;
}

/** Python Methods ****************************************************/

static PyMethodDef namespace_methods[] = {
  { NULL }
};

/** Python Members ****************************************************/

#define Namespace_MEMBER(name, member) \
  { #name, T_OBJECT, offsetof(NamespaceObject, member), RO }

static PyMemberDef namespace_members[] = {
  Namespace_MEMBER(nodeName, nodeName),
  Namespace_MEMBER(localName, nodeName),
  Namespace_MEMBER(nodeValue, nodeValue),
  Namespace_MEMBER(value, nodeValue),
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
  Py_CLEAR(self->nodeValue);
  Py_CLEAR(self->nodeName);
  Node_Del(self);
}

static PyObject *namespace_repr(NamespaceObject *self)
{
  PyObject *repr;
  PyObject *name = PyObject_Repr(self->nodeName);
  PyObject *value = PyObject_Repr(self->nodeValue);
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
  ElementObject *parentNode;
  PyObject *prefix, *namespaceURI;
  static char *kwlist[] = { "parent", "prefix", "namespace", NULL };
  NamespaceObject *self;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O!OO:Element", kwlist,
                                   &DomletteElement_Type, &parentNode,
                                   &prefix, &namespaceURI)) {
    return NULL;
  }

  prefix = XmlString_ConvertArgument(prefix, "prefix", 1);
  if (prefix == NULL) return NULL;

  namespaceURI = XmlString_ConvertArgument(namespaceURI, "namespace", 0);
  if (namespaceURI == NULL) {
    Py_DECREF(prefix);
    return NULL;
  }

  if (type != &DomletteNamespace_Type) {
    self = Namespace(type->tp_alloc(type, 0));
    if (self != NULL) {
      _Node_INIT(self);
      if (namespace_init(self, parentNode, prefix, namespaceURI) < 0) {
        Py_DECREF(self);
        self = NULL;
      }
    }
  } else {
    self = Namespace_New(parentNode, prefix, namespaceURI);
  }
  Py_DECREF(prefix);
  Py_DECREF(namespaceURI);

  return (PyObject *) self;
}

static char namespace_doc[] = "\
Namespace(parent, prefix, namespace) -> Namespace object\n\
\n\
The Namespace interface represents the XPath namespace node type\n\
that DOM lacks.";

PyTypeObject DomletteNamespace_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "Namespace",
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

  dict = DomletteNamespace_Type.tp_dict;

  value = PyString_FromString("namespace");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_type", value))
    return -1;
  Py_DECREF(value);

  Py_INCREF(&DomletteNamespace_Type);
  return PyModule_AddObject(module, "Namespace",
                            (PyObject*)&DomletteNamespace_Type);
}

void DomletteNamespace_Fini(void)
{
  PyType_CLEAR(&DomletteNamespace_Type);
}
