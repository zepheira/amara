#ifndef XSLT_ELEMENT_H
#define XSLT_ELEMENT_H

#ifdef __cplusplus
extern "C" {
#endif

#include "xslt_node.h"

  typedef struct {
    XsltNodeObject __base__;
    Py_ssize_t count, allocated;
    XsltNodeObject **nodes;
    PyObject *nodeName;
    PyObject *expanded_name;
    PyObject *attributes;
    PyObject *namespaces;
    PyObject *baseUri;
    int import_precedence;
    int lineNumber;
    int columnNumber;
  } XsltElementObject;

#define XsltElement(op) ((XsltElementObject *)(op))
#define XsltElement_NODE_NAME(op)         (XsltElement(op)->nodeName)
#define XsltElement_EXPANDED_NAME(op)     (XsltElement(op)->expanded_name)
#define XsltElement_ATTRIBUTES(op)        (XsltElement(op)->attributes)
#define XsltElement_NAMESPACES(op)        (XsltElement(op)->namespaces)
#define XsltElement_BASE_URI(op)          (XsltElement(op)->baseUri)
#define XsltElement_LINE_NUMBER(op)       (XsltElement(op)->lineNumber)
#define XsltElement_COLUMN_NUMBER(op)     (XsltElement(op)->columnNumber)
#define XsltElement_IMPORT_PRECEDENCE(op) (XsltElement(op)->import_precedence)

#define XsltElement_CHILDREN(op)      (XsltElement(op)->children)
#define XsltElement_GET_COUNT(op)     (XsltElement(op)->count)
#define XsltElement_GET_NODES(op)     (XsltElement(op)->nodes)
#define XsltElement_GET_CHILD(op, i)  (XsltElement_GET_NODES(op)[i])

  extern PyTypeObject XsltElement_Type;

#define XsltElement_Check(op) \
  PyObject_TypeCheck((PyObject *)(op), &XsltElement_Type)

  /* Module Methods */
  int XsltElement_Init(PyObject *module);
  void XsltElement_Fini(void);

  /* XsltElement Methods */
  int XsltElement_AppendChild(XsltElementObject *self, XsltNodeObject *child);
  int XsltElement_InsertChild(XsltElementObject *self, XsltNodeObject *child,
                              Py_ssize_t index);
  int XsltElement_Merge(XsltElementObject *self, XsltElementObject *other);
  int XsltElement_SetAttribute(XsltElementObject *self, PyObject *namespaceURI,
                               PyObject *localName, PyObject *value);

#ifdef __cplusplus
}
#endif

#endif /* XSLT_ELEMENT_H */
