#ifndef DOMLETTE_CHARACTERDATA_H
#define DOMLETTE_CHARACTERDATA_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "node.h"

  typedef struct {
    Node_HEAD
    PyObject *value;
  } CharacterDataObject;

#define CharacterData(op) ((CharacterDataObject *)(op))
#define CharacterData_GET_VALUE(op) (CharacterData(op)->value)

#ifdef Domlette_BUILDING_MODULE

  extern PyTypeObject DomletteCharacterData_Type;

#define CharacterData_Check(op) \
  PyObject_TypeCheck((op), &DomletteCharacterData_Type)
#define CharacterData_CheckExact(op) \
  ((op)->ob_type, &DomletteCharacterData_Type)
#define CharacterData_SET_VALUE(op, v) (CharacterData_GET_VALUE(op) = (v))

  /* Module Methods */
  int DomletteCharacterData_Init(PyObject *module);
  void DomletteCharacterData_Fini(void);

  /* CharacterData Methods */
  CharacterDataObject *_CharacterData_New(PyTypeObject *type, PyObject *data);
#define CharacterData_New(type, typeobj, data) \
  ((type *) _CharacterData_New((typeobj), (data)))

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_CHARACTERDATA_H */
