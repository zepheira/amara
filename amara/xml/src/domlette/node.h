#ifndef DOMLETTE_NODE_H
#define DOMLETTE_NODE_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "nodetype.h"

  /* Node_HEAD defines the initial segment of every Domlette node. */
#define Node_HEAD                      \
    PyObject_HEAD                      \
    long flags;                        \
    struct NodeObject *parentNode;

#define ContainerNode_HEAD             \
    Node_HEAD                          \
    Py_ssize_t count;                  \
    struct NodeObject **nodes;         \
    Py_ssize_t allocated;

#include "document.h"

  /* Nothing is actually declared to be a NodeObject, but every pointer to
   * a Domlette object can be cast to a NodeObject*.  This is inheritance
   * built by hand.
   */
  typedef struct NodeObject {
    Node_HEAD
  } NodeObject;

  typedef struct ContainerNodeObject {
    ContainerNode_HEAD
  } ContainerNodeObject;

#define Node_GET_PARENT(op) (((NodeObject *)(op))->parentNode)
#define Node_SET_PARENT(op, v) (Node_GET_PARENT(op) = (v))

#define ContainerNode_GET_COUNT(op) (((ContainerNodeObject *)(op))->count)
#define ContainerNode_GET_CHILD(op, i)          \
  (((ContainerNodeObject *)(op))->nodes[i])

  /* NodeObject Creatation */
#define Node_FLAGS_CONTAINER (1L<<0)

#define Node_HasFlag(n,f) ((n)->flags & (f))
#define Node_SetFlag(n,f) ((n)->flags |= (f))
#define Node_ClearFlag(n,f) ((n)->flags &= ~(f))

#ifdef Domlette_BUILDING_MODULE

  extern PyTypeObject DomletteNode_Type;

#define Node_Check(op) PyObject_TypeCheck((op), &DomletteNode_Type)
#define Node_CheckExact(op) ((op)->ob_type == &DomletteNode_Type)

  /* Module Methods */
  int DomletteNode_Init(PyObject *module);
  void DomletteNode_Fini(void);

#define _Node_INIT_FLAGS(op, f) \
  ( (op)->flags = (f), \
    (op)->parentNode = NULL )

#define _Node_INIT(op) \
  _Node_INIT_FLAGS((op), 0)
#define _Node_INIT_CONTAINER(op) \
  ( (op)->count = 0, (op)->allocated = 0, (op)->nodes = NULL, \
    _Node_INIT_FLAGS((op), Node_FLAGS_CONTAINER) )

  NodeObject *_Node_New(PyTypeObject *type, long flags);
#define Node_New(type, typeobj) \
  ((type *) _Node_New((typeobj), 0))
#define Node_NewContainer(type, typeobj) \
  ((type *) _Node_New((typeobj), Node_FLAGS_CONTAINER))

  void _Node_Del(NodeObject *node);
#define Node_Del(obj) _Node_Del((NodeObject *)(obj))

  int _Node_SetChildren(NodeObject *self, NodeObject **children,
                        Py_ssize_t size);

  /* DOM Node Methods */
  int Node_RemoveChild(NodeObject *self, NodeObject *oldChild);
  int Node_AppendChild(NodeObject *self, NodeObject *newChild);
  int Node_InsertBefore(NodeObject *self, NodeObject *newChild,
                        NodeObject *refChild);
  int Node_ReplaceChild(NodeObject *self, NodeObject *newChild,
                        NodeObject *oldChild);
  NodeObject *Node_CloneNode(PyObject *node, int deep);

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_NODE_H */
