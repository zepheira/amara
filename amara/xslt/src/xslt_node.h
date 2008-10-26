#ifndef XSLT_NODE_H
#define XSLT_NODE_H

#include "Python.h"
#include "structmember.h"

/* Backward compat code recommended in PEP 353 */
#if PY_VERSION_HEX < 0x02050000
  typedef int Py_ssize_t;
#define PY_FORMAT_SIZE_T ""
  typedef inquiry lenfunc;
  //typedef intargfunc ssizeargfunc;
  //typedef intintargfunc ssizessizeargfunc;
  //typedef intobjargproc ssizeobjargproc;
  //typedef intintobjargproc ssizessizeobjargproc;
#endif

#ifdef __cplusplus
extern "C" {
#endif

  typedef struct {
    PyObject_HEAD
    PyObject *root;
    PyObject *parent;
  } XsltNodeObject;

#define XsltNode(op) ((XsltNodeObject *)(op))
#define XsltNode_ROOT(op) (((XsltNodeObject *)(op))->root)
#define XsltNode_GET_PARENT(op) (((XsltNodeObject *)(op))->parent)
#define XsltNode_SET_PARENT(op, v) (XsltNode_GET_PARENT(op) = (v))

  extern PyTypeObject XsltNode_Type;

#define XsltNode_Check(op) \
  PyObject_TypeCheck((PyObject *)(op), &XsltNode_Type)

  /* Module Methods */
  int XsltNode_Init(PyObject *module);
  void XsltNode_Fini(void);

  /* XsltNode Methods */
  XsltNodeObject *XsltNode_New(PyTypeObject *type);
  int XsltNode_Link(XsltNodeObject *self, XsltNodeObject *child);
  int XsltNode_PrettyPrint(XsltNodeObject *self);

#ifdef __cplusplus
}
#endif

#endif /* XSLT_NODE_H */
