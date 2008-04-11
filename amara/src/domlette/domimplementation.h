#ifndef DOMLETTE_DOMIMPLEMENTATION_H
#define DOMLETTE_DOMIMPLEMENTATION_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

  typedef struct {
    PyObject_HEAD
  } DOMImplementationObject;

#ifdef Domlette_BUILDING_MODULE

  extern PyObject *g_implementation;

  extern PyTypeObject DomletteDOMImplementation_Type;

#define DOMImplementation_Check(op) \
  ((op)->ob_type == &DomletteDOMImplementation_Type)

  /* Module Methods */
  int DomletteDOMImplementation_Init(PyObject *module);
  void DomletteDOMImplementation_Fini(void);

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_DOMIMPLEMENTATION_H */
