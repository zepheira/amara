#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

Py_LOCAL_INLINE(int)
xns_init(XPathNamespaceObject *self, ElementObject *parentNode,
         PyObject *prefix, PyObject *namespaceURI)
{
  if ((self == NULL || !XPathNamespace_Check(self)) ||
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

/** C API **************************************************************/

XPathNamespaceObject *XPathNamespace_New(ElementObject *parentNode,
                                         PyObject *prefix,
                                         PyObject *namespaceURI)
{
  XPathNamespaceObject *self;

  if (parentNode == NULL || !Element_Check(parentNode)) {
    PyErr_BadInternalCall();
    return NULL;
  }

  self = Node_New(XPathNamespaceObject, &DomletteXPathNamespace_Type);
  if (self != NULL) {
    if (xns_init(self, parentNode, prefix, namespaceURI) < 0) {
      Node_Del(self);
      return NULL;
    }
  }

  PyObject_GC_Track(self);

  return self;
}

/** Python Methods ****************************************************/

#define XPathNamespace_METHOD(name) \
  { #name, (PyCFunction) xns_##name, METH_VARARGS, xns_##name##_doc }

static PyMethodDef xns_methods[] = {
  { NULL }
};

/** Python Members ****************************************************/

#define XPathNamespace_MEMBER(name, member) \
  { #name, T_OBJECT, offsetof(XPathNamespaceObject, member), RO }

static PyMemberDef xns_members[] = {
  XPathNamespace_MEMBER(nodeName, nodeName),
  XPathNamespace_MEMBER(localName, nodeName),
  XPathNamespace_MEMBER(nodeValue, nodeValue),
  XPathNamespace_MEMBER(value, nodeValue),
  { NULL }
};

/** Python Computed Members *******************************************/

static PyGetSetDef xns_getset[] = {
  { NULL }
};

/** Type Object ********************************************************/

static void xns_dealloc(XPathNamespaceObject *self)
{
  PyObject_GC_UnTrack((PyObject *) self);
  Py_CLEAR(self->nodeValue);
  Py_CLEAR(self->nodeName);
  Node_Del(self);
}

static PyObject *xns_repr(XPathNamespaceObject *self)
{
  PyObject *repr;
  PyObject *name = PyObject_Repr(self->nodeName);
  PyObject *value = PyObject_Repr(self->nodeValue);
  if (name == NULL || value == NULL) {
    Py_XDECREF(name);
    Py_XDECREF(value);
    return NULL;
  }
  repr = PyString_FromFormat("<XPathNamespace at %p: name %s, value %s>",
                             self,
                             PyString_AsString(name),
                             PyString_AsString(value));
  Py_DECREF(name);
  Py_DECREF(value);
  return repr;
}

static PyObject *xns_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  ElementObject *parentNode;
  PyObject *prefix, *namespaceURI;
  static char *kwlist[] = { "parentNode", "prefix", "namespaceURI", NULL };
  XPathNamespaceObject *self;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O!OO:Element", kwlist,
                                   &DomletteElement_Type, &parentNode,
                                   &prefix, &namespaceURI)) {
    return NULL;
  }

  prefix = XmlString_ConvertArgument(prefix, "prefix", 1);
  if (prefix == NULL) return NULL;

  namespaceURI = XmlString_ConvertArgument(namespaceURI, "namespaceURI", 0);
  if (namespaceURI == NULL) {
    Py_DECREF(prefix);
    return NULL;
  }

  if (type != &DomletteXPathNamespace_Type) {
    self = XPathNamespace(type->tp_alloc(type, 0));
    if (self != NULL) {
      _Node_INIT(self);
      if (xns_init(self, parentNode, prefix, namespaceURI) < 0) {
        Py_DECREF(self);
        self = NULL;
      }
    }
  } else {
    self = XPathNamespace_New(parentNode, prefix, namespaceURI);
  }
  Py_DECREF(prefix);
  Py_DECREF(namespaceURI);

  return (PyObject *) self;
}

static char xns_doc[] = "\
XPathNamespace(parentNode, prefix, namespaceURI) -> XPathNamespace object\n\
\n\
The XPathNamespace interface represents the XPath namespace node type\n\
that DOM lacks.";

PyTypeObject DomletteXPathNamespace_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "XPathNamespace",
  /* tp_basicsize      */ sizeof(XPathNamespaceObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) xns_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) xns_repr,
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
  /* tp_doc            */ (char *) xns_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) xns_methods,
  /* tp_members        */ (PyMemberDef *) xns_members,
  /* tp_getset         */ (PyGetSetDef *) xns_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) xns_new,
  /* tp_free           */ 0,
};

/** Module Interface **************************************************/

int DomletteXPathNamespace_Init(PyObject *module)
{
  PyObject *dict, *value;

  DomletteXPathNamespace_Type.tp_base = &DomletteNode_Type;
  if (PyType_Ready(&DomletteXPathNamespace_Type) < 0)
    return -1;

  dict = DomletteXPathNamespace_Type.tp_dict;

  value = PyInt_FromLong(XPATH_NAMESPACE_NODE);
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "nodeType", value))
    return -1;
  Py_DECREF(value);

  Py_INCREF(&DomletteXPathNamespace_Type);
  return PyModule_AddObject(module, "XPathNamespace",
           (PyObject*) &DomletteXPathNamespace_Type);
}

void DomletteXPathNamespace_Fini(void)
{
  PyType_CLEAR(&DomletteXPathNamespace_Type);
}
