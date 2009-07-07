#include "Python.h"
#include "state_machine.h"
#include "debug.h"

typedef struct {
  StateId transitions[NUM_EVENTS];
  void *data;
  StateDataFree destruct;
} StateEntry;

struct StateTableStruct {
  /* The first member must be current so that the StateTable_GetState()
     macro works. */
  StateId current;
  size_t size;
  size_t allocated;
  StateEntry *states;
};

#ifdef DEBUG_STATE_TABLE
static char *event_names[NUM_EVENTS] = {
  "ERROR_EVENT",
  "PARSE_RESUME_EVENT",
  "START_ELEMENT_EVENT",
  "END_ELEMENT_EVENT",
  "CHARACTER_DATA_EVENT",
  "COMMENT_EVENT",
  "PI_EVENT",
  "START_NS_SCOPE_EVENT",
  "END_NS_SCOPE_EVENT",
  "XPTR_MATCH_EVENT",
  "XPTR_CLOSE_EVENT",
};
#endif


StateTable *StateTable_New(int size)
{
  StateTable *table = PyMem_New(StateTable, 1);
  if (table != NULL) {
    table->current = 0;
    table->size = 0;
    table->allocated = size;
    if ((table->states = PyMem_New(StateEntry, size)) == NULL) {
      PyErr_NoMemory();
      return NULL;
    }
    memset(table->states, 0, size * sizeof(StateEntry));
  }

  return table;
}

void StateTable_Del(StateTable *table)
{
  size_t i;
  StateEntry *state = table->states;

  for (i = 0; i < table->size; i++) {
    if (state->destruct != NULL)
      state->destruct(state->data);
    state++;
  }

  PyMem_Del(table->states);
  PyMem_Del(table);
}

int StateTable_AddState(StateTable *table, void *data, StateDataFree destruct)
{
  StateEntry *states;
  size_t new_allocated;
  size_t allocated, newsize;
  StateId newstate = (StateId)table->size;

#ifdef DEBUG_STATE_TABLE
  fprintf(stderr, "StateTable_AddState(%p) => %4d\n", table, newstate);
#endif

  /* Bypass realloc() when a previous overallocation is large enough
     to accommodate the newsize.
  */
  allocated = table->allocated;
  states = table->states;
  if (newstate >= (StateId)allocated) {
    /* This over-allocates proportional to the list size, making room
     * for additional growth.  The over-allocation is mild, but is
     * enough to give linear-time amortized behavior over a long
     * sequence of appends() in the presence of a poorly-performing
     * system realloc().
     * The growth pattern is:  0, 4, 8, 16, 25, 35, 46, 58, 72, 88, ...
     */
    newsize = newstate + 1;
    new_allocated = (newsize >> 3) + (newsize < 9 ? 3 : 6) + newsize;
    if (new_allocated <= ((~(size_t)0) / sizeof(StateEntry)))
      PyMem_Resize(states, StateEntry, new_allocated);
    else
      states = NULL;
    if (states == NULL) {
      PyErr_NoMemory();
      return -1;
    }
    memset(states + allocated, 0,
           (new_allocated - allocated) * sizeof(StateEntry));

    table->allocated = new_allocated;
    table->states = states;
    table->size = newsize;
  } else if (newstate >= (StateId)table->size) {
    table->size = newstate + 1;
  }

  /* initialize the new state */
  memset(table->states[newstate].transitions, 0, sizeof(StateId) * NUM_EVENTS);
  table->states[newstate].data = data;
  table->states[newstate].destruct = destruct;

  return newstate;
}


int StateTable_SetTransition(StateTable *table, StateId from, EventId event,
                             StateId to)
{
  StateEntry *states = table->states;

#ifdef DEBUG_STATE_TABLE
  fprintf(stderr, "StateTable_SetTransition(%p, %4d, %20s, %4d)\n",
          table, from, event_names[event], to);
#endif
  if (from > (StateId)table->size) {
    PyErr_Format(PyExc_RuntimeError, "Initial state %d is undefined", from);
    return -1;
  }
  else if (to > (StateId)table->size) {
    PyErr_Format(PyExc_RuntimeError, "Final state %d is undefined", to);
    return -1;
  }

  /* blindly replace existing entry in transitions table */
  states[from].transitions[event] = to;

  return 0;
}


StateId StateTable_Transit(StateTable *table, EventId event)
{
  StateId new_state_id;
  StateId current = table->current;
  StateEntry *states = table->states;

  /* find the state this event transitions to starting from the end */
  new_state_id = states[current].transitions[event];

#ifdef DEBUG_STATE_TABLE
  fprintf(stderr, "StateTable_Transit(%p, %s): from %4d to %4d\n",
          table, event_names[event], current, new_state_id);
#endif

  table->current = new_state_id;
  return new_state_id;
}


void *StateTable_GetStateData(StateTable *table, StateId state)
{
  if (state < 0 || state > (StateId)table->size) {
    PyErr_Format(PyExc_ValueError, "state %d out of bounds", state);
    return NULL;
  }

  return table->states[state].data;
}
