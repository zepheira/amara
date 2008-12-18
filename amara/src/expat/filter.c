#include "expat_interface.h"
#include "attributes.h"

/** Private Interface *************************************************/

enum HandlerTypes {
  /* ContentHandler */
  Handler_StartFilter,
  Handler_EndFilter,
  Handler_StartDocument,
  Handler_EndDocument,
  Handler_StartNamespace,
  Handler_EndNamespace,
  Handler_StartElement,
  Handler_EndElement,
  Handler_Characters,
  Handler_Whitespace,
  Handler_ProcessingInstruction,
  Handler_SkippedEntity,

  /* DTDHandler */
  Handler_NotationDecl,
  Handler_UnparsedEntityDecl,

  /* EntityResolver */
  Handler_ResolveEntity,

  /* ErrorHandler */
  Handler_Warning,
  Handler_Error,
  Handler_FatalError,

  /* LexicalHandler */
  Handler_StartDTD,
  Handler_EndDTD,
  Handler_StartCDATA,
  Handler_EndCDATA,
  Handler_Comment,

  /* DeclHandler */
  Handler_ElementDecl,
  Handler_AttributeDecl,
  Handler_InternalEntityDecl,
  Handler_ExternalEntityDecl,

  TotalHandlers
};

/* Cached PyCodeObjects for frames */
static PyCodeObject *tb_codes[TotalHandlers];

/* no-op function for override checks */
static PyObject *filter_noop(PyObject *self, PyObject *args)
{
  Py_RETURN_NONE;
}

#ifndef PyDict_GET_SIZE
#define PyDict_GET_SIZE(ma) (((PyDictObject *)(ma))->ma_used)
#endif

#ifndef PyDict_CLEAR
#define PyDict_CLEAR(ma) if (PyDict_GET_SIZE(ma) > 0) PyDict_Clear(ma)
#endif

/** Reader Callbacks **************************************************/

#define getcode(slot) _getcode(Handler_##slot, #slot, __LINE__)
Py_LOCAL_INLINE(PyCodeObject *)
_getcode(enum HandlerTypes slot, char *name, int lineno)
{
  if (tb_codes[slot] == NULL)
    tb_codes[slot] = _PyCode_Here(name, __FILE__, lineno);
  return tb_codes[slot];
}

static ExpatStatus
filter_StartFilter(void *arg, ExpatName *name)
{
  PyObject *self = (PyObject *)arg;
  PyObject *handler, *args, *result;

  handler = PyObject_GetAttrString(self, "start_filter");
  if (handler == NULL)
    return EXPAT_STATUS_ERROR;

  /* if the method was not overriden, save some cycles and just return */
  if (PyCFunction_Check(handler) &&
      PyCFunction_GET_FUNCTION(handler) == filter_noop) {
    Py_DECREF(handler);
    return EXPAT_STATUS_OK;
  }

  args = Py_BuildValue("(OO)O", name->namespaceURI, name->localName,
                       name->qualifiedName);
  if (args == NULL) {
    Py_DECREF(handler);
    return EXPAT_STATUS_ERROR;
  }
  result = PyTrace_CallObject(getcode(StartFilter), handler, args);
  Py_DECREF(args);
  if (result == NULL) {
    Py_DECREF(handler);
    return EXPAT_STATUS_ERROR;
  }
  Py_DECREF(result);
  Py_DECREF(handler);
  return EXPAT_STATUS_OK;
}

static ExpatStatus
filter_EndFilter(void *arg, ExpatName *name)
{
  PyObject *self = (PyObject *)arg;
  PyObject *handler, *args, *result;

  handler = PyObject_GetAttrString(self, "end_filter");
  if (handler == NULL)
    return EXPAT_STATUS_ERROR;

  /* if the method was not overriden, save some cycles and just return */
  if (PyCFunction_Check(handler) &&
      PyCFunction_GET_FUNCTION(handler) == filter_noop) {
    Py_DECREF(handler);
    return EXPAT_STATUS_OK;
  }

  args = Py_BuildValue("(OO)O", name->namespaceURI, name->localName,
                       name->qualifiedName);
  if (args == NULL) {
    Py_DECREF(handler);
    return EXPAT_STATUS_ERROR;
  }
  result = PyTrace_CallObject(getcode(EndFilter), handler, args);
  Py_DECREF(args);
  if (result == NULL) {
    Py_DECREF(handler);
    return EXPAT_STATUS_ERROR;
  }
  Py_DECREF(result);
  Py_DECREF(handler);
  return EXPAT_STATUS_OK;
}

