#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

Py_LOCAL_INLINE(int)
pi_init(ProcessingInstructionObject *self, PyObject *target, PyObject *data)
{
  if ((self == NULL || !ProcessingInstruction_Check(self)) ||
      (target == NULL || !XmlString_Check(target)) ||
      (data == NULL || !XmlString_Check(data))) {
    PyErr_BadInternalCall();
    return -1;
  }

  Py_INCREF(target);
  self->nodeName = target;

  Py_INCREF(data);
  self->nodeValue = data;

  return 0;
}

/** Public C API ******************************************************/

ProcessingInstructionObject *ProcessingInstruction_New(PyObject *target,
                                                       PyObject *data)
{
  ProcessingInstructionObject *self;

  self = Node_New(ProcessingInstructionObject,
                  &DomletteProcessingInstruction_Type);
  if (self != NULL) {
    if (pi_init(self, target, data) < 0) {
      Node_Del(self);
      return NULL;
    }
  }

  PyObject_GC_Track(self);

  return self;
}

ProcessingInstructionObject *ProcessingInstruction_CloneNode(PyObject *node,
                                                             int deep)
{
  PyObject *nodeValue, *target;
  ProcessingInstructionObject *newNode;

  nodeValue = PyObject_GetAttrString(node, "nodeValue");
  nodeValue = XmlString_FromObjectInPlace(nodeValue);
  target = PyObject_GetAttrString(node, "target");
  target = XmlString_FromObjectInPlace(target);
  if (nodeValue == NULL || target == NULL) {
    Py_XDECREF(nodeValue);
    Py_XDECREF(target);
    return NULL;
  }

  newNode = ProcessingInstruction_New(target, nodeValue);
  Py_DECREF(target);
  Py_DECREF(nodeValue);

  return newNode;
}

/** Python Methods ****************************************************/

#define ProcessingInstruction_METHOD(name) \
  { #name, (PyCFunction) pi_##name, METH_VARARGS, pi_##name##_doc }

static PyMethodDef pi_methods[] = {
  { NULL }
};

/** Python Members ****************************************************/

#define ProcessingInstruction_MEMBER(name, member) \
  { #name, T_OBJECT, offsetof(ProcessingInstructionObject, member), RO }

static PyMemberDef pi_members[] = {
  ProcessingInstruction_MEMBER(target, nodeName),
  ProcessingInstruction_MEMBER(nodeName, nodeName),
  { NULL }
};

/** Python Computed Members *******************************************/

static PyObject *get_data(ProcessingInstructionObject *self, void *arg)
{
  Py_INCREF(self->nodeValue);
  return self->nodeValue;
}

static int set_data(ProcessingInstructionObject *self, PyObject *v, char *arg)
{
  PyObject *nodeValue = XmlString_ConvertArgument(v, "data", 0);
  if (nodeValue == NULL) return -1;

  Py_DECREF(self->nodeValue);
  self->nodeValue = nodeValue;
  return 0;
}

static PyGetSetDef pi_getset[] = {
  { "data", (getter)get_data, (setter)set_data},
  { NULL }
};

/** Type Object *******************************************************/

static void pi_dealloc(ProcessingInstructionObject *self)
{
  PyObject_GC_UnTrack((PyObject *)self);
  Py_CLEAR(self->nodeName);
  Py_CLEAR(self->nodeValue);
  Node_Del(self);
}

static PyObject *pi_repr(ProcessingInstructionObject *self)
{
  PyObject *repr;
  PyObject *target = PyObject_Repr(self->nodeName);
  PyObject *data = PyObject_Repr(self->nodeValue);
  if (target == NULL || data == NULL) {
    Py_XDECREF(target);
    Py_XDECREF(data);
    return NULL;
  }
  repr = PyString_FromFormat(
    "<ProcessingInstruction at %p: target %s, data %s>",
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

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO:ProcessingInstruction",
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
      _Node_INIT(self);
      if (pi_init(self, target, data) < 0) {
        Py_DECREF(self);
        self = NULL;
      }
    }
  } else {
    self = ProcessingInstruction_New(target, data);
  }
  Py_DECREF(data);
  Py_DECREF(target);

  return (PyObject *) self;
}

static char pi_doc[] = "\
ProcessingInstruction(target, data) -> ProcessingInstruction\n\
\n\
The ProcessingInstruction interface represents a \"processing instruction\",\n\
used in XML as a way to keep processor-specific information in the text of\n\
the document.";

PyTypeObject DomletteProcessingInstruction_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "ProcessingInstruction",
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
  PyObject *value;

  DomletteProcessingInstruction_Type.tp_base = &DomletteNode_Type;
  if (PyType_Ready(&DomletteProcessingInstruction_Type) < 0)
    return -1;

  value = PyInt_FromLong(PROCESSING_INSTRUCTION_NODE);
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(DomletteProcessingInstruction_Type.tp_dict,
                           "xml_node_type", value))
    return -1;
  Py_DECREF(value);

  Py_INCREF(&DomletteProcessingInstruction_Type);
  return PyModule_AddObject(module, "ProcessingInstruction",
           (PyObject*) &DomletteProcessingInstruction_Type);
}

void DomletteProcessingInstruction_Fini(void)
{
  PyType_CLEAR(&DomletteProcessingInstruction_Type);
}
