#ifndef EXPAT_READER_H
#define EXPAT_READER_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

#ifdef Expat_BUILDING_MODULE

  int _Expat_Reader_Init(PyObject *module);
  void _Expat_Reader_Fini(void);

#endif /* Expat_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* EXPAT_READER_H */
