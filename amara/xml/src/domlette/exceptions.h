#ifndef DOMLETTE_EXCEPTIONS_H
#define DOMLETTE_EXCEPTIONS_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

  int DomletteExceptions_Init(PyObject *module);
  void DomletteExceptions_Fini(void);

  extern PyObject *ReaderException_Class;

  PyObject *ReaderException_FromObject(PyObject *errorCode,
                                       PyObject *systemId,
                                       int lineNumber,
                                       int columnNumber,
                                       PyObject *kwords);

  PyObject *ReaderException_FromString(const char *errorCode,
                                       PyObject *systemId,
                                       int lineNumber,
                                       int columnNumber,
                                       PyObject *kwords);

  PyObject *ReaderException_FromInt(int errorCode,
                                    PyObject *systemId,
                                    int lineNumber,
                                    int columnNumber,
                                    PyObject *kwords);

  PyObject *XIncludeException_InvalidParseAttr(PyObject *value);
  PyObject *XIncludeException_MissingHref(void);
  PyObject *XIncludeException_TextXPointer(void);
  PyObject *XIncludeException_FragmentIdentifier(PyObject *value);
  PyObject *XIncludeException_UnsupportedXPointer(PyObject *value);
  PyObject *XIncludeException_IncludeInInclude(void);
  PyObject *XIncludeException_FallbackNotInInclude(void);
  PyObject *XIncludeException_MultipleFallbacks(void);
       
  PyObject *DOMException_HierarchyRequestErr(const char *string);
  PyObject *DOMException_NotFoundErr(const char *string);
  PyObject *DOMException_NotSupportedErr(const char *string);
  PyObject *DOMException_InvalidStateErr(const char *string);
  PyObject *DOMException_NamespaceErr(const char *string);
  PyObject *DOMException_SyntaxErr(const char *string);

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_EXCEPTIONS_H */
