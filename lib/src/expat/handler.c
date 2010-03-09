/* ----------------------------------------------------------------------
 * handler.c
 *
 * This file defines the _expat.Handler base class.   There are two
 * parts to the implementation:
 *
 * First, a Python class called Handler is defined with the following
 * interface (shown in Python pseudocode):
 *
 * class Handler:
 *     def start_document(self):
 *         pass
 *     def end_documnet(self):
 *         pass
 *     def start_element(self,expandedName,qualifiedName,namespaces,attributes):
 *         pass
 *     def end_element(self,expandedName,qualifiedName):
 *         pass
 *     def attribute(self,expandedName,qualifiedName,value):
 *         pass
 *     def characters(self,data):
 *         pass
 *     def whitespace(self,data):
 *         pass
 *      
 * The above class does nothing---it is only meant to serve as a base
 * class.
 *
 * Second, a set of functions (handler_*) are defined and placed into
 * an ExpatHandlerFuncs dispatch table.  This table provides a bridge
 * between the above Python class and the low-level parsing code in
 * expat.c.  Specifically, during parsing, the parser calls handler_* 
 * functions in the dispatch table, which it turn, dispatch methods on the 
 * above Handler class.   If a user has defined their own handler
 * by inheriting from _expat.Handler, their methods should be trigger.
 *
 * Note:  The only part of Amara that appears to use Handler directly
 * is the xupdate module.
 * ---------------------------------------------------------------------- */

#include "expat_interface.h"
#include "attributes.h"

/** Private Interface *************************************************/

