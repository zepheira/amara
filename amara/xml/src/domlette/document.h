#ifndef DOMLETTE_DOCUMENT_H
#define DOMLETTE_DOCUMENT_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "node.h"

  typedef struct {
    ContainerNode_HEAD
    PyObject *documentURI;
    PyObject *publicId;
    PyObject *systemId;
    PyObject *unparsedEntities;
    PyObject *creationIndex;
  } DocumentObject;

#define Document(op) ((DocumentObject *)(op))
#define Document_GET_DOCUMENT_URI(op) (Document(op)->documentURI)
#define Document_GET_PUBLIC_ID(op) (Document(op)->publicId)
#define Document_GET_SYSTEM_ID(op) (Document(op)->systemId)
#define Document_GET_INDEX(op) (Document(op)->creationIndex)

#ifdef Domlette_BUILDING_MODULE

  extern PyTypeObject DomletteDocument_Type;

#define Document_Check(op) PyObject_TypeCheck((op), &DomletteDocument_Type)
#define Document_CheckExact(op) ((op)->ob_type == &DomletteDocument_Type)

  /* Module Methods */
  int DomletteDocument_Init(PyObject *module);
  void DomletteDocument_Fini(void);

  /* Document Methods */
  DocumentObject *Document_New(PyObject *documentURI);

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_DOCUMENT_H */
