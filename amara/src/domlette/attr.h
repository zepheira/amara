#ifndef DOMLETTE_ATTR_H
#define DOMLETTE_ATTR_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "node.h"
#include "../expat/validation.h"

  typedef struct {
    Node_HEAD
    PyObject *namespaceURI;
    PyObject *localName;
    PyObject *nodeName;
    PyObject *nodeValue;
    AttributeType type;
  } AttrObject;

#define Attr(op) ((AttrObject *)(op))
#define Attr_GET_NAMESPACE_URI(op) (Attr(op)->namespaceURI)
#define Attr_GET_LOCAL_NAME(op) (Attr(op)->localName)
#define Attr_GET_NODE_NAME(op) (Attr(op)->nodeName)
#define Attr_GET_NODE_VALUE(op) (Attr(op)->nodeValue)
#define Attr_GET_VALUE(op) (Attr(op)->nodeValue)
#define Attr_GET_TYPE(op) (Attr(op)->type)

#ifdef Domlette_BUILDING_MODULE

  extern PyTypeObject DomletteAttr_Type;

#define Attr_Check(op) PyObject_TypeCheck((op), &DomletteAttr_Type)
#define Attr_CheckExact(op) ((op)->ob_type == &DomletteAttr_Type)
#define Attr_SET_VALUE(op, v) (Attr_GET_NODE_VALUE(op) = (v))
#define Attr_SET_TYPE(op, v) (Attr_GET_TYPE(op) = (v))

  /* Module Methods */
  int DomletteAttr_Init(PyObject *module);
  void DomletteAttr_Fini(void);

  /* Attr Methods */
  AttrObject *Attr_New(PyObject *namespaceURI, PyObject *qualifiedName,
                       PyObject *localName, PyObject *value);

  AttrObject *Attr_Copy(PyObject *self, int deep);

#endif

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_ATTR_H */
