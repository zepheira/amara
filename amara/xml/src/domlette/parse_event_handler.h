#ifndef DOMLETTE_PARSE_EVENT_HANDLER_H
#define DOMLETTE_PARSE_EVENT_HANDLER_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

#ifdef Domlette_BUILDING_MODULE

  typedef enum {
    PARSE_TYPE_STANDALONE = 0,
    PARSE_TYPE_NO_VALIDATE,
    PARSE_TYPE_VALIDATE,
  } ParseType;

  typedef struct {
    PyObject *document_new;
    PyObject *element_new;
    PyObject *attr_new;
    PyObject *text_new;
    PyObject *processing_instruction_new;
    PyObject *comment_new;
  } NodeFactories;

  PyObject *ParseDocument(PyObject *inputSource, ParseType parseType,
                          NodeFactories *factories);

  PyObject *ParseFragment(PyObject *inputSource, PyObject *namespaces,
                          NodeFactories *factories);

  int DomletteBuilder_Init(PyObject *module);
  void DomletteBuilder_Fini(void);

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_PARSE_EVENT_HANDLER_H */

