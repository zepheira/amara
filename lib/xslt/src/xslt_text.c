#include "xslt_text.h"
#include "xslt_root.h"

/** Private Routines **************************************************/

/* The maximum number of characters of the nodeValue to use when
   creating the repr string.
*/
#define DATA_REPR_LIMIT 20

/** Public C API ******************************************************/

XsltNodeObject *XsltText_New(XsltRootObject *root, PyObject *data)
{
  XsltTextObject *self;

  if (!PyUnicode_Check(data)) {
    PyErr_BadInternalCall();
    return NULL;
  }

  self = (XsltTextObject *) XsltNode_New(&XsltText_Type);
  if (self != NULL) {
    Py_DECREF(XsltNode_ROOT(self));
    Py_INCREF((PyObject *) root);
    XsltNode_ROOT(self) = (PyObject *) root;

    Py_INCREF(data);
    self->data = data;
  }

  return (XsltNodeObject *) self;
}

/** Python Methods ****************************************************/

static PyObject *text_instantiate(PyObject *self, PyObject *args)
{
  PyObject *context;

  if (!PyArg_ParseTuple(args, "O:instantiate", &context))
    return NULL;

  return PyObject_CallMethod(context, "text", "O", XsltText_DATA(self));
}

static char getstate_doc[] = "helper for pickle";

static PyObject *text_getstate(XsltTextObject *self, PyObject *args)
{
  PyObject *state;

  if (!PyArg_ParseTuple(args, ":__getstate__"))
    return NULL;

  state = PyTuple_New(3);
  if (state == NULL)
    return NULL;

  /* XsltText.root */
  Py_INCREF(XsltNode_ROOT(self));
  PyTuple_SET_ITEM(state, 0, XsltNode_ROOT(self));

  /* XsltText.parent */
  Py_INCREF(XsltNode_GET_PARENT(self));
  PyTuple_SET_ITEM(state, 1, XsltNode_GET_PARENT(self));

  /* XsltText.data */
  Py_INCREF(self->data);
  PyTuple_SET_ITEM(state, 2, self->data);

  return state;
}

static char setstate_doc[] = "helper for pickle";

static PyObject *text_setstate(XsltTextObject *self, PyObject *args)
{
  PyObject *root, *parent, *data, *temp;

  if (!PyArg_ParseTuple(args, "(OOO):__setstate__", &root, &parent, &data))
    return NULL;

  temp = XsltNode_ROOT(self);
  Py_INCREF(root);
  XsltNode_ROOT(self) = root;
  Py_DECREF(temp);

  temp = XsltNode_GET_PARENT(self);
  Py_INCREF(parent);
  XsltNode_SET_PARENT(self, parent);
  Py_DECREF(temp);

  temp = self->data;
  Py_INCREF(data);
  self->data = data;
  Py_DECREF(temp);

  Py_INCREF(Py_None);
  return Py_None;
}

static struct PyMethodDef text_methods[] = {
  { "instantiate", text_instantiate, METH_VARARGS, NULL },
  { "__getstate__", (PyCFunction)text_getstate, METH_VARARGS, getstate_doc },
  { "__setstate__", (PyCFunction)text_setstate, METH_VARARGS, setstate_doc },
  { NULL }
};

/** Python Members *****************************************************/

static struct PyMemberDef text_members[] = {
  { "data", T_OBJECT, offsetof(XsltTextObject, data), RO },
  { NULL }
};

/** Python Computed Members ********************************************/

static PyGetSetDef text_getsets[] = {
  { NULL }
};

/** Type Object ********************************************************/

static void text_dealloc(XsltTextObject *self)
{
  Py_XDECREF(self->data);
  self->data = NULL;
  assert(XsltNode_Type.tp_dealloc);
  XsltNode_Type.tp_dealloc((PyObject *) self);
}

static PyObject *text_repr(XsltTextObject *self)
{
  PyObject *obj, *repr;

  if (PyUnicode_GET_SIZE(self->data) > DATA_REPR_LIMIT) {
    Py_UNICODE dots[] = { '.', '.', '.' };
    PyObject *slice, *ellipsis;
    slice = PyUnicode_FromUnicode(PyUnicode_AS_UNICODE(self->data),
                                  DATA_REPR_LIMIT);
    ellipsis = PyUnicode_FromUnicode(dots, 3);
    if (slice == NULL || ellipsis == NULL) {
      Py_XDECREF(slice);
      Py_XDECREF(ellipsis);
      return NULL;
    }
    obj = PyUnicode_Concat(slice, ellipsis);
    Py_DECREF(slice);
    Py_DECREF(ellipsis);
    if (obj == NULL) return NULL;
  } else {
    obj = self->data;
    Py_INCREF(obj);
  }

  repr = PyObject_Repr(obj);
  Py_DECREF(obj);
  if (repr == NULL) return NULL;

  obj = PyString_FromFormat("<XsltText at %p: %s>",
                            self,
                            PyString_AS_STRING(repr));
  Py_DECREF(repr);
  return obj;
}

static int text_init(XsltTextObject *self, PyObject *args, PyObject *kwds)
{
  PyObject *root, *data, *temp;
  static char *kwlist[] = { "root", "data", NULL };

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O!O:XsltText", kwlist,
                                   &XsltRoot_Type, &root, &data))
    return -1;

  data = PyUnicode_FromObject(data);
  if (data == NULL) return -1;

  temp = XsltNode_ROOT(self);
  Py_INCREF(root);
  XsltNode_ROOT(self) = root;
  Py_DECREF(temp);

  temp = self->data;
  self->data = data;
  Py_DECREF(temp);

  return 0;
}

static PyObject *text_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  XsltTextObject *self = (XsltTextObject *) XsltNode_New(&XsltText_Type);
  if (self) {
    Py_INCREF(Py_None);
    self->data = Py_None;
  }
  return (PyObject *) self;
}

static char text_doc[] = "\
This interface represents the content of a text node.";

PyTypeObject XsltText_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "amara.xslt.tree.xslt_text",
  /* tp_basicsize      */ sizeof(XsltTextObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) text_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) text_repr,
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
  /* tp_doc            */ (char *) text_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) text_methods,
  /* tp_members        */ (PyMemberDef *) text_members,
  /* tp_getset         */ (PyGetSetDef *) text_getsets,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) text_init,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) text_new,
  /* tp_free           */ 0,
};

/** Module Setup & Teardown *******************************************/

int XsltText_Init(PyObject *module)
{
  PyObject *dict, *constant;

  XsltText_Type.tp_base = &XsltNode_Type;
  if (PyType_Ready(&XsltText_Type) < 0)
    return -1;

  if (PyModule_AddObject(module, "xslt_text", (PyObject *) &XsltText_Type))
    return -1;

  /* Assign "class" constants */
  dict = XsltText_Type.tp_dict;

  constant = PyUnicode_DecodeASCII("#text", 5, NULL);
  if (constant == NULL) return -1;
  if (PyDict_SetItemString(dict, "nodeName", constant)) return -1;
  Py_DECREF(constant);

  return 0;
}

void XsltText_Fini(void)
{
  PyDict_Clear(XsltText_Type.tp_dict);
}
