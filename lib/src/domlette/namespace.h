#ifndef DOMLETTE_NAMESPACE_H
#define DOMLETTE_NAMESPACE_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "node.h"

  typedef struct {
    Node_HEAD
    Py_ssize_t hash;
    PyObject *name;
    PyObject *value;
  } NamespaceObject;

#define Namespace(op) ((NamespaceObject *)(op))
#define Namespace_GET_HASH(op) (Namespace(op)->hash)
#define Namespace_GET_NAME(op) (Namespace(op)->name)
#define Namespace_GET_VALUE(op) (Namespace(op)->value)

#ifdef Domlette_BUILDING_MODULE
#include "element.h"

  extern PyTypeObject DomletteNamespace_Type;

#define Namespace_Check(op) PyObject_TypeCheck(op, &DomletteNamespace_Type)
#define Namespace_CheckExact(op) ((op)->ob_type == &DomletteNamespace_Type)
#define Namespace_SET_VALUE(op, v) (Namespace_GET_VALUE(op) = (v))

  /* Module Methods */
  int DomletteNamespace_Init(PyObject *module);
  void DomletteNamespace_Fini(void);

  /* Namespace Methods */
  NamespaceObject *Namespace_New(PyObject *prefix, PyObject *namespaceURI);

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif


#endif /* DOMLETTE_NAMESPACE_H */
