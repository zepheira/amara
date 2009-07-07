#include "attributes.h"

/** Private Interface *************************************************/

typedef struct {
  PyObject_HEAD
  PyObject *values;
  PyObject *qnames;
  Py_ssize_t length;
} AttributesObject;

/* Empty attributes reuse scheme to save calls to malloc and free */
#define MAX_FREE_ATTRS 80
static AttributesObject *free_attrs[MAX_FREE_ATTRS];
static int num_free_attrs = 0;

/** Python Interface **************************************************/

static char attributes_get_value_doc[] =
"getValue(name)\n\
Returns the value of the attribute with the given expanded name.";

static PyObject *
attributes_get_value(AttributesObject *self, PyObject *args)
{
  PyObject *name, *result;

  if (!PyArg_ParseTuple(args, "O:getValue", &name)) return NULL;

  result = PyDict_GetItem(self->values, name);
  if (result == NULL) {
    PyErr_SetObject(PyExc_KeyError, name);
  } else {
    Py_INCREF(result);
  }
  return result;
}

static char attributes_get_qname_doc[] =
"getQNameByName(name)\n\
Returns the qualified name of the attribute with the given expanded name.";

static PyObject *
attributes_get_qname(AttributesObject *self, PyObject *args)
{
  PyObject *name, *result;

  if (!PyArg_ParseTuple(args, "O:getQNameByName", &name)) return NULL;

  result = PyDict_GetItem(self->qnames, name);
  if (result == NULL) {
    PyErr_SetObject(PyExc_KeyError, name);
  } else {
    Py_INCREF(result);
  }
  return result;
}

static char attributes_has_key_doc[] =
"has_key(name)\n\
Returns True if the attribute name is in the list, False otherwise.";

static PyObject *
attributes_has_key(AttributesObject *self, PyObject *args)
{
  PyObject *name;
  PyObject *result;

  if (!PyArg_ParseTuple(args, "O:has_key", &name)) return NULL;

  result = PyMapping_HasKey(self->values, name) ? Py_True : Py_False;
  Py_INCREF(result);
  return result;
}

static char attributes_get_doc[] =
"get(name[, alternative=None])\n\
Return the value associated with attribute name; if it is not available,\n\
then return the alternative.";

static PyObject *
attributes_get(AttributesObject *self, PyObject *args)
{
  PyObject *name, *alternative = Py_None;
  PyObject *result;

  if (!PyArg_ParseTuple(args, "O|O:get", &name, &alternative)) return NULL;

  result = PyDict_GetItem(self->values, name);
  if (result == NULL) {
    result = alternative;
  }
  Py_INCREF(result);
  return result;
}

static char attributes_keys_doc[] =
"keys()\n\
Returns a list of the names of all attribute in the list.";

static PyObject *
attributes_keys(AttributesObject *self, PyObject *args)
{
  if (!PyArg_ParseTuple(args, ":keys")) return NULL;

  return PyDict_Keys(self->values);
}

static char attributes_items_doc[] =
"items()\n\
Return a list of (attribute_name, value) pairs.";

static PyObject *
attributes_items(AttributesObject *self, PyObject *args)
{
  if (!PyArg_ParseTuple(args, ":items")) return NULL;

  return PyDict_Items(self->values);
}

static char attributes_values_doc[] =
"values()\n\
Return a list of all attribute values.";

static PyObject *
attributes_values(AttributesObject *self, PyObject *args)
{
  if (!PyArg_ParseTuple(args, ":values")) return NULL;

  return PyDict_Values(self->values);
}

static PyMethodDef attributes_methods[] = {
  { "getValue", (PyCFunction) attributes_get_value, METH_VARARGS,
    attributes_get_value_doc },
  { "getQNameByName", (PyCFunction) attributes_get_qname, METH_VARARGS,
    attributes_get_qname_doc },
  /* named mapping methods */
  { "has_key", (PyCFunction) attributes_has_key, METH_VARARGS,
    attributes_has_key_doc },
  { "get", (PyCFunction) attributes_get, METH_VARARGS,
    attributes_get_doc },
  { "keys", (PyCFunction) attributes_keys, METH_VARARGS,
    attributes_keys_doc },
  { "values", (PyCFunction) attributes_values, METH_VARARGS,
    attributes_values_doc },
  { "items", (PyCFunction) attributes_items, METH_VARARGS,
    attributes_items_doc },
  { NULL }
};

/** PySequenceMethods **********/

static Py_ssize_t attributes_length(PyObject *self)
{
  return ((AttributesObject *)self)->length;
}

static int attributes_contains(AttributesObject *self, PyObject *key)
{
  return PyDict_GetItem(self->values, key) != NULL;
}

static PySequenceMethods attributes_as_sequence = {
  /* sq_length         */ attributes_length,
  /* sq_concat         */ (binaryfunc) 0,
  /* sq_repeat         */ 0,
  /* sq_item           */ 0,
  /* sq_slice          */ 0,
  /* sq_ass_item       */ 0,
  /* sq_ass_slice      */ 0,
  /* sq_contains       */ (objobjproc) attributes_contains,
  /* sq_inplace_concat */ (binaryfunc) 0,
  /* sq_inplace_repeat */ 0,
};

/** PyMappingMethods **********/

static PyObject *attributes_subscript(AttributesObject *self, PyObject *name)
{
  PyObject *result = PyDict_GetItem(self->values, name);
  if (result == NULL) {
    PyErr_SetObject(PyExc_KeyError, name);
  } else {
    Py_INCREF(result);
  }
  return result;
}