static ExpatStatus
filter_StartDocument(void *arg)
{
  PyObject *self = (PyObject *)arg;
  PyObject *handler, *args, *result;

  handler = PyObject_GetAttrString(self, "start_document");
  if (handler == NULL)
    return EXPAT_STATUS_ERROR;

  /* if the method was not overriden, save some cycles and just return */
  if (PyCFunction_Check(handler) &&
      PyCFunction_GET_FUNCTION(handler) == filter_noop) {
    Py_DECREF(handler);
    return EXPAT_STATUS_OK;
  }

  args = PyTuple_New(0);
  if (args == NULL) {
    Py_DECREF(handler);
    return EXPAT_STATUS_ERROR;
  }
  result = PyTrace_CallObject(getcode(StartDocument), handler, args);
  Py_DECREF(args);
  if (result == NULL) {
    Py_DECREF(handler);
    return EXPAT_STATUS_ERROR;
  }
  Py_DECREF(result);
  Py_DECREF(handler);
  return EXPAT_STATUS_OK;
}

static ExpatStatus
filter_EndDocument(void *arg)
{
  PyObject *self = (PyObject *)arg;
  PyObject *handler, *args, *result;

  handler = PyObject_GetAttrString(self, "end_document");
  if (handler == NULL)
    return EXPAT_STATUS_ERROR;

  /* if the method was not overriden, save some cycles and just return */
  if (PyCFunction_Check(handler) &&
      PyCFunction_GET_FUNCTION(handler) == filter_noop) {
    Py_DECREF(handler);
    return EXPAT_STATUS_OK;
  }

  args = PyTuple_New(0);
  if (args == NULL) {
    Py_DECREF(handler);
    return EXPAT_STATUS_ERROR;
  }
  result = PyTrace_CallObject(getcode(EndDocument), handler, args);
  Py_DECREF(args);
  if (result == NULL) {
    Py_DECREF(handler);
    return EXPAT_STATUS_ERROR;
  }
  Py_DECREF(result);
  Py_DECREF(handler);
  return EXPAT_STATUS_OK;
}

static ExpatStatus
filter_StartElement(void *arg, ExpatName *name, ExpatAttribute atts[],
                    size_t natts)
{
  FilterObject *self = (FilterObject *)arg;
  PyObject *handler, *args, *result;

  handler = PyObject_GetAttrString((PyObject *)self, "start_element");
  if (handler == NULL)
    return EXPAT_STATUS_ERROR;

  /* if the method was not overriden, save some cycles and just return */
  if (PyCFunction_Check(handler) &&
      PyCFunction_GET_FUNCTION(handler) == filter_noop) {
    Py_DECREF(handler);
    return EXPAT_STATUS_OK;
  }

  args = Py_BuildValue("(OO)OON", name->namespaceURI, name->localName,
                       name->qualifiedName, self->new_namespaces,
                       Attributes_New(atts, natts));
  if (args == NULL) {
    PyDict_CLEAR(self->new_namespaces);
    Py_DECREF(handler);
    return EXPAT_STATUS_ERROR;
  }
  result = PyTrace_CallObject(getcode(StartElement), handler, args);
  PyDict_CLEAR(self->new_namespaces);
  Py_DECREF(args);
  Py_DECREF(handler);
  if (result == NULL)
    return EXPAT_STATUS_ERROR;
  Py_DECREF(result);
  return EXPAT_STATUS_OK;
}

static ExpatStatus
filter_EndElement(void *arg, ExpatName *name)
{
  PyObject *self = (PyObject *)arg;
  PyObject *handler, *args, *result;

  handler = PyObject_GetAttrString(self, "end_element");
  if (handler == NULL)
    return EXPAT_STATUS_ERROR;

  /* if the method was not overriden, save some cycles and just return */
  if (PyCFunction_Check(handler) &&
      PyCFunction_GET_FUNCTION(handler) == filter_noop) {
    Py_DECREF(handler);
    return EXPAT_STATUS_OK;
  }

  args = Py_BuildValue("(OO)O", name->namespaceURI, name->localName,
                       name->qualifiedName);
  if (args == NULL) {
    Py_DECREF(handler);
    return EXPAT_STATUS_ERROR;
  }
  result = PyTrace_CallObject(getcode(EndElement), handler, args);
  Py_DECREF(args);
  if (result == NULL) {
    Py_DECREF(handler);
    return EXPAT_STATUS_ERROR;
  }
  Py_DECREF(result);
  Py_DECREF(handler);
  return EXPAT_STATUS_OK;
}

