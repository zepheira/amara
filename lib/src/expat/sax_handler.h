#ifndef EXPAT_SAX_HANDLER_H
#define EXPAT_SAX_HANDLER_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

#ifdef Expat_BUILDING_MODULE

  int _Expat_SaxHandler_Init(PyObject *module);
  void _Expat_SaxHandler_Fini(void);

#endif /* Expat_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* EXPAT_SAX_HANDLER_H */
