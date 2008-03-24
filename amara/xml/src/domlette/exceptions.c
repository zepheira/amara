#include "Python.h"
#include "exceptions.h"

/** Ft.Xml.ReaderException ********************************************/

PyObject *ReaderException_Class;

PyObject *ReaderException_FromObject(PyObject *errorCode, PyObject *systemId,
                                     int line, int column, PyObject *kwords)
{
  PyObject *args, *exception;

  args = Py_BuildValue("OOii", errorCode, systemId, line, column);
  if (args == NULL) {
    return NULL;
  }
  exception = PyObject_Call(ReaderException_Class, args, kwords);
  Py_DECREF(args);
  return exception;
}


PyObject *ReaderException_FromString(const char *errorCode, PyObject *systemId,
                                     int line, int column, PyObject *kwords)
{
  PyObject *code, *exception;
  
  code = PyObject_GetAttrString(ReaderException_Class, (char *)errorCode);
  if (code == NULL) {
    return NULL;
  }
  exception = ReaderException_FromObject(code, systemId, line, column, kwords);
  Py_DECREF(code);
  return exception;
}


PyObject *ReaderException_FromInt(int errorCode, PyObject *systemId,
                                  int line, int column, PyObject *kwords)
{
  PyObject *code, *exception;
  
  code = PyInt_FromLong(errorCode);
  if (code == NULL) {
    return NULL;
  }
  exception = ReaderException_FromObject(code, systemId, line, column, kwords);
  Py_DECREF(code);
  return exception;
}


/** Ft.Xml.XInclude Exception ********************************/

static PyObject *XIncludeException;

PyObject *XIncludeException_InvalidParseAttr(PyObject *value)
{
  PyObject *code, *exception;

  code = PyObject_GetAttrString(XIncludeException, "INVALID_PARSE_ATTR");
  if (code) {
    exception = PyObject_CallFunction(XIncludeException, "NO", code, value);
    if (exception) {
      PyErr_SetObject(XIncludeException, exception);
      Py_DECREF(exception);
    }
  }
  return NULL;
}


PyObject *XIncludeException_MissingHref(void)
{
  PyObject *code, *exception;

  code = PyObject_GetAttrString(XIncludeException, "MISSING_HREF");
  if (code) {
    exception = PyObject_CallFunction(XIncludeException, "N", code);
    if (exception) {
      PyErr_SetObject(XIncludeException, exception);
      Py_DECREF(exception);
    }
  }
  return NULL;
}

PyObject *XIncludeException_TextXPointer(void)
{
  PyObject *code, *exception;

  code = PyObject_GetAttrString(XIncludeException, "TEXT_XPOINTER");
  if (code) {
    exception = PyObject_CallFunction(XIncludeException, "N", code);
    if (exception) {
      PyErr_SetObject(XIncludeException, exception);
      Py_DECREF(exception);
    }
  }
  return NULL;
}

PyObject *XIncludeException_FragmentIdentifier(PyObject *value)
{
  PyObject *code, *exception;

  code = PyObject_GetAttrString(XIncludeException, "FRAGMENT_IDENTIFIER");
  if (code) {
    exception = PyObject_CallFunction(XIncludeException, "NO", code, value);
    if (exception) {
      PyErr_SetObject(XIncludeException, exception);
      Py_DECREF(exception);
    }
  }
  return NULL;
}

PyObject *XIncludeException_UnsupportedXPointer(PyObject *value)
{
  PyObject *code, *exception;

  code = PyObject_GetAttrString(XIncludeException, "UNSUPPORTED_XPOINTER");
  if (code) {
    exception = PyObject_CallFunction(XIncludeException, "NO", code, value);
    if (exception) {
      PyErr_SetObject(XIncludeException, exception);
      Py_DECREF(exception);
    }
  }
  return NULL;
}

PyObject *XIncludeException_IncludeInInclude(void)
{
  PyObject *code, *exception;

  code = PyObject_GetAttrString(XIncludeException, "INCLUDE_IN_INCLUDE");
  if (code) {
    exception = PyObject_CallFunction(XIncludeException, "N", code);
    if (exception) {
      PyErr_SetObject(XIncludeException, exception);
      Py_DECREF(exception);
    }
  }
  return NULL;
}

PyObject *XIncludeException_FallbackNotInInclude(void)
{
  PyObject *code, *exception;

  code = PyObject_GetAttrString(XIncludeException, "FALLBACK_NOT_IN_INCLUDE");
  if (code) {
    exception = PyObject_CallFunction(XIncludeException, "N", code);
    if (exception) {
      PyErr_SetObject(XIncludeException, exception);
      Py_DECREF(exception);
    }
  }
  return NULL;
}

PyObject *XIncludeException_MultipleFallbacks(void)
{
  PyObject *code, *exception;

  code = PyObject_GetAttrString(XIncludeException, "MULTIPLE_FALLBACKS");
  if (code) {
    exception = PyObject_CallFunction(XIncludeException, "N", code);
    if (exception) {
      PyErr_SetObject(XIncludeException, exception);
      Py_DECREF(exception);
    }
  }
  return NULL;
}

/** xml.dom.DOMException **********************************************/

