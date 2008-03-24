#ifndef EXPAT_SAX_FILTER_H
#define EXPAT_SAX_FILTER_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

#ifdef Expat_BUILDING_MODULE

  int _Expat_SaxFilter_Init(PyObject *module);
  void _Expat_SaxFilter_Fini(void);

#endif /* Expat_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* EXPAT_SAX_FILTER_H */
