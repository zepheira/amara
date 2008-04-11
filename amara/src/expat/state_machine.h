#ifndef STATE_MACHINE_H
#define STATE_MACHINE_H

#ifdef __cplusplus
extern "C" {
#endif

/* States */

#define ERROR_STATE 0
#define START_STATE 1

/* Events */

  typedef enum {
    ERROR_EVENT,
    PARSE_RESUME_EVENT,
    START_ELEMENT_EVENT,
    END_ELEMENT_EVENT,
    CHARACTER_DATA_EVENT,
    COMMENT_EVENT,
    PI_EVENT,
    START_NS_SCOPE_EVENT,
    END_NS_SCOPE_EVENT,
    FILTER_MATCH_EVENT,
    FILTER_CLOSE_EVENT,
    NUM_EVENTS,
  } EventId;

  struct StateTableStruct;
  typedef struct StateTableStruct StateTable;

  typedef int StateId;

  typedef void (*StateDataFree)(void *params);

  StateTable *StateTable_New(int size);
  void StateTable_Del(StateTable *table);

#define StateTable_Reset(table) ((*(StateId *)(table)) = 0)

  int StateTable_AddState(StateTable *table, void *data,
                          StateDataFree destruct);

  int StateTable_SetTransition(StateTable *table, StateId from, EventId event,
                               StateId next);

  /* Returns the new state id */
  StateId StateTable_Transit(StateTable *table, EventId event);

#define StateTable_GetState(table) (*(StateId *)(table))

  void *StateTable_GetStateData(StateTable *table, StateId state);

#ifdef __cplusplus
}
#endif

#endif /* STATE_MACHINE_H */
