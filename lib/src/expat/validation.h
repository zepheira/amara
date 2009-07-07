#ifndef EXPAT_VALIDATION_H
#define EXPAT_VALIDATION_H

#include "Python.h"

#ifdef __cplusplus
extern "C" {
#endif

  typedef enum {
    ATTRIBUTE_TYPE_CDATA,
    ATTRIBUTE_TYPE_ID,
    ATTRIBUTE_TYPE_IDREF,
    ATTRIBUTE_TYPE_IDREFS,
    ATTRIBUTE_TYPE_ENTITY,
    ATTRIBUTE_TYPE_ENTITIES,
    ATTRIBUTE_TYPE_NMTOKEN,
    ATTRIBUTE_TYPE_NMTOKENS,
    ATTRIBUTE_TYPE_NOTATION,
    ATTRIBUTE_TYPE_ENUMERATION,
  } AttributeType;

  typedef enum {
    ATTRIBUTE_DECL_DEFAULT,
    ATTRIBUTE_DECL_IMPLIED,
    ATTRIBUTE_DECL_REQUIRED,
    ATTRIBUTE_DECL_FIXED,
  } AttributeDecl;

  typedef struct {
    PyObject_HEAD
    PyObject *name;
    AttributeType type;
    AttributeDecl decl;
    PyObject *allowed_values;
    PyObject *value;
  } AttributeTypeObject;

#define AttributeType_GET_NAME(op) \
  (((AttributeTypeObject *)(op))->name)
#define AttributeType_GET_TYPE(op) \
  (((AttributeTypeObject *)(op))->type)
#define AttributeType_GET_DECL(op) \
  (((AttributeTypeObject *)(op))->decl)
#define AttributeType_GET_ALLOWED_VALUES(op) \
  (((AttributeTypeObject *)(op))->allowed_values)
#define AttributeType_GET_VALUE(op) \
  (((AttributeTypeObject *)(op))->value)

  typedef struct {
    PyObject_HEAD
    PyObject *name;
    PyObject *attributes;         /* mapping of name to AttributeType */
    PyObject *content_model;      /* list of states */
  } ElementTypeObject;

#define ElementType_GET_NAME(op) \
  (((ElementTypeObject *)(op))->name)
#define ElementType_GET_MODEL(op) \
  (((ElementTypeObject *)(op))->content_model)
#define ElementType_GET_ATTRIBUTES(op) \
  (((ElementTypeObject *)(op))->attributes)
#define ElementType_GET_ATTRIBUTE(op, name) \
  PyDict_GetItem(ElementType_GET_ATTRIBUTES(op), (name))

#ifdef Expat_BUILDING_MODULE

  struct ValidatorStruct;
  typedef struct ValidatorStruct ValidatorObject;

  /** ElementType **/

  PyObject *ElementType_New(PyObject *name, PyObject *model);

  int ElementType_SetContentModel(PyObject *self, PyObject *model);

  int ElementType_AddAttribute(PyObject *self,
                               PyObject *name,
                               AttributeType type,
                               AttributeDecl decl,
                               PyObject *allowedValues,
                               PyObject *defaultValue);

  /** Validator **/

  PyObject *Validator_New(void);

  int Validator_AddElementType(PyObject *self, PyObject *elementType);

  PyObject *Validator_GetElementType(PyObject *self, PyObject *name);

  PyObject *Validator_GetCurrentElementType(PyObject *self);

  int Validator_ValidateEvent(PyObject *self, PyObject *event);

  int Validator_CheckEvent(PyObject *self, PyObject *event);

  int Validator_StartElement(PyObject *self, PyObject *name);

  int Validator_EndElement(PyObject *self);

  /** Module **/

  int ExpatValidation_Init(PyObject *module);
  void ExpatValidation_Fini(void);

#endif /* Expat_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* EXPAT_VALIDATION_H */
