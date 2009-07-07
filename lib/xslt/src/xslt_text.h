#ifndef XSLT_TEXT_H
#define XSLT_TEXT_H

#ifdef __cplusplus
extern "C" {
#endif

#include "xslt_node.h"
#include "xslt_root.h"

  typedef struct {
    XsltNodeObject __base__;
    PyObject *data;
  } XsltTextObject;

#define XsltText_DATA(op) (((XsltTextObject *)(op))->data)

  extern PyTypeObject XsltText_Type;

#define XsltText_Check(op) \
  PyObject_TypeCheck((PyObject *)(op), &XsltText_Type)

  XsltNodeObject *XsltText_New(XsltRootObject *root, PyObject *data);

  /* Module Methods */
  int XsltText_Init(PyObject *module);
  void XsltText_Fini(void);

#ifdef __cplusplus
}
#endif

#endif /* XSLT_TEXT_H */
