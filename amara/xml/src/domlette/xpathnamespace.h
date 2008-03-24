#ifndef DOMLETTE_XPATHNAMESPACE_H
#define DOMLETTE_XPATHNAMESPACE_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "node.h"
#include "element.h"

  typedef struct {
    Node_HEAD
    PyObject *nodeName;
    PyObject *nodeValue;
  } XPathNamespaceObject;

#define XPathNamespace(op) ((XPathNamespaceObject *)(op))
#define XPathNamespace_GET_NAME(op) (XPathNamespace(op)->nodeName)
#define XPathNamespace_GET_VALUE(op) (XPathNamespace(op)->nodeValue)

#ifdef Domlette_BUILDING_MODULE

  extern PyTypeObject DomletteXPathNamespace_Type;

#define XPathNamespace_Check(op) \
  PyObject_TypeCheck(op, &DomletteXPathNamespace_Type)
#define XPathNamespace_CheckExact(op) \
  ((op)->ob_type == &DomletteXPathNamespace_Type)

  /* Module Methods */
  int DomletteXPathNamespace_Init(PyObject *module);
  void DomletteXPathNamespace_Fini(void);

  /* XPathNamespace Methods */
  XPathNamespaceObject *XPathNamespace_New(ElementObject *parentNode,
                                           PyObject *prefix,
                                           PyObject *namespaceURI);

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif


#endif /* DOMLETTE_XPATHNAMESPACE_H */
