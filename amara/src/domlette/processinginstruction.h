#ifndef DOMLETTE_PROCESSING_INSTRUCTION_H
#define DOMLETTE_PROCESSING_INSTRUCTION_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "node.h"

  typedef struct {
    Node_HEAD
    PyObject *pi_target;
    PyObject *pi_data;
  } ProcessingInstructionObject;

#define ProcessingInstruction(op) ((ProcessingInstructionObject *)(op))
#define ProcessingInstruction_GET_TARGET(op) \
  (ProcessingInstruction(op)->pi_target)
#define ProcessingInstruction_GET_DATA(op) \
  (ProcessingInstruction(op)->pi_data)

#ifdef Domlette_BUILDING_MODULE

  extern PyTypeObject DomletteProcessingInstruction_Type;

#define ProcessingInstruction_Check(op) \
  PyObject_TypeCheck(op, &DomletteProcessingInstruction_Type)
#define ProcessingInstruction_CheckExact(op) \
  ((op)->ob_type == &DomletteProcessingInstruction_Type)

  /* Module Methods */
  int DomletteProcessingInstruction_Init(PyObject *module);
  void DomletteProcessingInstruction_Fini(void);

  /* ProcessingInstruction Methods */
  ProcessingInstructionObject *
  ProcessingInstruction_New(PyObject *target, PyObject *data);

  ProcessingInstructionObject *
  ProcessingInstruction_Copy(PyObject *self, int deep);

#endif /* Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_PROCESSING_INSTRUCTION_H */