static ExpatStatus
filter_Attribute(void *arg, ExpatName *name, PyObject *value, AttributeType type)
{
  return EXPAT_STATUS_OK;
}

static ExpatStatus
filter_Characters(void *arg, PyObject *data)
{
  PyObject *self = (PyObject *)arg;
  PyObject *handler, *args, *result;

  handler = PyObject_GetAttrString(self, "characters");
  if (handler == NULL)
    return EXPAT_STATUS_ERROR;

  /* if the method was not overriden, save some cycles and just return */
  if (PyCFunction_Check(handler) &&
      PyCFunction_GET_FUNCTION(handler) == filter_noop) {
    Py_DECREF(handler);
    return EXPAT_STATUS_OK;
  }

  args = PyTuple_Pack(1, data);
  if (args == NULL) {
    Py_DECREF(handler);
    return EXPAT_STATUS_ERROR;
  }
  result = PyTrace_CallObject(getcode(Characters), handler, args);
  Py_DECREF(args);
  if (result == NULL) {
    Py_DECREF(handler);
    return EXPAT_STATUS_ERROR;
  }
  Py_DECREF(result);
  Py_DECREF(handler);
  return EXPAT_STATUS_OK;
}

static ExpatStatus
filter_Whitespace(void *arg, PyObject *data)
{
  PyObject *self = (PyObject *)arg;
  PyObject *handler, *args, *result;

  handler = PyObject_GetAttrString(self, "whitespace");
  if (handler == NULL)
    return EXPAT_STATUS_ERROR;

  /* if the method was not overriden, save some cycles and just return */
  if (PyCFunction_Check(handler) &&
      PyCFunction_GET_FUNCTION(handler) == filter_noop) {
    Py_DECREF(handler);
    return EXPAT_STATUS_OK;
  }

  args = PyTuple_Pack(1, data);
  if (args == NULL) {
    Py_DECREF(handler);
    return EXPAT_STATUS_ERROR;
  }
  result = PyTrace_CallObject(getcode(Whitespace), handler, args);
  Py_DECREF(args);
  if (result == NULL) {
    Py_DECREF(handler);
    return EXPAT_STATUS_ERROR;
  }
  Py_DECREF(result);
  Py_DECREF(handler);
  return EXPAT_STATUS_OK;
}

static ExpatStatus
filter_StartNamespace(void *arg, PyObject *prefix, PyObject *uri)
{
  FilterObject *self = (FilterObject *)arg;

  if (PyDict_SetItem(self->new_namespaces, prefix, uri) < 0) {
    return EXPAT_STATUS_ERROR;
  }
  return EXPAT_STATUS_OK;
}


static ExpatHandlers filter_handlers = {
  /* start_filter           */ filter_StartFilter,
  /* end_filter             */ filter_EndFilter,
  /* start_document         */ filter_StartDocument,
  /* end_document           */ filter_EndDocument,
  /* start_element          */ filter_StartElement,
  /* end_element            */ filter_EndElement,
  /* attribute              */ filter_Attribute,
  /* characters             */ filter_Characters,
  /* ignorable_whitespace   */ filter_Whitespace,
  /* processing_instruction */ NULL,
  /* comment                */ NULL,
  /* start_namespace_decl   */ filter_StartNamespace,
  /* end_namespace_decl     */ NULL,
  /* start_doctype_decl     */ NULL,
  /* end_doctype_decl       */ NULL,
  /* element_decl           */ NULL,
  /* attribute_decl         */ NULL,
  /* internal_entity_decl   */ NULL,
  /* external_entity_decl   */ NULL,
  /* unparsed_entity_decl   */ NULL,
  /* notation_decl          */ NULL,
  /* skipped_entity         */ NULL,
  /* start_cdata_section    */ NULL,
  /* end_cdata_section      */ NULL,
  /* warning                */ NULL,
  /* error                  */ NULL,
  /* fatal_error            */ NULL,
  /* resolve_entity         */ NULL,
};

/** Public Interface **************************************************/


/** Python Interface **************************************************/

static char filter_doc[] =
"Filter(*patterns) -> Filter object\n\
\n\
Base class for defining a Reader event filter.";