static PyObject *IndexSizeErr;
static PyObject *DomstringSizeErr;
static PyObject *HierarchyRequestErr;
static PyObject *WrongDocumentErr;
static PyObject *InvalidCharacterErr;
static PyObject *NoDataAllowedErr;
static PyObject *NoModificationAllowedErr;
static PyObject *NotFoundErr;
static PyObject *NotSupportedErr;
static PyObject *InuseAttributeErr;
static PyObject *InvalidStateErr;
static PyObject *SyntaxErr;
static PyObject *InvalidModificationErr;
static PyObject *NamespaceErr;
static PyObject *InvalidAccessErr;


PyObject *DOMException_HierarchyRequestErr(const char *string)
{
  PyObject *exception = PyObject_CallFunction(HierarchyRequestErr, "s", string);
  if (exception) {
    PyErr_SetObject(HierarchyRequestErr, exception);
    Py_DECREF(exception);
  }
  return NULL;
}

PyObject *DOMException_NotFoundErr(const char *string)
{
  PyObject *exception = PyObject_CallFunction(NotFoundErr, "s", string);
  if (exception) {
    PyErr_SetObject(NotFoundErr, exception);
    Py_DECREF(exception);
  }
  return NULL;
}

PyObject *DOMException_NotSupportedErr(const char *string)
{
  PyObject *exception = PyObject_CallFunction(NotSupportedErr, "s", string);
  if (exception) {
    PyErr_SetObject(NotSupportedErr, exception);
    Py_DECREF(exception);
  }
  return NULL;
}

PyObject *DOMException_InvalidStateErr(const char *string)
{
  PyObject *exception = PyObject_CallFunction(InvalidStateErr, "s", string);
  if (exception) {
    PyErr_SetObject(InvalidStateErr, exception);
    Py_DECREF(exception);
  }
  return NULL;
}

PyObject *DOMException_NamespaceErr(const char *string)
{
  PyObject *exception = PyObject_CallFunction(NamespaceErr, "s", string);
  if (exception) {
    PyErr_SetObject(NamespaceErr, exception);
    Py_DECREF(exception);
  }
  return NULL;
}

PyObject *DOMException_SyntaxErr(const char *string)
{
  PyObject *exception = PyObject_CallFunction(SyntaxErr, "s", string);
  if (exception) {
    PyErr_SetObject(SyntaxErr, exception);
    Py_DECREF(exception);
  }
  return NULL;
}

/** Initialization ****************************************************/

int DomletteExceptions_Init(PyObject *module)
{
  PyObject *import;

  /* Load the ReaderException and XIncludeException */
  import = PyImport_ImportModule("Ft.Xml");
  if (import == NULL) return -1;
  ReaderException_Class = PyObject_GetAttrString(import, "ReaderException");
  if (ReaderException_Class == NULL) {
    Py_DECREF(import);
    return -1;
  }
  XIncludeException = PyObject_GetAttrString(import, "XIncludeException");
  if (XIncludeException == NULL) {
    Py_DECREF(import);
    return -1;
  }
  Py_DECREF(import);

  /* Load the DOMExceptions */
  import  = PyImport_ImportModule("xml.dom");
  if (import == NULL) return -1;

#define GET_DOM_EXC(NAME) \
  NAME = PyObject_GetAttrString(import, #NAME); \
  if (NAME == NULL) {                           \
    Py_DECREF(import);                          \
    return -1;                                  \
  }

  GET_DOM_EXC(IndexSizeErr);
  GET_DOM_EXC(HierarchyRequestErr);
  GET_DOM_EXC(WrongDocumentErr);
  GET_DOM_EXC(InvalidCharacterErr);
  GET_DOM_EXC(NoDataAllowedErr);
  GET_DOM_EXC(NoModificationAllowedErr);
  GET_DOM_EXC(NotFoundErr);
  GET_DOM_EXC(NotSupportedErr);
  GET_DOM_EXC(InuseAttributeErr);
  GET_DOM_EXC(InvalidStateErr);
  GET_DOM_EXC(SyntaxErr);
  GET_DOM_EXC(InvalidModificationErr);
  GET_DOM_EXC(NamespaceErr);
  GET_DOM_EXC(InvalidAccessErr);

  /* special case exception misnaming */
  if (PyObject_HasAttrString(import, "DomstringSizeErr")) {
    /* Python 2.1+ and PyXML 0.8+ */
    DomstringSizeErr = PyObject_GetAttrString(import, "DomstringSizeErr");
  } else {
    /* PyXML < 0.8 */
    DomstringSizeErr = PyObject_GetAttrString(import, "DOMStringSizeErr");
  }
  if (DomstringSizeErr == NULL) {
    Py_DECREF(import);
    return -1;
  }
  Py_DECREF(import);

  return 0;
}

/** Finalization ******************************************************/

void DomletteExceptions_Fini(void)
{
  Py_DECREF(ReaderException_Class);
  Py_DECREF(XIncludeException);
  Py_DECREF(IndexSizeErr);
  Py_DECREF(DomstringSizeErr);
  Py_DECREF(HierarchyRequestErr);
  Py_DECREF(WrongDocumentErr);
  Py_DECREF(InvalidCharacterErr);
  Py_DECREF(NoDataAllowedErr);
  Py_DECREF(NoModificationAllowedErr);
  Py_DECREF(NotFoundErr);
  Py_DECREF(NotSupportedErr);
  Py_DECREF(InuseAttributeErr);
  Py_DECREF(InvalidStateErr);
  Py_DECREF(SyntaxErr);
  Py_DECREF(InvalidModificationErr);
  Py_DECREF(NamespaceErr);
  Py_DECREF(InvalidAccessErr);
}
