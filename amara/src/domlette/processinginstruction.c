#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

#define ProcessingInstruction_SET_TARGET(op, v) \
  (ProcessingInstruction_GET_TARGET(op) = (v))
#define ProcessingInstruction_SET_DATA(op, v) \
  (ProcessingInstruction_GET_DATA(op) = (v))

Py_LOCAL_INLINE(ProcessingInstructionObject *)
pi_init(ProcessingInstructionObject *self, PyObject *target, PyObject *data)
{
  assert(self && ProcessingInstruction_Check(self));
  if ((target == NULL || !XmlString_Check(target)) ||
      (data == NULL || !XmlString_Check(data))) {
    PyErr_BadInternalCall();
    Py_DECREF(self);
    return NULL;
  }

  ProcessingInstruction_SET_TARGET(self, target);
  Py_INCREF(target);
  ProcessingInstruction_SET_DATA(self, data);
  Py_INCREF(data);

  return self;
}

/** Public C API ******************************************************/

ProcessingInstructionObject *ProcessingInstruction_New(PyObject *target,
                                                       PyObject *data)
{
  ProcessingInstructionObject *self;

  self = Node_New(ProcessingInstructionObject,
                  &DomletteProcessingInstruction_Type);
  if (self != NULL) {
    self = pi_init(self, target, data);
  }
  return self;
}

/** Python Methods ****************************************************/

static PyObject *pi_getnewargs(PyObject *self, PyObject *noarg)
{
  return PyTuple_Pack(2, ProcessingInstruction_GET_TARGET(self),
                      ProcessingInstruction_GET_DATA(self));
}

static PyMethodDef pi_methods[] = {
  { "__getnewargs__", pi_getnewargs, METH_NOARGS,  "helper for pickle" },
  { NULL }
};

/** Python Members ****************************************************/

#define ProcessingInstruction_OFFSET(name) \
  offsetof(ProcessingInstructionObject, name)

static PyMemberDef pi_members[] = {
  { "xml_target", T_OBJECT, ProcessingInstruction_OFFSET(pi_target), RO },
  { NULL }
};

/** Python Computed Members *******************************************/

static PyObject *get_data(ProcessingInstructionObject *self, void *arg)
{
  PyObject *data = ProcessingInstruction_GET_DATA(self);
  Py_INCREF(data);
  return data;
}

static int set_data(ProcessingInstructionObject *self, PyObject *v, char *arg)
{
  PyObject *data, *temp;

  data = XmlString_ConvertArgument(v, "xml_data", 0);
  if (data == NULL)
    return -1;
  temp = ProcessingInstruction_GET_DATA(self);
  ProcessingInstruction_SET_DATA(self, data);
  Py_DECREF(temp);
  return 0;
}

static PyGetSetDef pi_getset[] = {
  { "xml_data", (getter)get_data, (setter)set_data},
  { NULL }
};

/** Type Object *******************************************************/

static void pi_dealloc(ProcessingInstructionObject *self)
{
  PyObject_GC_UnTrack((PyObject *)self);
  Py_CLEAR(self->pi_target);
  Py_CLEAR(self->pi_data);
  Node_Del(self);
}

static PyObject *pi_repr(ProcessingInstructionObject *self)
{
  PyObject *repr;
  PyObject *target = PyObject_Repr(ProcessingInstruction_GET_TARGET(self));
  PyObject *data = PyObject_Repr(ProcessingInstruction_GET_DATA(self));
  if (target == NULL || data == NULL) {
    Py_XDECREF(target);
    Py_XDECREF(data);
    return NULL;
  }
  repr = PyString_FromFormat(
    "<processing_instruction at %p: target %s, data %s>",
    self, PyString_AsString(target), PyString_AsString(data));
  Py_DECREF(target);
  Py_DECREF(data);
  return repr;
}

static PyObject *pi_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  PyObject *target, *data;
  static char *kwlist[] = { "target", "data", NULL };
  ProcessingInstructionObject *self;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO:processing_instruction",
                                   kwlist, &target, &data)) {
    return NULL;
  }

  target = XmlString_ConvertArgument(target, "target", 0);
  if (target == NULL) return NULL;

  data = XmlString_ConvertArgument(data, "data", 0);
  if (data == NULL) {
    Py_DECREF(target);
    return NULL;
  }

  if (type != &DomletteProcessingInstruction_Type) {
    self = ProcessingInstruction(type->tp_alloc(type, 0));
    if (self != NULL) {
      self =  pi_init(self, target, data);
    }
  } else {
    self = ProcessingInstruction_New(target, data);
  }
  Py_DECREF(data);
  Py_DECREF(target);

  return (PyObject *) self;
}

static char pi_doc[] = "\
processing_instruction(target, data) -> processing_instruction object\n\
\n\
The `processing_instruction` interface represents a processing instruction,\n\
used in XML as a way to keep processor-specific information in the text of\n\
the document.";

PyTypeObject DomletteProcessingInstruction_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "processing_instruction",
  /* tp_basicsize      */ sizeof(ProcessingInstructionObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) pi_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) pi_repr,
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
  /* tp_doc            */ (char *) pi_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) pi_methods,
  /* tp_members        */ (PyMemberDef *) pi_members,
  /* tp_getset         */ (PyGetSetDef *) pi_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) pi_new,
  /* tp_free           */ 0,
};

/** Module Interface **************************************************/

int DomletteProcessingInstruction_Init(PyObject *module)
{
  PyObject *dict, *value;

  DomletteProcessingInstruction_Type.tp_base = &DomletteNode_Type;
  if (PyType_Ready(&DomletteProcessingInstruction_Type) < 0)
    return -1;
  dict = DomletteProcessingInstruction_Type.tp_dict;

  value = PyString_FromString("processing-instruction");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_type", value))
    return -1;
  Py_DECREF(value);
  /* add the "typecode" character for use with `xml_nodeid` */
  value = PyString_FromString("p");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_typecode", value) < 0)
    return -1;
  Py_DECREF(value);

  Py_INCREF(&DomletteProcessingInstruction_Type);
  return PyModule_AddObject(module, "processing_instruction",
           (PyObject*) &DomletteProcessingInstruction_Type);
}

void DomletteProcessingInstruction_Fini(void)
{
  PyType_CLEAR(&DomletteProcessingInstruction_Type);
}