static int attributes_ass_subscript(AttributesObject *self, PyObject *name,
                                    PyObject *value)
{
  int rc;

  if (value == NULL) {
    /* delete item */
    if ((rc = PyDict_DelItem(self->values, name)) == 0) {
      rc = PyDict_DelItem(self->qnames, name);
    }
  } else {
    PyErr_SetString(PyExc_TypeError,
                    "object does not support item assignment");
    rc = -1;
  }

  return rc;
}

static PyMappingMethods attributes_as_mapping = {
  /* mp_length        */ attributes_length,
  /* mp_subscript     */ (binaryfunc) attributes_subscript,
  /* mp_ass_subscript */ (objobjargproc) attributes_ass_subscript,
};

/** Type Methods **************/

static void attributes_dealloc(AttributesObject *self)
{
  PyObject_GC_UnTrack((PyObject *) self);

  self->length = 0;

  if (self->values != NULL) {
    Py_DECREF(self->values);
    self->values = NULL;
  }

  if (self->qnames != NULL) {
    Py_DECREF(self->qnames);
    self->qnames = NULL;
  }

  if (num_free_attrs < MAX_FREE_ATTRS) {
    free_attrs[num_free_attrs++] = self;
  } else {
    PyObject_GC_Del(self);
  }
}

static int attributes_print(AttributesObject *self, FILE *fp, int flags)
{
  return PyObject_Print(self->values, fp, flags);
}

static PyObject *attributes_repr(AttributesObject *self)
{
  return PyObject_Repr(self->values);
}

static int attributes_traverse(AttributesObject *self, visitproc visit,
                               void *arg)
{
  int err;

  if (self->values != NULL) {
    err = visit(self->values, arg);
    if (err) return err;
  }

  if (self->qnames != NULL) {
    err = visit(self->qnames, arg);
    if (err) return err;
  }

  return 0;
}

static int attributes_clear(AttributesObject *self)
{
  Py_CLEAR(self->values);
  Py_CLEAR(self->qnames);
  return 0;
}

static PyObject *attributes_iter(AttributesObject *self)
{
  return PyObject_GetIter(self->values);
}

static char attributes_doc[] =
"Interface for a list of XML attributes.\n\
\n\
Contains a list of XML attributes, accessible by name.";

static PyTypeObject Attributes_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Expat_MODULE_NAME "." "Attributes",
  /* tp_basicsize      */ sizeof(AttributesObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) attributes_dealloc,
  /* tp_print          */ (printfunc) attributes_print,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) attributes_repr,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) &attributes_as_sequence,
  /* tp_as_mapping     */ (PyMappingMethods *) &attributes_as_mapping,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) 0,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
  /* tp_doc            */ (char *) attributes_doc,
  /* tp_traverse       */ (traverseproc) attributes_traverse,
  /* tp_clear          */ (inquiry) attributes_clear,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) attributes_iter,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) attributes_methods,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) 0,
  /* tp_free           */ 0,
};

/** Public Interface **************************************************/

PyObject *
Attributes_New(ExpatAttribute atts[], Py_ssize_t length)
{
  PyObject *values, *qnames, *expandedName;
  AttributesObject *self;
  register Py_ssize_t i;

  if (num_free_attrs) {
    num_free_attrs--;
    self = free_attrs[num_free_attrs];
    _Py_NewReference((PyObject *) self);
  } else {
    self = PyObject_GC_New(AttributesObject, &Attributes_Type);
    if (self == NULL)
      return NULL;
  }

  values = self->values = PyDict_New();
  qnames = self->qnames = PyDict_New();
  if (values == NULL || qnames == NULL) {
    Py_XDECREF(self->values);
    Py_XDECREF(self->qnames);
    Py_DECREF(self);
    return NULL;
  }

  PyObject_GC_Track(self);

  for (i = 0; i < length; i++) {
    /* create the expanded-name 'key' of (namespaceURI, localName) */
    expandedName = PyTuple_Pack(2, atts[i].namespaceURI, atts[i].localName);
    if (expandedName == NULL ||
        PyDict_SetItem(values, expandedName, atts[i].value) < 0 ||
        PyDict_SetItem(qnames, expandedName, atts[i].qualifiedName) < 0) {
      Py_XDECREF(expandedName);
      Py_DECREF(self);
      return NULL;
    }
    Py_DECREF(expandedName);
  }
  self->length = length;

  return (PyObject *)self;
}

int
Attributes_SetItem(PyObject *attributes,
                   PyObject *namespaceURI, PyObject *localName,
                   PyObject *qualifiedName, PyObject *value)
{
  AttributesObject *self = (AttributesObject *)attributes;
  PyObject *expandedName;
  int has_key;

  expandedName = PyTuple_Pack(2, namespaceURI, localName);
  if (expandedName == NULL)
    return -1;

  has_key = PyDict_GetItem(self->values, expandedName) != NULL;

  if (PyDict_SetItem(self->values, expandedName, value) < 0) {
    Py_DECREF(expandedName);
    return -1;
  }

  if (PyDict_SetItem(self->qnames, expandedName, qualifiedName) < 0) {
    PyDict_DelItem(self->values, expandedName);
    Py_DECREF(expandedName);
    return -1;
  }

  if (has_key)
    self->length++;

  return 0;
}

/** Module Interface **************************************************/

int _Expat_Attributes_Init(PyObject *module)
{
  return PyModule_AddType(module, &Attributes_Type);
}

void _Expat_Attributes_Fini(void)
{
  PyType_CLEAR(&Attributes_Type);
}
