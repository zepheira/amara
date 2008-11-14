#ifndef DOMLETTE_ELEMENT_H
#define DOMLETTE_ELEMENT_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "node.h"

  typedef struct {
    Container_HEAD
    PyObject *namespaceURI;
    PyObject *localName;
    PyObject *qname;
    PyObject *attributes;
    PyObject *namespaces;
  } ElementObject;

#define Element(op) ((ElementObject *)(op))
#define Element_NAMESPACE_URI(op) (Element(op)->namespaceURI)
#define Element_LOCAL_NAME(op) (Element(op)->localName)
#define Element_QNAME(op) (Element(op)->qname)
#define Element_ATTRIBUTES(op) (Element(op)->attributes)
#define Element_NAMESPACES(op) (Element(op)->namespaces)

#ifdef Domlette_BUILDING_MODULE
#include "attributemap.h"
#include "namespacemap.h"

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

  NamespaceObject *Element_AddNamespace(ElementObject *self,
                                        PyObject *prefix,
                                        PyObject *namespace);
  int Element_SetNamespace(ElementObject *self, NamespaceObject *node);

  AttrObject *Element_AddAttribute(ElementObject *self,
                                   PyObject *namespaceURI,
                                   PyObject *qualifiedName,
                                   PyObject *localName,
                                   PyObject *value);
  AttrObject *Element_GetAttribute(ElementObject *self, 
                                   PyObject *namespaceURI,
                                   PyObject *localName);
  int Element_SetAttribute(ElementObject *self, AttrObject *attr);

  PyObject *Element_InscopeNamespaces(ElementObject *self);

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_ELEMENT_H */
