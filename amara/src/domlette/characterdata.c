#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

/* The maximum number of characters of the nodeValue to use when
   creating the repr string.
*/
#define CHARACTERDATA_REPR_LIMIT 20

Py_LOCAL_INLINE(int)
characterdata_init(CharacterDataObject *self, PyObject *data)
{
  if ((self == NULL || !CharacterData_Check(self)) ||
      (data == NULL || !XmlString_Check(data))) {
    PyErr_BadInternalCall();
    return -1;
  }

  Py_INCREF(data);
  self->nodeValue = data;

  return 0;
}

/** Public C API ******************************************************/

CharacterDataObject *_CharacterData_New(PyTypeObject *type, PyObject *data)
{
  CharacterDataObject *self;

  self = Node_New(CharacterDataObject, type);
  if (self != NULL) {
    if (characterdata_init(self, data) < 0) {
      Node_Del(self);
      return NULL;
    }
  }

  PyObject_GC_Track(self);

  return self;
}

CharacterDataObject *_CharacterData_CloneNode(PyTypeObject *type,
                                              PyObject *node, int deep)
{
  PyObject *nodeValue;
  CharacterDataObject *newNode;

  nodeValue = PyObject_GetAttrString(node, "nodeValue");
  nodeValue = XmlString_FromObjectInPlace(nodeValue);
  if (nodeValue == NULL) return NULL;

  newNode = _CharacterData_New(type, nodeValue);
  Py_DECREF(nodeValue);

  return newNode;
}

PyObject *CharacterData_SubstringData(CharacterDataObject *self,
                                      Py_ssize_t index, Py_ssize_t count)
{
  PyObject *newValue;

  newValue = PyUnicode_FromUnicode(NULL, count);
  if (newValue) {
    Py_UNICODE_COPY(PyUnicode_AS_UNICODE(newValue),
                    PyUnicode_AS_UNICODE(self->nodeValue) + index,
                    count);
  }
  return newValue;
}

int CharacterData_AppendData(CharacterDataObject *self, PyObject *arg)
{
  PyObject *oldValue = self->nodeValue;
  PyObject *newValue;

  if (arg == NULL || !PyUnicode_Check(arg)) {
    PyErr_BadInternalCall();
    return -1;
  }

  newValue = PyUnicode_FromUnicode(NULL,
                                   PyUnicode_GET_SIZE(oldValue) + \
                                   PyUnicode_GET_SIZE(arg));
  if (newValue == NULL) return -1;

  Py_UNICODE_COPY(PyUnicode_AS_UNICODE(newValue),
                  PyUnicode_AS_UNICODE(oldValue),
                  PyUnicode_GET_SIZE(oldValue));
  Py_UNICODE_COPY(PyUnicode_AS_UNICODE(newValue) + PyUnicode_GET_SIZE(oldValue),
                  PyUnicode_AS_UNICODE(arg),
                  PyUnicode_GET_SIZE(arg));

  Py_DECREF(oldValue);
  self->nodeValue = newValue;
  return 0;
}

int CharacterData_InsertData(CharacterDataObject *self, Py_ssize_t offset,
                             PyObject *arg)
{
  PyObject *oldValue = self->nodeValue;
  PyObject *newValue;

  if (arg == NULL || !PyUnicode_Check(arg)) {
    PyErr_BadInternalCall();
    return -1;
  }

  newValue = PyUnicode_FromUnicode(NULL,
                                   PyUnicode_GET_SIZE(oldValue) + \
                                   PyUnicode_GET_SIZE(arg));
  if (newValue == NULL) return -1;

  Py_UNICODE_COPY(PyUnicode_AS_UNICODE(newValue),
                  PyUnicode_AS_UNICODE(oldValue),
                  offset);
  Py_UNICODE_COPY(PyUnicode_AS_UNICODE(newValue) + offset,
                  PyUnicode_AS_UNICODE(arg),
                  PyUnicode_GET_SIZE(arg));
  Py_UNICODE_COPY(PyUnicode_AS_UNICODE(newValue) + offset + PyUnicode_GET_SIZE(arg),
                  PyUnicode_AS_UNICODE(oldValue) + offset,
                  PyUnicode_GET_SIZE(oldValue) - offset);

  Py_DECREF(oldValue);
  self->nodeValue = newValue;
  return 0;
}

