#ifndef XSLT_ROOT_H
#define XSLT_ROOT_H

#ifdef __cplusplus
extern "C" {
#endif

#include "xslt_node.h"

  typedef struct {
    XsltNodeObject __base__;
    PyObject *baseUri;
    PyObject *stylesheet;
    PyObject *validate_instructions;
    PyObject *prime_instructions;
    PyObject *teardown_instructions;
    PyObject *sources;
    PyObject *sourceNodes;
  } XsltRootObject;

#define XsltRoot(op) ((XsltRootObject *)(op))
#define XsltRoot_BASE_URI(op) (XsltRoot(op)->baseUri)
#define XsltRoot_STYLESHEET(op) (XsltRoot(op)->stylesheet)
#define XsltRoot_VALIDATE_INSTRUCTIONS(op) (XsltRoot(op)->validate_instructions)
#define XsltRoot_PRIME_INSTRUCTIONS(op) (XsltRoot(op)->prime_instructions)
#define XsltRoot_TEARDOWN_INSTRUCTIONS(op) (XsltRoot(op)->teardown_instructions)
#define XsltRoot_SOURCES(op) (XsltRoot(op)->sources)

  extern PyTypeObject XsltRoot_Type;

#define XsltRoot_Check(op) PyObject_TypeCheck((PyObject *)(op), &XsltRoot_Type)

  XsltRootObject *XsltRoot_New(PyObject *baseUri);
  int XsltRoot_AppendChild(XsltRootObject *self, XsltNodeObject *child);

  /* Module Methods */
  int XsltRoot_Init(PyObject *module);
  void XsltRoot_Fini(void);

#ifdef __cplusplus
}
#endif

#endif /* XSLT_ROOT_H */
