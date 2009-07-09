#ifndef DOMLETTE_TEXT_H
#define DOMLETTE_TEXT_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "characterdata.h"

  typedef CharacterDataObject TextObject;

#define Text(op) ((TextObject *)(op))
#define Text_GET_VALUE CharacterData_GET_VALUE

#ifdef Domlette_BUILDING_MODULE

  extern PyTypeObject DomletteText_Type;

#define Text_Check(op) PyObject_TypeCheck((op), &DomletteText_Type)
#define Text_CheckExact(op) ((op)->ob_type == &DomletteText_Type)
#define Text_SET_VALUE CharacterData_SET_VALUE

  /* Module Methods */
  int DomletteText_Init(PyObject *module);
  void DomletteText_Fini(void);

  /* Text Methods */
  TextObject *Text_New(PyObject *data);
#define Text_New(data) \
  CharacterData_New(TextObject, &DomletteText_Type, (data))

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_TEXT_H */
