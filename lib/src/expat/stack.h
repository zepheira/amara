#ifndef EXPAT_STACK_H
#define EXPAT_STACK_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

  typedef struct {
    int size;
    int allocated;
    PyObject **items;
  } Stack;

  Stack *Stack_New(void);
  void Stack_Del(Stack *stack);
  int Stack_Push(Stack *stack, PyObject *item);
  PyObject *Stack_Pop(Stack *stack);
  PyObject *Stack_Peek(Stack *stack);

#ifdef Py_DEBUG
#define Stack_PEEK Stack_Peek
#else
#define Stack_PEEK(stack) ((stack)->items[(stack)->size - 1])
#endif

#ifdef __cplusplus
}
#endif

#endif /* EXPAT_STACK_H */
