#include "expat_interface.h"

/** Private Interface *************************************************/

PyObject *uri_resolver;

/** Python Interface **************************************************/

static char inputsource_doc[] =
"InputSource(byteStream, baseURI[, encoding]) -> InputSource object";

static PyObject *
inputsource_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = { "byteStream", "baseURI", "encoding", NULL };
  PyObject *byte_stream, *base_uri, *encoding = Py_None;
  InputSourceObject *newobj;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|O:InputSource", kwlist,
                                   &byte_stream, &base_uri, &encoding))
    return NULL;

  base_uri = PyObject_Unicode(base_uri);
  if (base_uri == NULL)
    return NULL;
  if (encoding == Py_None) {
    Py_INCREF(encoding);
  } else {
    encoding = PyObject_Unicode(encoding);
    if (encoding == NULL) {
      Py_DECREF(base_uri);
      return NULL;
    }
  }

  newobj = (InputSourceObject *)type->tp_alloc(type, 0);
  if (newobj != NULL) {
    Py_INCREF(byte_stream);
    newobj->byte_stream = byte_stream;
    newobj->base_uri = base_uri;
    newobj->encoding = encoding;
  } else {
    Py_DECREF(base_uri);
    Py_DECREF(encoding);
  }
  return (PyObject *)newobj;
}

static void
inputsource_dealloc(InputSourceObject *self)
{
  PyObject_GC_UnTrack((PyObject *)self);
  Py_XDECREF(self->byte_stream);
  Py_XDECREF(self->char_stream);
  Py_XDECREF(self->string_data);
  Py_XDECREF(self->system_id);
  Py_XDECREF(self->public_id);
  Py_XDECREF(self->base_uri);
  Py_XDECREF(self->encoding);
  ((PyObject *)self)->ob_type->tp_free((PyObject *)self);
}

static int
inputsource_traverse(InputSourceObject *self, visitproc visit, void *arg)
{
  Py_VISIT(self->byte_stream);
  Py_VISIT(self->char_stream);
  Py_VISIT(self->string_data);
  Py_VISIT(self->system_id);
  Py_VISIT(self->public_id);
  Py_VISIT(self->base_uri);
  Py_VISIT(self->encoding);
  return 0;
}

static int
inputsource_clear(InputSourceObject *self)
{
  Py_CLEAR(self->byte_stream);
  Py_CLEAR(self->char_stream);
  Py_CLEAR(self->string_data);
  Py_CLEAR(self->system_id);
  Py_CLEAR(self->public_id);
  Py_CLEAR(self->base_uri);
  Py_CLEAR(self->encoding);
  return 0;
}

/** InputSource Methods **/

Py_LOCAL_INLINE(PyObject *)
resolve_uri(InputSourceObject *self, PyObject *uri)
{
  PyObject *byte_stream;

  uri = PyObject_CallMethod(uri_resolver, "normalize", "OO", uri,
                            self->base_uri);
  if (uri == NULL)
    return NULL;

  byte_stream = PyObject_CallMethod(uri_resolver, "resolve", "O", uri);
  if (byte_stream == NULL) {
    Py_DECREF(uri);
    return NULL;
  }

  return PyObject_CallFunction((PyObject *)self->ob_type, "NN",
                               byte_stream, uri);
}

static PyObject *
inputsource_resolve(InputSourceObject *self, PyObject *args)
{
  PyObject *href, *base=Py_None, *hint=Py_None;

  if (!PyArg_ParseTuple(args, "O|OO:resolve", &href, &base, &hint))
    return NULL;

  return resolve_uri(self, href);
}

static PyObject *
inputsource_resolve_entity(InputSourceObject *self, PyObject *args)
{
  PyObject *publicId, *systemId;

  if (!PyArg_ParseTuple(args, "OO:resolveEntity", &publicId, &systemId))
    return NULL;

  return resolve_uri(self, systemId);
}

static PyMethodDef inputsource_methods[] = {
  { "resolve", (PyCFunction)inputsource_resolve, METH_VARARGS },
  { "resolveEntity", (PyCFunction)inputsource_resolve_entity, METH_VARARGS },
  { NULL }
};

/** InputSource Members **/

static PyMemberDef inputsource_members[] = {
  { "stream", T_OBJECT, offsetof(InputSourceObject, byte_stream), RO },
  { "stringData", T_OBJECT, offsetof(InputSourceObject, string_data), RO },
  { "systemId", T_OBJECT, offsetof(InputSourceObject, system_id), RO },
  { "publicId", T_OBJECT, offsetof(InputSourceObject, public_id), RO },
  { "uri", T_OBJECT, offsetof(InputSourceObject, base_uri), RO },
  { "encoding", T_OBJECT, offsetof(InputSourceObject, encoding), RO },
  { NULL }
};

PyTypeObject InputSource_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Expat_MODULE_NAME "." "InputSource",
  /* tp_basicsize      */ sizeof(InputSourceObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) inputsource_dealloc,
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
  /* tp_doc            */ (char *) inputsource_doc,
  /* tp_traverse       */ (traverseproc) inputsource_traverse,
  /* tp_clear          */ (inquiry) inputsource_clear,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) inputsource_methods,
  /* tp_members        */ (PyMemberDef *) inputsource_members,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) inputsource_new,
  /* tp_free           */ 0,
};

/** Module Interface **************************************************/

int _Expat_InputSource_Init(PyObject *module)
{
  PyObject *import;

  if (PyModule_AddType(module, &InputSource_Type) < 0) return -1;
  import = PyImport_ImportModule("amara.lib.iri");
  if (import == NULL) return -1;
  uri_resolver = PyObject_GetAttrString(import, "DEFAULT_RESOLVER");
  if (uri_resolver == NULL) {
    Py_DECREF(import);
    return -1;
  }
  Py_DECREF(import);

  return 0;
}

void _Expat_InputSource_Fini(void)
{
  Py_DECREF(uri_resolver);

  PyType_CLEAR(&InputSource_Type);
}
