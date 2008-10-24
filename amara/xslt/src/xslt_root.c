#include "xslt_node.h"
#include "xslt_root.h"

/** Private Routines **************************************************/

static PyObject *setup_string;
static PyObject *validate_string;
static PyObject *prime_string;
static PyObject *teardown_string;

/** Public C API ******************************************************/

XsltRootObject *XsltRoot_New(PyObject *baseUri)
{
  XsltRootObject *self;

  self = (XsltRootObject *) XsltNode_New(&XsltRoot_Type);
  if (self == NULL) return NULL;

  Py_DECREF(XsltNode_ROOT(self));
  Py_INCREF((PyObject *) self);
  XsltNode_ROOT(self) = (PyObject *) self;

  if ((self->validate_instructions = PyList_New(0)) == NULL) {
    Py_DECREF((PyObject *) self);
    return NULL;
  }

  if ((self->prime_instructions = PyList_New(0)) == NULL) {
    Py_DECREF(self->validate_instructions);
    Py_DECREF((PyObject *) self);
    return NULL;
  }

  if ((self->teardown_instructions = PyList_New(0)) == NULL) {
    Py_DECREF(self->validate_instructions);
    Py_DECREF(self->prime_instructions);
    Py_DECREF((PyObject *) self);
    return NULL;
  }

  if ((self->sources = PyDict_New()) == NULL) {
    Py_DECREF(self->teardown_instructions);
    Py_DECREF(self->prime_instructions);
    Py_DECREF(self->validate_instructions);
    Py_DECREF((PyObject *) self);
    return NULL;
  }

  if ((self->sourceNodes = PyDict_New()) == NULL) {
    Py_DECREF(self->sources);
    Py_DECREF(self->teardown_instructions);
    Py_DECREF(self->prime_instructions);
    Py_DECREF(self->validate_instructions);
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
  PyObject *temp;

  if (!XsltRoot_Check(self) || !XsltNode_Check(child)) {
    PyErr_BadInternalCall();
    return -1;
  }

  /* Make the node our only child */
  temp = self->stylesheet;
  Py_INCREF(child);
  self->stylesheet = (PyObject *) child;
  Py_DECREF(temp);

  /* Set its parent link */
  return XsltNode_Link(XsltNode(self), child);
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

static char prime_doc[] = "prime(context)";

static PyObject *root_prime(XsltRootObject *self, PyObject *args)
{
  PyObject *context;
  PyObject *nodes = self->prime_instructions;
  Py_ssize_t i, size;

  if (!PyArg_ParseTuple(args, "O:prime", &context))
    return NULL;

  if (PyDict_Size(self->sourceNodes)) {
    PyObject *documents = PyObject_GetAttrString(context, "documents");
    if (documents == NULL)
      return NULL;
    if (PyDict_Merge(documents, self->sourceNodes, 1) < 0) {
      Py_DECREF(documents);
      return NULL;
    }
    Py_DECREF(documents);
  }

  /* Call `prime()` for those nodes that have it defined. */
  size = PyList_GET_SIZE(nodes);
  for (i = 0; i < size; i++) {
    PyObject *result = PyList_GET_ITEM(nodes, i);
    PyObject *func = PyObject_GetAttr(result, prime_string);
    if (func == NULL) return NULL;
    result = PyObject_Call(func, args, NULL);
    Py_DECREF(func);
    if (result == NULL) return NULL;
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static char teardown_doc[] = "teardown()";

static PyObject *root_teardown(XsltRootObject *self, PyObject *args)
{
  PyObject *nodes = self->teardown_instructions;
  Py_ssize_t i, size;

  if (!PyArg_ParseTuple(args, ":teardown"))
    return NULL;

  /* Call `teardown()` for those nodes that have it defined. */
  size = PyList_GET_SIZE(nodes);
  for (i = 0; i < size; i++) {
    PyObject *result = PyList_GET_ITEM(nodes, i);
    PyObject *func = PyObject_GetAttr(result, teardown_string);
    Py_DECREF(result);
    if (func == NULL) return NULL;
    result = PyObject_Call(func, args, NULL);
    Py_DECREF(func);
    if (result == NULL) return NULL;
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static char getstate_doc[] = "helper for pickle";

static PyObject *root_getstate(XsltRootObject *self, PyObject *args)
{
  if (!PyArg_ParseTuple(args, ":__getstate__"))
    return NULL;

  return PyTuple_Pack(6, self->baseUri, self->stylesheet,
                      self->validate_instructions, self->prime_instructions,
                      self->teardown_instructions, self->sources);
}

static char setstate_doc[] = "helper for pickle";

static PyObject *root_setstate(XsltRootObject *self, PyObject *args)
{
  PyObject *base, *stylesheet, *validate, *prime, *teardown, *sources, *temp;

  if (!PyArg_ParseTuple(args, "(OOOOOO):__setstate__",
                        &base, &stylesheet, &validate, &prime, &teardown,
                        &sources))
    return NULL;

  temp = self->baseUri;
  Py_INCREF(base);
  self->baseUri = base;
  Py_DECREF(temp);

  temp = self->stylesheet;
  Py_INCREF(stylesheet);
  self->stylesheet = stylesheet;
  Py_DECREF(temp);

  temp = self->validate_instructions;
  Py_INCREF(validate);
  self->validate_instructions = validate;
  Py_DECREF(temp);

  temp = self->prime_instructions;
  Py_INCREF(prime);
  self->prime_instructions = prime;
  Py_DECREF(temp);

  temp = self->teardown_instructions;
  Py_INCREF(teardown);
  self->teardown_instructions = teardown;
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
  XsltRoot_METHOD(prime),
  XsltRoot_METHOD(teardown),
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
  Py_VISIT(self->stylesheet);
  Py_VISIT(self->validate_instructions);
  Py_VISIT(self->prime_instructions);
  Py_VISIT(self->teardown_instructions);
  Py_VISIT(self->sources);
  Py_VISIT(self->sourceNodes);

  if (XsltNode_Type.tp_traverse)
    return XsltNode_Type.tp_traverse((PyObject *)self, visit, arg);

  return 0;
}

static int root_clear(XsltRootObject *self)
{
  Py_CLEAR(self->stylesheet);
  Py_CLEAR(self->validate_instructions);
  Py_CLEAR(self->prime_instructions);
  Py_CLEAR(self->teardown_instructions);
  Py_CLEAR(self->sources);
  Py_CLEAR(self->sourceNodes);

  if (XsltNode_Type.tp_clear)
    return XsltNode_Type.tp_clear((PyObject *) self);

  return 0;
}


static void root_dealloc(XsltRootObject *self)
{
  Py_CLEAR(self->baseUri);
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
This interface represents the root node of the stylesheet tree.";

PyTypeObject XsltRoot_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "amara.xslt.tree.xslt_root",
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

  /* Initialize constants */
  setup_string = PyString_FromString("setup");
  if (setup_string == NULL) return -1;
  validate_string = PyString_FromString("validate");
  if (validate_string == NULL) return -1;
  prime_string = PyString_FromString("prime");
  if (prime_string == NULL) return -1;
  teardown_string = PyString_FromString("teardown");
  if (teardown_string == NULL) return -1;

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
  Py_DECREF(setup_string);
  Py_DECREF(validate_string);
  Py_DECREF(prime_string);
  Py_DECREF(teardown_string);
  PyDict_Clear(XsltRoot_Type.tp_dict);
}
