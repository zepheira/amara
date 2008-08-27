#ifndef DOMLETTE_COMMENT_H
#define DOMLETTE_COMMENT_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "characterdata.h"

  typedef CharacterDataObject CommentObject;

#define Comment_GET_DATA(op) CharacterData_NODE_VALUE(op)
#define Comment_SET_DATA(op, v) (Comment_GET_DATA(op) = (v))

#ifdef Domlette_BUILDING_MODULE

  extern PyTypeObject DomletteComment_Type;

#define Comment_Check(op) PyObject_TypeCheck((op), &DomletteComment_Type)
#define Comment_CheckExact(op) ((op)->ob_type == &DomletteComment_Type)

  /* Module Methods */
  int DomletteComment_Init(PyObject *module);
  void DomletteComment_Fini(void);

  /* Comment Methods */
  CommentObject *Comment_New(PyObject *data);
#define Comment_New(data) \
  CharacterData_New(CommentObject, &DomletteComment_Type, (data))

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_COMMENT_H */
