#include "stack.h"

#define Stack_INITIAL_SIZE 10

Stack *Stack_New(void)
{
  Stack *stack = PyMem_New(Stack, 1);
  if (stack != NULL) {
    stack->size = 0;
    stack->allocated = Stack_INITIAL_SIZE;
    if ((stack->items = PyMem_New(PyObject *, Stack_INITIAL_SIZE)) == NULL) {
      PyErr_NoMemory();
      PyMem_Free(stack);
      return NULL;
    }
  }
  return stack;
}

void Stack_Del(Stack *stack)
{
  while (stack->size-- > 0) {
    Py_DECREF(stack->items[stack->size]);
  }
  PyMem_Free(stack->items);
  PyMem_Free(stack);
}

int Stack_Push(Stack *stack, PyObject *item)
{
  int allocated, new_allocated;
  int new_size = stack->size + 1;
  PyObject **items;

  /* Bypass realloc() when a previous overallocation is large enough
     to accommodate the newsize.
  */
  allocated = stack->allocated;
  items = stack->items;
  if (new_size >= allocated) {
    /* This over-allocates proportional to the list size, making room
     * for additional growth.  The over-allocation is mild, but is
     * enough to give linear-time amortized behavior over a long
     * sequence of appends() in the presence of a poorly-performing
     * system realloc().
     * The growth pattern is:  0, 4, 8, 16, 25, 35, 46, 58, 72, 88, ...
     */
    new_allocated = (new_size >> 3) + (new_size < 9 ? 3 : 6) + new_size;
    if (PyMem_Resize(items, PyObject *, new_allocated) == NULL) {
      PyErr_NoMemory();
      return -1;
    }
    stack->allocated = new_allocated;
    stack->items = items;
  }
  Py_INCREF(item);
  stack->items[stack->size] = item;
  stack->size = new_size;

  return 0;
}

PyObject *Stack_Pop(Stack *stack)
{
  if (stack->size == 0) {
    return NULL;
  }

  stack->size--;
  return stack->items[stack->size];
}

PyObject *Stack_Peek(Stack *stack)
{
  assert(stack->size > 0);
  return stack->items[stack->size - 1];
}