int CharacterData_DeleteData(CharacterDataObject *self, Py_ssize_t offset,
                             Py_ssize_t count)
{
  PyObject *oldValue = self->nodeValue;
  PyObject *newValue;

  newValue = PyUnicode_FromUnicode(NULL, PyUnicode_GET_SIZE(oldValue) - count);
  if (newValue == NULL) return -1;

  Py_UNICODE_COPY(PyUnicode_AS_UNICODE(newValue),
                  PyUnicode_AS_UNICODE(oldValue),
                  offset);
  Py_UNICODE_COPY(PyUnicode_AS_UNICODE(newValue) + offset,
                  PyUnicode_AS_UNICODE(oldValue) + offset + count,
                  PyUnicode_GET_SIZE(oldValue) - offset - count);

  Py_DECREF(oldValue);
  self->nodeValue = newValue;
  return 0;
}

int CharacterData_ReplaceData(CharacterDataObject *self, Py_ssize_t offset,
                              Py_ssize_t count, PyObject *arg)
{
  PyObject *oldValue = self->nodeValue;
  PyObject *newValue;

  if (arg == NULL || !PyUnicode_Check(arg)) {
    PyErr_BadInternalCall();
    return -1;
  }

  newValue = PyUnicode_FromUnicode(NULL,
                                   PyUnicode_GET_SIZE(oldValue) - count + \
                                   PyUnicode_GET_SIZE(arg));
  if (newValue == NULL) return -1;

  Py_UNICODE_COPY(PyUnicode_AS_UNICODE(newValue),
                  PyUnicode_AS_UNICODE(oldValue),
                  offset);
  Py_UNICODE_COPY(PyUnicode_AS_UNICODE(newValue) + offset,
                  PyUnicode_AS_UNICODE(arg),
                  PyUnicode_GET_SIZE(arg));
  Py_UNICODE_COPY(PyUnicode_AS_UNICODE(newValue) + offset + PyUnicode_GET_SIZE(arg),
                  PyUnicode_AS_UNICODE(oldValue) + offset + count,
                  PyUnicode_GET_SIZE(oldValue) - offset - count);

  Py_DECREF(oldValue);
  self->nodeValue = newValue;
  return 0;
}

/** Python Methods ****************************************************/

static char substring_doc[] = "\
Extracts a range of data from the node.";

static PyObject *characterdata_substring(PyObject *self, PyObject *args)
{
  Py_ssize_t offset, count;

  if (!PyArg_ParseTuple(args, "nn:substringData",
                        &offset, &count))
    return NULL;

  return CharacterData_SubstringData(CharacterData(self), offset, count);
}

static char append_doc[] = "\
Append the string to the end of the character data of the node.";

static PyObject *characterdata_append(PyObject *self, PyObject *args)
{
  PyObject *data;

  if (!PyArg_ParseTuple(args, "O:appendData", &data))
    return NULL;

  if ((data = XmlString_ConvertArgument(data, "data", 0)) == NULL)
    return NULL;

  if (CharacterData_AppendData(CharacterData(self), data) < 0) {
    Py_DECREF(data);
    return NULL;
  }
  Py_DECREF(data);

  Py_INCREF(Py_None);
  return Py_None;
}

static char insert_doc[] = "\
Insert a string at the specified unicode unit offset.";

static PyObject *characterdata_insert(PyObject *self, PyObject *args)
{
  Py_ssize_t offset;
  PyObject *data;

  if (!PyArg_ParseTuple(args, "nO:insert_data", &offset, &data))
    return NULL;

  if ((data = XmlString_ConvertArgument(data, "data", 0)) == NULL)
    return NULL;

  if (CharacterData_InsertData(CharacterData(self), offset, data) < 0) {
    Py_DECREF(data);
    return NULL;
  }

  Py_DECREF(data);
  Py_INCREF(Py_None);
  return Py_None;
}

static char delete_doc[] = "\
Remove a range of unicode units from the node.";

