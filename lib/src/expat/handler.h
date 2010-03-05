#ifndef DOMLETTE_EXPAT_HANDLER_H
#define DOMLETTE_EXPAT_HANDLER_H

#ifdef __cplusplus
extern "C" {
#endif

  #include "Python.h"

#ifdef Expat_BUILDING_MODULE

  typedef struct {
    PyObject_HEAD
    ExpatHandler *handler;
    /* parsing state */
    PyObject *new_namespaces;
  } HandlerObject;

#define Handler_GET_HANDLER(op) (((HandlerObject *)(op))->handler)

  extern PyTypeObject Handler_Type;
#define Handler_Check(op) PyObject_TypeCheck((PyObject *)(op), &Handler_Type)
  int _Expat_Handler_Init(PyObject *module);
  void _Expat_Handler_Fini(void);

#endif

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_EXPAT_HANDLER_H */