static PyObject *
filter_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  FilterObject *filter;
  if (!_PyArg_NoKeywords("Filter", kwds))
    return NULL;

  filter = (FilterObject *)type->tp_alloc(type, 0);
  if (filter != NULL) {
    filter->filter = ExpatFilter_New(filter, &filter_handlers, 0, NULL);
    if (filter->filter == NULL) {
      Py_DECREF(filter);
      return NULL;
    }
    Py_INCREF(args);
    filter->patterns = args;
    filter->new_namespaces = PyDict_New();
    if (filter->new_namespaces == NULL) {
      Py_DECREF(filter);
      return NULL;
    }
  }
  return (PyObject *)filter;
}

static void filter_dealloc(FilterObject *self)
{
  PyObject_GC_UnTrack(self);

  Py_CLEAR(self->new_namespaces);
  Py_CLEAR(self->patterns);
  if (self->filter) {
    ExpatFilter_Del(self->filter);
    self->filter = NULL;
  }
  self->ob_type->tp_free((PyObject *)self);
}

static int filter_traverse(FilterObject *self, visitproc visit, void *arg)
{
  Py_VISIT(self->patterns);
  return 0;
}

static int filter_clear(FilterObject *self)
{
  Py_CLEAR(self->patterns);
  return 0;
}

static PyMethodDef filter_methods[] = {
  { "start_filter", filter_noop, METH_VARARGS,
    "F.start_filter(expandedName, qualifiedName)" },
  { "end_filter", filter_noop, METH_VARARGS,
    "F.end_filter(expandedName, qualifiedName)" },
  { "start_document", filter_noop, METH_VARARGS,
    "F.start_document()" },
  { "end_document", filter_noop, METH_VARARGS,
    "F.end_document()" },
  { "start_element", filter_noop, METH_VARARGS,
    "F.start_element(expandedName, qualifiedName, namespaces, attributes)" },
  { "attribute", filter_noop, METH_VARARGS,
    "F.attribute(expandedName, qualifiedName, value)" },
  { "end_element", filter_noop, METH_VARARGS,
    "F.end_element(expandedName, qualifiedName)" },
  { "characters", filter_noop, METH_VARARGS,
    "F.characters(data)" },
  { "whitespace", filter_noop, METH_VARARGS,
    "F.whitespace(data)" },
  { NULL }
};

static PyMemberDef filter_members[] = {
  //{ "chain_next", T_OBJECT, offsetof(FilterObject, next), RO },
  { NULL }
};

static PyGetSetDef filter_getset[] = {
  { NULL }
};

PyTypeObject Filter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Expat_MODULE_NAME "." "Filter",
  /* tp_basicsize      */ sizeof(FilterObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) filter_dealloc,
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
  /* tp_doc            */ (char *) filter_doc,
  /* tp_traverse       */ (traverseproc) filter_traverse,
  /* tp_clear          */ (inquiry) filter_clear,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) filter_methods,
  /* tp_members        */ (PyMemberDef *) filter_members,
  /* tp_getset         */ (PyGetSetDef *) filter_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) filter_new,
  /* tp_free           */ 0,
};

static char handler_doc[] =
"Handler(*patterns)";

static PyObject *
handler_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  FilterObject *filter;
  if (!_PyArg_NoKeywords("Handler", kwds))
    return NULL;

  filter = (FilterObject *)type->tp_alloc(type, 0);
  if (filter != NULL) {
    filter->filter = ExpatFilter_New(filter, &filter_handlers,
                                     ExpatFilter_HANDLER_TYPE, NULL);
    Py_INCREF(args);
    filter->patterns = args;
    filter->new_namespaces = PyDict_New();
    if (filter->new_namespaces == NULL) {
      Py_DECREF(filter);
      return NULL;
    }
  }
  return (PyObject *)filter;
}

static PyTypeObject Handler_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Expat_MODULE_NAME "." "Handler",
  /* tp_basicsize      */ sizeof(FilterObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) 0,
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
                           0),
  /* tp_doc            */ (char *) handler_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) 0,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) &Filter_Type,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) handler_new,
  /* tp_free           */ 0,
};

static PyTypeObject FilterState_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Expat_MODULE_NAME "." "FilterState",
  /* tp_basicsize      */ sizeof(FilterObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) 0,
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
  /* tp_flags          */ Py_TPFLAGS_DEFAULT,
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) 0,
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

/** Module Interface **************************************************/

int _Expat_Filter_Init(PyObject *module)
{
  if (PyModule_AddType(module, &Filter_Type) < 0)
      return -1;
  if (PyModule_AddType(module, &Handler_Type) < 0)
      return -1;
  return 0;
}

void _Expat_Filter_Fini(void)
{
  PyType_CLEAR(&Filter_Type);
  PyType_CLEAR(&Handler_Type);
}
