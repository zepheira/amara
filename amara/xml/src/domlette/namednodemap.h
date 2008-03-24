#ifndef DOMLETTE_NAMEDNODEMAP_H
#define DOMLETTE_NAMEDNODEMAP_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

  PyObject *NamedNodeMap_New(PyObject *dict);

  /* Module Methods */
  int DomletteNamedNodeMap_Init(PyObject *module);
  void DomletteNamedNodeMap_Fini(void);

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_CHARACTERDATA_H */
