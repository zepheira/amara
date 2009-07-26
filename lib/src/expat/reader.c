#include "expat_interface.h"

/** Private Interface *************************************************/

typedef struct {
  PyObject_HEAD
  ExpatReader *reader;
  PyObject *filters;
} ReaderObject;

/** Python Interface **************************************************/

static char reader_doc[] =
"Reader([filters]) -> Reader object\n\
\n\
Interface for reading an XML document using callbacks.";

static PyObject *
reader_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = { "filters", NULL };
  PyObject *seq = NULL;
  ExpatFilter **filters;
  Py_ssize_t nfilters, i;
  ReaderObject *newobj;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O:Reader", kwlist,
                                   &seq))
    return NULL;

  if (seq == NULL) {
    filters = NULL;
    nfilters = 0;
  }
  else {
    seq = PySequence_Tuple(seq);
    if (seq == NULL)
      return NULL;
    nfilters = PyTuple_GET_SIZE(seq);
    filters = PyMem_New(ExpatFilter *, nfilters);
    if (filters == NULL) {
      Py_DECREF(seq);
      return NULL;
    }
    for (i = 0; i < nfilters; i++) {
      PyObject *filter = PyTuple_GET_ITEM(seq, i);
      if (!Filter_Check(filter)) {
        PyErr_SetString(PyExc_TypeError, "expected sequence of Filters");
        Py_DECREF(seq);
        PyMem_Del(filters);
        return NULL;
      }
      filters[i] = Filter_GET_FILTER(filter);
    }
  }
  newobj = (ReaderObject *)type->tp_alloc(type, 0);
  if (newobj != NULL) {
    newobj->filters = seq;
    newobj->reader = ExpatReader_New(filters, nfilters);
    if (newobj->reader == NULL) {
      Py_CLEAR(newobj);
      goto finally;
    }
  } else {
    Py_DECREF(seq);
  }
finally:
  if (filters) PyMem_Del(filters);
  return (PyObject *)newobj;
}

static void
reader_dealloc(ReaderObject *self)
{
  PyObject_GC_UnTrack((PyObject *)self);

  if (self->reader) {
    ExpatReader_Del(self->reader);
    self->reader = NULL;
  }
  Py_CLEAR(self->filters);

  ((PyObject *)self)->ob_type->tp_free((PyObject *)self);
}

static int
reader_traverse(ReaderObject *self, visitproc visit, void *arg)
{
  return 0;
}

static int
reader_clear(ReaderObject *self)
{
  return 0;
}

/** Reader Methods **/

static char reader_parse_doc[] =
"R.parse(source) -> None";

static PyObject *
reader_parse(ReaderObject *self, PyObject *args)
{
  PyObject *source;
  ExpatStatus status;

  if (!PyArg_ParseTuple(args, "O:parse", &source))
    return NULL;

  status = ExpatReader_Parse(self->reader, source);
  if (status == EXPAT_STATUS_ERROR)
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char reader_parse_entity_doc[] =
"R.parseEntity(source[, namespaces]) -> None";

static PyObject *
reader_parse_entity(ReaderObject *self, PyObject *args)
{
  PyObject *source, *namespaces=NULL;
  ExpatStatus status;

  if (!PyArg_ParseTuple(args, "O|O:parseEntity", &source, &namespaces))
    return NULL;

  status = ExpatReader_ParseEntity(self->reader, source, namespaces);
  if (status == EXPAT_STATUS_ERROR)
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyMethodDef reader_methods[] = {
  { "parse", (PyCFunction)reader_parse, METH_VARARGS,
     reader_parse_doc },
  { "parseEntity", (PyCFunction)reader_parse_entity, METH_VARARGS,
    reader_parse_entity_doc },
  { NULL }
};

/** Reader Members **/

static PyMemberDef reader_members[] = {
  { NULL }
};

/** Reader Descriptors **/

static PyObject *
reader_get_validation(ReaderObject *self, void *arg)
{
  return PyBool_FromLong(ExpatReader_GetValidation(self->reader));
}

static int
reader_set_validation(ReaderObject *self, PyObject *v, void *arg)
{
  int validation = PyObject_IsTrue(v);
  if (validation < 0)
    return -1;
  ExpatReader_SetValidation(self->reader, validation);
  return 0;
}

static PyObject *
reader_get_param_entity(ReaderObject *self, void *arg)
{
  return PyBool_FromLong(ExpatReader_GetParamEntityParsing(self->reader));
}

static int
reader_set_param_entity(ReaderObject *self, PyObject *v, void *arg)
{
  int parsing = PyObject_IsTrue(v);
  if (parsing < 0)
    return -1;
  ExpatReader_SetParamEntityParsing(self->reader, parsing);
  return 0;
}

static PyObject *
reader_get_stripping(ReaderObject *self, void *arg)
{
  return ExpatReader_GetWhitespaceStripping(self->reader);
}

static int
reader_set_stripping(ReaderObject *self, PyObject *v, void *arg)
{
  ExpatStatus status;

  status = ExpatReader_SetWhitespaceStripping(self->reader, v);
  if (status == EXPAT_STATUS_ERROR)
    return -1;
  return 0;
}

static PyGetSetDef reader_getset[] = {
  { "validation",
    (getter)reader_get_validation, (setter)reader_set_validation },
  { "external_parameter_entities",
    (getter)reader_get_param_entity, (setter)reader_set_param_entity },
  { "whitespace_stripping",
    (getter)reader_get_stripping, (setter)reader_set_stripping },
  { NULL }
};

static PyTypeObject Reader_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Expat_MODULE_NAME "." "Reader",
  /* tp_basicsize      */ sizeof(ReaderObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) reader_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) 0,
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
                           Py_TPFLAGS_BASETYPE | /* allow subclassing */
                           Py_TPFLAGS_HAVE_GC |  /* support cyclic GC */
                           0),
  /* tp_doc            */ (char *) reader_doc,
  /* tp_traverse       */ (traverseproc) reader_traverse,
  /* tp_clear          */ (inquiry) reader_clear,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) reader_methods,
  /* tp_members        */ (PyMemberDef *) reader_members,
  /* tp_getset         */ (PyGetSetDef *) reader_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) reader_new,
  /* tp_free           */ 0,
};

/** Public Interface **************************************************/


/** Module Interface **************************************************/

int _Expat_Reader_Init(PyObject *module)
{
  return PyModule_AddType(module, &Reader_Type);
}

void _Expat_Reader_Fini(void)
{
  PyType_CLEAR(&Reader_Type);
}
