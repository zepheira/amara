#ifndef DOMLETTE_ELEMENT_H
#define DOMLETTE_ELEMENT_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "node.h"
#include "attr.h"

  typedef struct {
    ContainerNode_HEAD
    PyObject *namespaceURI;
    PyObject *localName;
    PyObject *nodeName;
    PyObject *attributes;
  } ElementObject;

#define Element(op) ((ElementObject *)(op))
#define Element_GET_NAMESPACE_URI(op) (Element(op)->namespaceURI)
#define Element_GET_LOCAL_NAME(op) (Element(op)->localName)
#define Element_GET_NODE_NAME(op) (Element(op)->nodeName)
#define Element_GET_ATTRIBUTES(op) (Element(op)->attributes)

#ifdef Domlette_BUILDING_MODULE

  extern PyTypeObject DomletteElement_Type;

#define Element_Check(op) PyObject_TypeCheck((op), &DomletteElement_Type)
#define Element_CheckExact(op) ((op)->ob_type == &DomletteElement_Type)

  /* Module Methods */
  int DomletteElement_Init(PyObject *module);
  void DomletteElement_Fini(void);

  /* Element Methods */
  ElementObject *Element_New(PyObject *namespaceURI,
                             PyObject *qualifiedName,
                             PyObject *localName);

  AttrObject *Element_SetAttributeNS(ElementObject *self,
                                     PyObject *namespaceURI,
                                     PyObject *qualifiedName,
                                     PyObject *localName,
                                     PyObject *value);

  PyObject *Element_GetAttributeNodeNS(ElementObject *self,
                                       PyObject *namespaceURI,
                                       PyObject *localName);
  PyObject *Element_SetAttributeNodeNS(ElementObject *self,
                                       AttrObject *attr);

  ElementObject *Element_CloneNode(PyObject *node, int deep);

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_ELEMENT_H */
