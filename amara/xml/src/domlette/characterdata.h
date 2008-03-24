#ifndef DOMLETTE_CHARACTERDATA_H
#define DOMLETTE_CHARACTERDATA_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "node.h"

  typedef struct {
    Node_HEAD
    PyObject *nodeValue;
  } CharacterDataObject;

#define CharacterData(op) ((CharacterDataObject *)(op))
#define CharacterData_GET_NODE_VALUE(op) (CharacterData(op)->nodeValue)

#ifdef Domlette_BUILDING_MODULE

  extern PyTypeObject DomletteCharacterData_Type;

#define CharacterData_Check(op) \
  PyObject_TypeCheck((op), &DomletteCharacterData_Type)
#define CharacterData_CheckExact(op) \
  ((op)->ob_type, &DomletteCharacterData_Type)

  /* Module Methods */
  int DomletteCharacterData_Init(PyObject *module);
  void DomletteCharacterData_Fini(void);

  /* CharacterData Methods */
  CharacterDataObject *_CharacterData_New(PyTypeObject *type, PyObject *data);
#define CharacterData_New(type, typeobj, data) \
  ((type *) _CharacterData_New((typeobj), (data)))

  CharacterDataObject *_CharacterData_CloneNode(PyTypeObject *type,
                                                PyObject *node, int deep);
#define CharacterData_CloneNode(type, typeobj, node, deep) \
  ((type *) _CharacterData_CloneNode((typeobj), (node), (deep)))

  PyObject *CharacterData_SubstringData(CharacterDataObject *node,
                                        Py_ssize_t offset, Py_ssize_t count);

  int CharacterData_AppendData(CharacterDataObject *node, PyObject *arg);

  int CharacterData_InsertData(CharacterDataObject *node, Py_ssize_t offset,
                               PyObject *arg);

  int CharacterData_DeleteData(CharacterDataObject *node, Py_ssize_t offset,
                               Py_ssize_t count);

  int CharacterData_ReplaceData(CharacterDataObject *node, Py_ssize_t offset,
                                Py_ssize_t count,PyObject *arg);

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_CHARACTERDATA_H */
