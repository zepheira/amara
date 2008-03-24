#ifndef DOMLETTE_EXPAT_FILTER_H
#define DOMLETTE_EXPAT_FILTER_H

#ifdef __cplusplus
extern "C" {
#endif

  #include "Python.h"
  #include "state_machine.h"

  struct FilterCriterionStruct;
  typedef struct FilterCriterionStruct FilterCriterion;

  typedef struct FilterContext {
    struct FilterContext *next;
    int matched;
    int depth;
    StateTable *state_table;
    StateId accepting;
    ExpatFilter *handlers;
  } FilterContext;

  typedef enum {
    ELEMENT_ID,           /* Shorthand and element() scheme */
    ELEMENT_COUNT,        /* element() and xpointer() scheme */
    ELEMENT_MATCH,        /* xpointer() scheme */
    ATTRIBUTE_MATCH,      /* xpointer() scheme */
  } FilterCriterionType;

  FilterCriterion *FilterCriterion_New(FilterCriterionType type, ...);
  void FilterCriterion_Del(FilterCriterion *criterion);

  /* FilterCriterion_FromSeq creates a new FilterCriterion object from an
     iterable object producing iterable objects. */
  FilterCriterion *FilterCriterion_FromSeq(PyObject *seq);

  FilterContext *FilterContext_New(int size);
  void FilterContext_Del(FilterContext *context);

  FilterContext *FilterContext_FromSeq(PyObject *seq);

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_EXPAT_FILTER_H */
