#ifndef DOMLETTE_ENTITY_H
#define DOMLETTE_ENTITY_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "node.h"

  typedef struct {
    Container_HEAD
    PyObject *documentURI;
    PyObject *publicId;
    PyObject *systemId;
    PyObject *unparsed_entities;
    PyObject *creationIndex;
  } EntityObject;

#define Entity(op) ((EntityObject *)(op))
#define Entity_GET_DOCUMENT_URI(op) (Entity(op)->documentURI)
#define Entity_GET_PUBLIC_ID(op) (Entity(op)->publicId)
#define Entity_GET_SYSTEM_ID(op) (Entity(op)->systemId)
#define Entity_GET_UNPARSED_ENTITIES(op) (Entity(op)->unparsed_entities)
#define Entity_GET_INDEX(op) (Entity(op)->creationIndex)

#ifdef Domlette_BUILDING_MODULE

#define Entity_SET_DOCUMENT_URI(op, v) ((Entity(op)->documentURI) = (v))
#define Entity_SET_PUBLIC_ID(op, v) ((Entity(op)->publicId) = (v))
#define Entity_SET_SYSTEM_ID(op, v) ((Entity(op)->systemId) = (v))

  extern PyTypeObject DomletteEntity_Type;

#define Entity_Check(op) PyObject_TypeCheck((op), &DomletteEntity_Type)
#define Entity_CheckExact(op) ((op)->ob_type == &DomletteEntity_Type)

  /* Module Methods */
  int DomletteEntity_Init(PyObject *module);
  void DomletteEntity_Fini(void);

  /* Entity Methods */
  EntityObject *Entity_New(PyObject *documentURI);

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_ENTITY_H */
