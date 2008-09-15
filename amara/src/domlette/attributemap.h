#ifndef DOMLETTE_ATTRIBUTEMAP_H
#define DOMLETTE_ATTRIBUTEMAP_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "element.h"
#include "attr.h"

/* AttributeMap_MINSIZE is the minimum size of a dictionary.  This many slots
 * are allocated directly in the dict object (in the ma_smalltable member).
 * It must be a power of 2, and at least 4.  8 allows dicts with no more
 * than 5 active entries to live in `nm_smalltable` (and so avoid an
 * additional malloc); instrumentation suggested this suffices for the
 * majority of dicts (consisting mostly of usually-small instance dicts and
 * usually-small dicts created to pass keyword arguments).
 */
#define AttributeMap_MINSIZE 8

  typedef struct {
    PyObject_HEAD
    /* The number of inuse entries in the table. */
    Py_ssize_t nm_used;
    /* The table contains `nm_mask` + 1 slots, and that's a power of 2.
     * We store the mask instead of the size because the mask is more
     * frequently needed.
     */
    Py_ssize_t nm_mask;
    /* `nm_table` points to `nm_smalltable` for small tables, else to
     * additional malloc'ed memory.  `nm_table` is never NULL!  This rule
     * saves repeated runtime null-tests in the workhorse getitem and
     * setitem calls.
     */
    AttrObject **nm_table;
    ElementObject *nm_owner;
    AttrObject *nm_smalltable[AttributeMap_MINSIZE];
  } AttributeMapObject;

#define AttributeMap_GET_SIZE(op) (((AttributeMapObject *)(op))->nm_used)

#ifdef Domlette_BUILDING_MODULE

  PyObject *AttributeMap_New(ElementObject *owner);

  Py_ssize_t AttributeMap_GetHash(PyObject *namespace, PyObject *name);

  AttrObject *AttributeMap_GetNode(PyObject *self, PyObject *namespace,
                                   PyObject *name);

  int AttributeMap_SetNode(PyObject *self, AttrObject *node);

  AttrObject *AttributeMap_Next(PyObject *self, Py_ssize_t *pos);

  /* Module Methods */
  int DomletteAttributeMap_Init(PyObject *module);
  void DomletteAttributeMap_Fini(void);

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_ATTRIBUTEMAP_H */