enum HandlerTypes {
  /* ContentHandler */
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
static PyObject *handler_noop(PyObject *self, PyObject *args)
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
handler_StartDocument(void *arg)
{
  PyObject *self = (PyObject *)arg;
  PyObject *handler, *args, *result;

  PyObject_Print(self, stdout, 0);
  fflush(stdout);

  handler = PyObject_GetAttrString(self, "start_document");
  if (handler == NULL)
    return EXPAT_STATUS_ERROR;

  /* if the method was not overriden, save some cycles and just return */
  if (PyCFunction_Check(handler) &&
      PyCFunction_GET_FUNCTION(handler) == handler_noop) {
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
handler_EndDocument(void *arg)
{
  PyObject *self = (PyObject *)arg;
  PyObject *handler, *args, *result;

  handler = PyObject_GetAttrString(self, "end_document");
  if (handler == NULL)
    return EXPAT_STATUS_ERROR;

  /* if the method was not overriden, save some cycles and just return */
  if (PyCFunction_Check(handler) &&
      PyCFunction_GET_FUNCTION(handler) == handler_noop) {
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
handler_StartElement(void *arg, ExpatName *name, ExpatAttribute atts[],
                    size_t natts)
{
  HandlerObject *self = (HandlerObject *)arg;
  PyObject *handler, *args, *result;

  handler = PyObject_GetAttrString((PyObject *)self, "start_element");
  if (handler == NULL)
    return EXPAT_STATUS_ERROR;

  /* if the method was not overriden, save some cycles and just return */
  if (PyCFunction_Check(handler) &&
      PyCFunction_GET_FUNCTION(handler) == handler_noop) {
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
handler_EndElement(void *arg, ExpatName *name)
{
  PyObject *self = (PyObject *)arg;
  PyObject *handler, *args, *result;

  handler = PyObject_GetAttrString(self, "end_element");
  if (handler == NULL)
    return EXPAT_STATUS_ERROR;

  /* if the method was not overriden, save some cycles and just return */
  if (PyCFunction_Check(handler) &&
      PyCFunction_GET_FUNCTION(handler) == handler_noop) {
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
handler_Attribute(void *arg, ExpatName *name, PyObject *value, AttributeType type)
{
  return EXPAT_STATUS_OK;
}

static ExpatStatus
handler_Characters(void *arg, PyObject *data)
{
  PyObject *self = (PyObject *)arg;
  PyObject *handler, *args, *result;

  handler = PyObject_GetAttrString(self, "characters");
  if (handler == NULL)
    return EXPAT_STATUS_ERROR;

  /* if the method was not overriden, save some cycles and just return */
  if (PyCFunction_Check(handler) &&
      PyCFunction_GET_FUNCTION(handler) == handler_noop) {
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
handler_Whitespace(void *arg, PyObject *data)
{
  PyObject *self = (PyObject *)arg;
  PyObject *handler, *args, *result;

  handler = PyObject_GetAttrString(self, "whitespace");
  if (handler == NULL)
    return EXPAT_STATUS_ERROR;

  /* if the method was not overriden, save some cycles and just return */
  if (PyCFunction_Check(handler) &&
      PyCFunction_GET_FUNCTION(handler) == handler_noop) {
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
handler_StartNamespace(void *arg, PyObject *prefix, PyObject *uri)
{
  HandlerObject *self = (HandlerObject *)arg;

  if (PyDict_SetItem(self->new_namespaces, prefix, uri) < 0) {
    return EXPAT_STATUS_ERROR;
  }
  return EXPAT_STATUS_OK;
}


static ExpatHandlerFuncs handler_handlers = {
  /* start_document         */ handler_StartDocument,
  /* end_document           */ handler_EndDocument,
  /* start_element          */ handler_StartElement,
  /* end_element            */ handler_EndElement,
  /* attribute              */ handler_Attribute,
  /* characters             */ handler_Characters,
  /* ignorable_whitespace   */ handler_Whitespace,
  /* processing_instruction */ NULL,
  /* comment                */ NULL,
  /* start_namespace_decl   */ handler_StartNamespace,
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

static char handler_doc[] =
"Handler()";

static PyObject *
handler_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  HandlerObject *handler;
  if (!_PyArg_NoKeywords("Handler", kwds))
    return NULL;

  if (!PyArg_ParseTuple(args,":Handler")) {
    return NULL;
  }
  handler = (HandlerObject *)type->tp_alloc(type, 0);
  if (handler != NULL) {
    handler->handler = ExpatHandler_New(handler, &handler_handlers);
    handler->new_namespaces = PyDict_New();
    if (handler->new_namespaces == NULL) {
      Py_DECREF(handler);
      return NULL;
    }
  }
  return (PyObject *)handler;
}

static void handler_dealloc(HandlerObject *self)
{
  Py_CLEAR(self->new_namespaces);
  if (self->handler) {
    ExpatHandler_Del(self->handler);
    self->handler = NULL;
  }
  self->ob_type->tp_free((PyObject *)self);
}


/** Public Interface **************************************************/


/** Python Interface **************************************************/

static PyMethodDef handler_methods[] = {
  { "start_document", handler_noop, METH_VARARGS,
    "H.start_document()" },
  { "end_document", handler_noop, METH_VARARGS,
    "H.end_document()" },
  { "start_element", handler_noop, METH_VARARGS,
    "H.start_element(expandedName, qualifiedName, namespaces, attributes)" },
  { "attribute", handler_noop, METH_VARARGS,
    "H.attribute(expandedName, qualifiedName, value)" },
  { "end_element", handler_noop, METH_VARARGS,
    "H.end_element(expandedName, qualifiedName)" },
  { "characters", handler_noop, METH_VARARGS,
    "H.characters(data)" },
  { "whitespace", handler_noop, METH_VARARGS,
    "H.whitespace(data)" },
  { NULL }
};

static PyMemberDef handler_members[] = {
  //{ "chain_next", T_OBJECT, offsetof(HandlerObject, next), RO },
  { NULL }
};

static PyGetSetDef handler_getset[] = {
  { NULL }
};

PyTypeObject Handler_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Expat_MODULE_NAME "." "Handler",
  /* tp_basicsize      */ sizeof(HandlerObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) handler_dealloc,
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
			   //                           Py_TPFLAGS_HAVE_GC |  /* support cyclic GC */
                           0),
  /* tp_doc            */ (char *) handler_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) handler_methods,
  /* tp_members        */ (PyMemberDef *) handler_members,
  /* tp_getset         */ (PyGetSetDef *) handler_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) handler_new,
  /* tp_free           */ 0,
};

/** Module Interface **************************************************/

int _Expat_Handler_Init(PyObject *module)
{
  if (PyModule_AddType(module, &Handler_Type) < 0)
        return -1;
  return 0;
}

void _Expat_Handler_Fini(void)
{
  PyType_CLEAR(&Handler_Type);
}
