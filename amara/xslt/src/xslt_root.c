#include "xslt_node.h"
#include "xslt_root.h"

/** Private Routines **************************************************/


/** Public C API ******************************************************/

XsltRootObject *XsltRoot_New(PyObject *baseUri)
{
  XsltRootObject *self;

  self = (XsltRootObject *) XsltNode_New(&XsltRoot_Type);
  if (self == NULL) return NULL;

  Py_DECREF(XsltNode_ROOT(self));
  Py_INCREF((PyObject *) self);
  XsltNode_ROOT(self) = (PyObject *) self;

  if ((self->primeInstructions = PyList_New(0)) == NULL) {
    Py_DECREF((PyObject *) self);
    return NULL;
  }

  if ((self->idleInstructions = PyList_New(0)) == NULL) {
    Py_DECREF(self->primeInstructions);
    Py_DECREF((PyObject *) self);
    return NULL;
  }

  if ((self->sources = PyDict_New()) == NULL) {
    Py_DECREF(self->idleInstructions);
    Py_DECREF(self->primeInstructions);
    Py_DECREF((PyObject *) self);
    return NULL;
  }

  if ((self->sourceNodes = PyDict_New()) == NULL) {
    Py_DECREF(self->sources);
    Py_DECREF(self->idleInstructions);
    Py_DECREF(self->primeInstructions);
    Py_DECREF((PyObject *) self);
    return NULL;
  }

  Py_INCREF(baseUri);
  self->baseUri = baseUri;

  Py_INCREF(Py_None);
  self->stylesheet = Py_None;

  return self;
}

int XsltRoot_AppendChild(XsltRootObject *self, XsltNodeObject *child)
{
  if (!XsltRoot_Check(self) || !XsltNode_Check(child)) {
    PyErr_BadInternalCall();
    return -1;
  }

  /* Make the node our only child */
  Py_DECREF(self->stylesheet);
  Py_INCREF(child);
  self->stylesheet = (PyObject *) child;

  /* Set its parent link */
  Py_DECREF(child->parent);
  Py_INCREF((PyObject *) self);
  child->parent = (PyObject *) self;

  return 0;
}

/** Python Methods ****************************************************/

static char appendChild_doc[] = "\
appendChild(child)\n\
\n\
Appends the child to the end of the children list.";

