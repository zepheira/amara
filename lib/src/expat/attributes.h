#ifndef EXPAT_ATTRIBUTES_H
#define EXPAT_ATTRIBUTES_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "expat_interface.h"

  PyObject *Attributes_New(ExpatAttribute atts[], Py_ssize_t length);

  int Attributes_SetItem(PyObject *attributes,
                         PyObject *namespaceURI, PyObject *localName,
                         PyObject *qualifiedName, PyObject *value);

#ifdef Expat_BUILDING_MODULE
  int _Expat_Attributes_Init(PyObject *module);
  void _Expat_Attributes_Fini(void);
#endif

#ifdef __cplusplus
}
#endif

#endif /* EXPAT_ATTRIBUTES_H */
