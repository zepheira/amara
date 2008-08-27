#ifndef DOMLETTE_NAMESPACE_H
#define DOMLETTE_NAMESPACE_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "node.h"

  typedef struct {
    Node_HEAD
    PyObject *nodeName;
    PyObject *nodeValue;
  } NamespaceObject;

#define Namespace(op) ((NamespaceObject *)(op))
#define Namespace_GET_NAME(op) (Namespace(op)->nodeName)
#define Namespace_GET_VALUE(op) (Namespace(op)->nodeValue)
#define Namespace_SET_VALUE(op, v) ((Namespace(op)->nodeValue) = (v))

#ifdef Domlette_BUILDING_MODULE
#include "element.h"

  extern PyTypeObject DomletteNamespace_Type;

#define Namespace_Check(op) PyObject_TypeCheck(op, &DomletteNamespace_Type)
#define Namespace_CheckExact(op) ((op)->ob_type == &DomletteNamespace_Type)

  /* Module Methods */
  int DomletteNamespace_Init(PyObject *module);
  void DomletteNamespace_Fini(void);

  /* Namespace Methods */
  NamespaceObject *Namespace_New(ElementObject *parentNode,
                                 PyObject *prefix,
                                 PyObject *namespaceURI);

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif


#endif /* DOMLETTE_NAMESPACE_H */