static PyObject *root_appendChild(XsltRootObject *self, PyObject *args)
{
  PyObject *child;

  if (!PyArg_ParseTuple(args, "O!:appendChild", &XsltNode_Type, &child))
    return NULL;

  if (XsltRoot_AppendChild(self, (XsltNodeObject *) child) == -1) {
    return NULL;
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static char getstate_doc[] = "helper for pickle";

static PyObject *root_getstate(XsltRootObject *self, PyObject *args)
{
  PyObject *state;

  if (!PyArg_ParseTuple(args, ":__getstate__"))
    return NULL;

  state = PyTuple_New(5);
  if (state == NULL)
    return NULL;

  /* XsltRoot.baseUri */
  Py_INCREF(self->baseUri);
  PyTuple_SET_ITEM(state, 0, self->baseUri);

  /* XsltRoot.stylesheet */
  Py_INCREF(self->stylesheet);
  PyTuple_SET_ITEM(state, 1, self->stylesheet);

  /* XsltRoot.primeInstructions */
  Py_INCREF(self->primeInstructions);
  PyTuple_SET_ITEM(state, 2, self->primeInstructions);

  /* XsltRoot.idleInstructions */
  Py_INCREF(self->idleInstructions);
  PyTuple_SET_ITEM(state, 3, self->idleInstructions);

  /* XsltRoot.sources */
  Py_INCREF(self->sources);
  PyTuple_SET_ITEM(state, 4, self->sources);

  return state;
}

static char setstate_doc[] = "helper for pickle";

static PyObject *root_setstate(XsltRootObject *self, PyObject *args)
{
  PyObject *base, *stylesheet, *prime, *idle, *sources, *temp;

  if (!PyArg_ParseTuple(args, "(OOOOO):__setstate__",
                        &base, &stylesheet, &prime, &idle, &sources))
    return NULL;

  temp = self->baseUri;
  Py_INCREF(base);
  self->baseUri = base;
  Py_DECREF(temp);

  temp = self->stylesheet;
  Py_INCREF(stylesheet);
  self->stylesheet = stylesheet;
  Py_DECREF(temp);

  temp = self->primeInstructions;
  Py_INCREF(prime);
  self->primeInstructions = prime;
  Py_DECREF(temp);

  temp = self->idleInstructions;
  Py_INCREF(idle);
  self->idleInstructions = idle;
  Py_DECREF(temp);

  temp = self->sources;
  Py_INCREF(sources);
  self->sources = sources;
  Py_DECREF(temp);

  Py_INCREF(Py_None);
  return Py_None;
}

#define XsltRoot_METHOD(NAME) \
  { #NAME, (PyCFunction) root_##NAME, METH_VARARGS, NAME##_doc }

static struct PyMethodDef root_methods[] = {
  XsltRoot_METHOD(appendChild),
  { "__getstate__", (PyCFunction) root_getstate, METH_VARARGS, getstate_doc },
  { "__setstate__", (PyCFunction) root_setstate, METH_VARARGS, setstate_doc },
  { NULL }
};

/** Python Members *****************************************************/

#define XsltRoot_MEMBER(name, flags) \
  { #name, T_OBJECT, offsetof(XsltRootObject, name), flags }

static struct PyMemberDef root_members[] = {
  XsltRoot_MEMBER(baseUri, 0),
  XsltRoot_MEMBER(stylesheet, READONLY),
  XsltRoot_MEMBER(primeInstructions, READONLY),
  XsltRoot_MEMBER(idleInstructions, READONLY),
  XsltRoot_MEMBER(sources, READONLY),
  XsltRoot_MEMBER(sourceNodes, READONLY),
  { NULL }
};

/** Python Computed Members ********************************************/

static PyObject *get_children(XsltRootObject *self, void *arg)
{
  PyObject *result;

  if (self->stylesheet == Py_None) {
    result = PyList_New(0);
  } else {
    result = PyList_New(1);
    if (result != NULL) {
      Py_INCREF(self->stylesheet);
      PyList_SET_ITEM(result, 0, self->stylesheet);
    }
  }

  return result;
}

static struct PyGetSetDef root_getset[] = {
  { "children", (getter) get_children },
  { NULL }
};

/** Type Object ********************************************************/

static PyObject *root_repr(XsltRootObject *self)
{
  return PyString_FromFormat("<XsltRoot at %p>", self);
}

static int root_traverse(XsltRootObject *self, visitproc visit, void *arg)
{
  int rt;

  if (self->stylesheet != NULL) {
    rt = visit(self->stylesheet, arg);
    if (rt) return rt;
  }

  if (self->primeInstructions != NULL) {
    rt = visit(self->primeInstructions, arg);
    if (rt) return rt;
  }

  if (self->idleInstructions != NULL) {
    rt = visit(self->idleInstructions, arg);
    if (rt) return rt;
  }

  if (self->sources != NULL) {
    rt = visit(self->sources, arg);
    if (rt) return rt;
  }

  if (self->sourceNodes != NULL) {
    rt = visit(self->sourceNodes, arg);
    if (rt) return rt;
  }

  if (XsltNode_Type.tp_traverse)
    return XsltNode_Type.tp_traverse((PyObject *)self, visit, arg);

  return 0;
}

static int root_clear(XsltRootObject *self)
{
  PyObject *tmp;

  if (self->stylesheet != NULL) {
    tmp = self->stylesheet;
    self->stylesheet = NULL;
    Py_DECREF(tmp);
  }

  if (self->primeInstructions != NULL) {
    tmp = self->primeInstructions;
    self->primeInstructions = NULL;
    Py_DECREF(tmp);
  }

  if (self->idleInstructions != NULL) {
    tmp = self->idleInstructions;
    self->idleInstructions = NULL;
    Py_DECREF(tmp);
  }

  if (self->sources != NULL) {
    tmp = self->sources;
    self->sources = NULL;
    Py_DECREF(tmp);
  }

  if (self->sourceNodes != NULL) {
    tmp = self->sourceNodes;
    self->sourceNodes = NULL;
    Py_DECREF(tmp);
  }

  if (XsltNode_Type.tp_clear)
    return XsltNode_Type.tp_clear((PyObject *) self);

  return 0;
}


static void root_dealloc(XsltRootObject *self)
{
  if (self->baseUri != NULL) {
    Py_DECREF(self->baseUri);
    self->baseUri = NULL;
  }

  root_clear(self);

  XsltNode_Type.tp_dealloc((PyObject *) self);
}


static int root_init(XsltRootObject *self, PyObject *args, PyObject *kwds)
{
  PyObject *baseUri, *temp;
  static char *kwlist[] = { "baseUri", NULL };

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:XsltRoot", kwlist,
                                   &baseUri))
    return -1;

  temp = self->baseUri;
  Py_INCREF(baseUri);
  self->baseUri = baseUri;
  Py_DECREF(temp);

  return 0;
}


static PyObject *root_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  return (PyObject *) XsltRoot_New(Py_None);
}


static char root_doc[] = "\
This interface represents the root node of the Stylesheet Tree.";

PyTypeObject XsltRoot_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "Ft.Xml.Xslt.cStylesheetTree.XsltRoot",
  /* tp_basicsize      */ sizeof(XsltRootObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) root_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) root_repr,
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
                           Py_TPFLAGS_HAVE_GC),
  /* tp_doc            */ (char *) root_doc,
  /* tp_traverse       */ (traverseproc) root_traverse,
  /* tp_clear          */ (inquiry) root_clear,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) root_methods,
  /* tp_members        */ (PyMemberDef *) root_members,
  /* tp_getset         */ (PyGetSetDef *) root_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) root_init,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) root_new,
  /* tp_free           */ 0,
};

/** Module Setup & Teardown *******************************************/

int XsltRoot_Init(PyObject *module)
{
  PyTypeObject *type;
  PyObject *dict, *constant;

  type = &XsltRoot_Type;
  type->tp_base = &XsltNode_Type;
  if (PyType_Ready(type) < 0) return -1;
  if (PyModule_AddObject(module, "xslt_root", (PyObject *)type)) return -1;

  /* Assign "class" constants */
  dict = XsltRoot_Type.tp_dict;

  /* nodeName = "#document" */
  constant = PyUnicode_DecodeASCII("#document", 9, NULL);
  if (constant == NULL) return -1;
  if (PyDict_SetItemString(dict, "nodeName", constant)) return -1;
  Py_DECREF(constant);

  return 0;
}


void XsltRoot_Fini(void)
{
  PyDict_Clear(XsltRoot_Type.tp_dict);
}
