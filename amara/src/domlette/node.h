#ifndef DOMLETTE_NODE_H
#define DOMLETTE_NODE_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

  /* Node_HEAD defines the initial segment of every Domlette node. */
#define Node_HEAD                      \
    PyObject_HEAD                      \
    struct NodeObject *parent;

  /* Nothing is actually declared to be a NodeObject, but every pointer to
   * a Domlette object can be cast to a NodeObject*.  This is inheritance
   * built by hand.
   */
  typedef struct NodeObject {
    Node_HEAD
  } NodeObject;

#define Node(op) ((NodeObject *)(op))
#define Node_GET_PARENT(op) (Node(op)->parent)
#define Node_SET_PARENT(op, v) (Node_GET_PARENT(op) = (v))

#ifdef Domlette_BUILDING_MODULE

  extern PyTypeObject DomletteNode_Type;

#define Node_Check(op) PyObject_TypeCheck((op), &DomletteNode_Type)

  /* Module Methods */
  int DomletteNode_Init(PyObject *module);
  void DomletteNode_Fini(void);

  NodeObject *_Node_New(PyTypeObject *type);
#define Node_New(type, typeobj) ((type *) _Node_New(typeobj))

  void _Node_Del(NodeObject *node);
#define Node_Del(obj) _Node_Del((NodeObject *)(obj))

  int Node_DispatchEvent(NodeObject *self, PyObject *event, NodeObject *target);

#endif /* Domlette_BUILDING_MODULE */

#include "container.h"

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_NODE_H */
