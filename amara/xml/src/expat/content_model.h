#ifndef EXPAT_CONTENT_MODEL_H
#define EXPAT_CONTENT_MODEL_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

#ifdef Expat_BUILDING_MODULE

  extern PyObject *ContentModel_FinalEvent;

  PyObject *ContentModel_New(void);

  int ContentModel_NewState(PyObject *self);

  int ContentModel_AddTransition(PyObject *self,
                                 PyObject *token,
                                 int from_state,
                                 int to_state);

  int ContentModel_AddEpsilonMove(PyObject *self,
                                  int from_state,
                                  int to_state);

  PyObject *ContentModel_Compile(PyObject *self);

  int _Expat_ContentModel_Init(PyObject *module);
  void _Expat_ContentModel_Fini(void);

#endif /* Expat_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* EXPAT_CONTENT_MODEL_H */
