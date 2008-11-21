#ifndef DOMLETTE_CONTAINER_H
#define DOMLETTE_CONTAINER_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "node.h"

  /* Container_HEAD defines the initial segment of all container nodes. */
#define Container_HEAD      \
    Node_HEAD               \
    Py_ssize_t count;       \
    NodeObject **nodes;     \
    Py_ssize_t allocated;

  /* Nothing is actually declared to be a ContainerObject, but every pointer 
   * to a Domlette container object can be cast to a ContainerObject*.
   */
  typedef struct ContainerObject {
    Container_HEAD
  } ContainerObject;

#define Container_GET_COUNT(op)    (((ContainerObject *)(op))->count)
#define Container_GET_NODES(op)    (((ContainerObject *)(op))->nodes)
#define Container_GET_CHILD(op, i) (((ContainerObject *)(op))->nodes[i])

#ifdef Domlette_BUILDING_MODULE

  extern PyTypeObject DomletteContainer_Type;

#define Container_Check(op) PyObject_TypeCheck((op), &DomletteContainer_Type)

  /* Module Methods */
  int DomletteContainer_Init(PyObject *module);
  void DomletteContainer_Fini(void);

#define Container_New Node_New

  void _Container_Del(NodeObject *node);
#define Container_Del(obj) _Container_Del((NodeObject *)(obj))

  int _Container_SetChildren(NodeObject *self, NodeObject **children,
                             Py_ssize_t size);

  int Container_Append(NodeObject *self, NodeObject *child);
  int Container_Remove(NodeObject *self, NodeObject *child);
  int Container_Insert(NodeObject *self, Py_ssize_t where, NodeObject *child);
  int Container_Replace(NodeObject *self, NodeObject *old, NodeObject *new);
  Py_ssize_t Container_Index(NodeObject *self, NodeObject *child);

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_CONTAINER_H */
