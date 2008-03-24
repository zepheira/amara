#ifndef EXPAT_UTIL_H
#define EXPAT_UTIL_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

#ifdef Expat_BUILDING_MODULE

  PyObject *PyTrace_CallObject(PyCodeObject *code, PyObject *func,
                               PyObject *args);

  #define PyCode_Here(NAME) _PyCode_Here((NAME), __FILE__, __LINE__)
  PyCodeObject *_PyCode_Here(char *name, char *file, int line);

  /* Add a type object to `module` using `type.__name__`.
   * This convenience function can be used from the module's initialization
   * function. Return -1 on error, 0 on success. */
  int PyModule_AddType(PyObject *module, PyTypeObject *type);

  int _Expat_Util_Init(PyObject *module);
  void _Expat_Util_Fini(void);

#endif /* Expat_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* EXPAT_UTIL_H */
