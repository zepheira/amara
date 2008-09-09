#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

/* The maximum number of characters of the value to use when
   creating the repr string.
*/
#define CHARACTERDATA_REPR_LIMIT 20

Py_LOCAL_INLINE(CharacterDataObject *)
characterdata_init(CharacterDataObject *self, PyObject *data)
{
  assert(self && CharacterData_Check(self));
  if (data == NULL || !XmlString_Check(data)) {
    PyErr_BadInternalCall();
    Py_DECREF(self);
    return NULL;
  }
  assert(CharacterData_GET_VALUE(self) == NULL);
  CharacterData_SET_VALUE(self, data);
  Py_INCREF(data);
  return self;
}

/** Public C API ******************************************************/

CharacterDataObject *_CharacterData_New(PyTypeObject *type, PyObject *data)
{
  CharacterDataObject *self;

  self = Node_New(CharacterDataObject, type);
  if (self != NULL) {
    self = characterdata_init(self, data);
  }
  return self;
}

/** Python Methods ****************************************************/

static PyObject *characterdata_getnewargs(PyObject *self, PyObject *noargs)
{
  return PyTuple_Pack(1, CharacterData_GET_VALUE(self));
}

static PyMethodDef characterdata_methods[] = {
  { "__getnewargs__", characterdata_getnewargs, METH_NOARGS,
    "helper for pickle" },
  { NULL }
};

/** Python Members *****************************************************/

static PyMemberDef characterdata_members[] = {
  { NULL }
};

/** Python Computed Members ********************************************/

static PyObject *get_value(CharacterDataObject *self, void *arg)
{
  Py_INCREF(CharacterData_GET_VALUE(self));
  return CharacterData_GET_VALUE(self);
}

static int set_value(CharacterDataObject *self, PyObject *v, void *arg)
{
  PyObject *temp, *value;

  value = XmlString_ConvertArgument(v, "xml_value", 0);
  if (value == NULL)
    return -1;
  temp = CharacterData_GET_VALUE(self);
  CharacterData_SET_VALUE(self, value);
  Py_DECREF(temp);
  return 0;
}

static PyGetSetDef characterdata_getset[] = {
  { "xml_value", (getter)get_value, (setter)set_value },
  { NULL }
};

/** Type Object ********************************************************/

static void characterdata_dealloc(CharacterDataObject *self)
{
  PyObject_GC_UnTrack((PyObject *) self);
  Py_CLEAR(CharacterData_GET_VALUE(self));
  Node_Del(self);
}

static PyObject *characterdata_repr(CharacterDataObject *self)
{
  PyObject *value, *obj, *repr, *name;

  value = CharacterData_GET_VALUE(self);
  if (PyUnicode_GET_SIZE(value) > CHARACTERDATA_REPR_LIMIT) {
    Py_UNICODE *src, *dst;

    obj = PyUnicode_FromUnicode(NULL, CHARACTERDATA_REPR_LIMIT + 3);
    if (obj == NULL) {
      return NULL;
    }
    /* copy the first part of the node value */
    src = PyUnicode_AS_UNICODE(value);
    dst = PyUnicode_AS_UNICODE(obj);
    Py_UNICODE_COPY(dst, src, (CHARACTERDATA_REPR_LIMIT / 2));
    dst += (CHARACTERDATA_REPR_LIMIT / 2);

    /* add the ellipsis */
    *dst++ = '.';
    *dst++ = '.';
    *dst++ = '.';

    /* copy the last part of the node value */
    src += PyUnicode_GET_SIZE(value);
    src -= (CHARACTERDATA_REPR_LIMIT / 2);
    Py_UNICODE_COPY(dst, src, (CHARACTERDATA_REPR_LIMIT / 2));
  } else {
    obj = value;
    Py_INCREF(obj);
  }

  name = PyObject_GetAttrString((PyObject *)self->ob_type, "__name__");
  if (name == NULL) {
    Py_DECREF(obj);
    return NULL;
  }

  repr = PyObject_Repr(obj);
  Py_DECREF(obj);
  if (repr == NULL) {
    Py_DECREF(name);
    return NULL;
  }

  /* `name` and `repr` should be PyStringObject, but play it safe and use
   * the error-checking function instead of the lookup macro. */
  obj = PyString_FromFormat("<%s at %p: %s>", PyString_AsString(name), self,
                            PyString_AsString(repr));
  Py_DECREF(name);
  Py_DECREF(repr);
  return obj;
}

static PyObject *characterdata_new(PyTypeObject *type, PyObject *args,
                                   PyObject *kwds)
{
  PyObject *data;
  static char *kwlist[] = { "data", NULL };
  CharacterDataObject *self;

  if (type == &DomletteCharacterData_Type) {
    PyErr_Format(PyExc_TypeError, "cannot create '%.100s' instances",
                 type->tp_name);
    return NULL;
  }

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:CharacterData", kwlist,
                                   &data)) {
    return NULL;
  }

  if ((data = XmlString_ConvertArgument(data, "data", 0)) == NULL)
    return NULL;

  self = CharacterData(type->tp_alloc(type, 0));
  if (self != NULL) {
    self = characterdata_init(self, data);
  }
  Py_DECREF(data);

  return (PyObject *) self;
}

static char characterdata_doc[] = "\
CharacterData(data) -> CharacterData object\n\
\n\
This interface represents a block of XML character data.";

PyTypeObject DomletteCharacterData_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "CharacterData",
  /* tp_basicsize      */ sizeof(CharacterDataObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) characterdata_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) characterdata_repr,
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
  /* tp_doc            */ (char *) characterdata_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) characterdata_methods,
  /* tp_members        */ (PyMemberDef *) characterdata_members,
  /* tp_getset         */ (PyGetSetDef *) characterdata_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) characterdata_new,
  /* tp_free           */ 0,
};

/** Module Interface **************************************************/

int DomletteCharacterData_Init(PyObject *module)
{
  DomletteCharacterData_Type.tp_base = &DomletteNode_Type;
  if (PyType_Ready(&DomletteCharacterData_Type) < 0)
    return -1;

  return 0;
}

void DomletteCharacterData_Fini(void)
{
  PyType_CLEAR(&DomletteCharacterData_Type);
}