static PyObject *characterdata_delete(PyObject *self, PyObject *args)
{
  Py_ssize_t offset, count;

  if (!PyArg_ParseTuple(args, "nn:delete_data",
                        &offset, &count))
    return NULL;

  if (CharacterData_DeleteData(CharacterData(self), offset, count) < 0)
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char replace_doc[] = "\
Replace the characters starting at the specified unicode unit offset with\n\
the specified string.";

static PyObject *characterdata_replace(PyObject *self, PyObject *args)
{
  Py_ssize_t offset, count;
  PyObject *data;

  if (!PyArg_ParseTuple(args, "nnO:replaceData",
                        &offset, &count, &data))
    return NULL;

  if ((data = XmlString_ConvertArgument(data, "data", 0)) == NULL)
    return NULL;

  if (CharacterData_DeleteData(CharacterData(self), offset, count) < 0) {
    Py_DECREF(data);
    return NULL;
  }

  Py_DECREF(data);
  Py_INCREF(Py_None);
  return Py_None;
}

static PyMethodDef characterdata_methods[] = {
  {"xml_substring", characterdata_substring, METH_VARARGS, substring_doc },
  {"xml_append",    characterdata_append,    METH_VARARGS, append_doc },
  {"xml_insert",    characterdata_insert,    METH_VARARGS, insert_doc },
  {"xml_delete",    characterdata_delete,    METH_VARARGS, delete_doc },
  {"xml_replace",   characterdata_replace,   METH_VARARGS, replace_doc },
  { NULL }
};

/** Python Members *****************************************************/

static PyMemberDef characterdata_members[] = {
  { NULL }
};

/** Python Computed Members ********************************************/

static PyObject *get_data(CharacterDataObject *self, void *arg)
{
  Py_INCREF(self->nodeValue);
  return self->nodeValue;
}

static int set_data(CharacterDataObject *self, PyObject *v, void *arg)
{
  PyObject *nodeValue = XmlString_ConvertArgument(v, "xml_data", 0);
  if (nodeValue == NULL) return -1;

  Py_DECREF(self->nodeValue);
  self->nodeValue = nodeValue;
  return 0;
}

static PyObject *get_length(CharacterDataObject *self, void *arg)
{
#if PY_VERSION_HEX < 0x02050000
    return PyInt_FromLong(PyUnicode_GET_SIZE(self->nodeValue));
#else
    return PyInt_FromSsize_t(PyUnicode_GET_SIZE(self->nodeValue));
#endif
}

static PyGetSetDef characterdata_getset[] = {
  { "xml_data",      (getter)get_data,   (setter)set_data},
  { "xml_length",    (getter)get_length },
  { NULL }
};

/** Type Object ********************************************************/

static void characterdata_dealloc(CharacterDataObject *self)
{
  PyObject_GC_UnTrack((PyObject *) self);

  Py_XDECREF(self->nodeValue);
  self->nodeValue = NULL;
  Node_Del(self);
}

static PyObject *characterdata_repr(CharacterDataObject *self)
{
  PyObject *obj, *repr, *name;

  if (PyUnicode_GET_SIZE(self->nodeValue) > CHARACTERDATA_REPR_LIMIT) {
    Py_UNICODE *src, *dst;

    obj = PyUnicode_FromUnicode(NULL, CHARACTERDATA_REPR_LIMIT + 3);
    if (obj == NULL) {
      return NULL;
    }
    /* copy the first part of the node value */
    src = PyUnicode_AS_UNICODE(self->nodeValue);
    dst = PyUnicode_AS_UNICODE(obj);
    Py_UNICODE_COPY(dst, src, (CHARACTERDATA_REPR_LIMIT / 2));
    dst += (CHARACTERDATA_REPR_LIMIT / 2);

    /* add the ellipsis */
    *dst++ = '.';
    *dst++ = '.';
    *dst++ = '.';

    /* copy the last part of the node value */
    src += PyUnicode_GET_SIZE(self->nodeValue);
    src -= (CHARACTERDATA_REPR_LIMIT / 2);
    Py_UNICODE_COPY(dst, src, (CHARACTERDATA_REPR_LIMIT / 2));
  } else {
    obj = self->nodeValue;
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

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:cdata", kwlist,
                                   &data)) {
    return NULL;
  }

  if ((data = XmlString_ConvertArgument(data, "cdata", 0)) == NULL)
    return NULL;

  self = CharacterData(type->tp_alloc(type, 0));
  if (self != NULL) {
    _Node_INIT(self);
    if (characterdata_init(self, data) < 0) {
      Py_DECREF(self);
      self = NULL;
    }
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

  Py_INCREF(&DomletteCharacterData_Type);
  return PyModule_AddObject(module, "CharacterData",
                            (PyObject*) &DomletteCharacterData_Type);
}

void DomletteCharacterData_Fini(void)
{
  PyType_CLEAR(&DomletteCharacterData_Type);
}
