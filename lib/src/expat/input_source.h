#ifndef EXPAT_INPUT_SOURCE_H
#define EXPAT_INPUT_SOURCE_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

  typedef struct {
    PyObject_HEAD
    PyObject *byte_stream;
    PyObject *char_stream;
    PyObject *string_data;
    PyObject *system_id;
    PyObject *public_id;
    PyObject *base_uri;
    PyObject *encoding;
  } InputSourceObject;

#define InputSource_GET_BYTE_STREAM(op) \
  (((InputSourceObject *)(op))->byte_stream)
#define InputSource_GET_CHARACTER_STREAM(op) \
  (((InputSourceObject *)(op))->char_stream)
#define InputSource_GET_STRING_DATA(op) \
  (((InputSourceObject *)(op))->string_data)
#define InputSource_GET_SYSTEM_ID(op) \
  (((InputSourceObject *)(op))->system_id)
#define InputSource_GET_PUBLIC_ID(op) \
  (((InputSourceObject *)(op))->public_id)
#define InputSource_GET_BASE_URI(op) \
  (((InputSourceObject *)(op))->base_uri)
#define InputSource_GET_ENCODING(op) \
  (((InputSourceObject *)(op))->encoding)

#ifdef Expat_BUILDING_MODULE

  extern PyTypeObject InputSource_Type;
#define InputSource_Check(op) PyObject_TypeCheck((op), &InputSource_Type)

  int _Expat_InputSource_Init(PyObject *module);
  void _Expat_InputSource_Fini(void);

#endif /* Expat_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* EXPAT_INPUT_SOURCE_H */
