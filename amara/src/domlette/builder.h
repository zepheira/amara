#ifndef DOMLETTE_PARSE_EVENT_HANDLER_H
#define DOMLETTE_PARSE_EVENT_HANDLER_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

#ifdef Domlette_BUILDING_MODULE

  PyObject *Domlette_Parse(PyObject *self, PyObject *args, PyObject *kw);

  PyObject *Domlette_ParseFragment(PyObject *self, PyObject *args,
                                   PyObject *kw);

  int DomletteBuilder_Init(PyObject *module);
  void DomletteBuilder_Fini(void);

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_PARSE_EVENT_HANDLER_H */

