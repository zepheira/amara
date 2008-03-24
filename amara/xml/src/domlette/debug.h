#ifndef DOMLETTE_DEBUG_H
#define DOMLETTE_DEBUG_H

#ifdef __cplusplus
extern "C" {
#endif

/* Use these defines to control different aspects of debugging */

/* Debug the append child calls */
/*#define DEBUG_NODE_APPEND_CHILD */

/* Debug the remove child calls */
/*#define DEBUG_NODE_REMOVE_CHILD */

/* Debug the replace child calls */
/*#define DEBUG_NODE_REPLACE_CHILD */

/* Debug the insert before calls */
/*#define DEBUG_NODE_INSERT_BEFORE */

/* Debug the normalize calls */
/*#define DEBUG_NODE_NORMALIZE */

/* Debug the creation and destruction of nodes */
/*#define DEBUG_NODE_CREATION */

/* Debug the parser calls */
/*#define DEBUG_PARSER */

/* Debug the state table calls */
/*#define DEBUG_STATE_TABLE */

/* Debug the memory (de)allocations */
/*#define DEBUG_MEMORY */

/* Enable all debugging flags */
/*#define DEBUG_ALL */

#ifdef DEBUG_ALL
#define DEBUG_NODE_APPEND_CHILD
#define DEBUG_NODE_REMOVE_CHILD
#define DEBUG_NODE_INSERT_BEFORE
#define DEBUG_NODE_NORMALIZE
#define DEBUG_NODE_CREATION
#define DEBUG_PARSER
#define DEBUG_STATE_TABLE
#define DEBUG_MEMORY
#endif

#if defined(Py_DEBUG) || defined(DEBUG_MEMORY)
#define PyType_CLEAR(op)                                          \
  do {                                                            \
    PyObject_ClearWeakRefs((PyObject *)(op));                     \
    Py_XDECREF(((PyTypeObject *)(op))->tp_dict);                  \
    Py_XDECREF(((PyTypeObject *)(op))->tp_bases);                 \
    Py_XDECREF(((PyTypeObject *)(op))->tp_mro);                   \
    Py_XDECREF(((PyTypeObject *)(op))->tp_cache);                 \
    Py_XDECREF(((PyTypeObject *)(op))->tp_subclasses);            \
    Py_XDECREF(((PyTypeObject *)(op))->tp_weaklist);              \
  } while(0)
#else
#define PyType_CLEAR(op)
#endif

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_DEBUG_H */
