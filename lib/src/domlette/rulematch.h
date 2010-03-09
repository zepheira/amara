/* rulematch.h */

#ifndef DOMLETTE_RULEMATCH_H
#define DOMLETTE_RULEMATCH_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

  typedef struct RuleMatchObject RuleMatchObject;
  extern int RuleMatch_Init(void);
  extern RuleMatchObject *RuleMatchObject_New(PyObject *contenthandler);
  extern void RuleMatchObject_Del(RuleMatchObject *);

  extern int RuleMatch_StartElement(RuleMatchObject *self,
				       PyObject *node,
				       ExpatName *name,
				       ExpatAttribute atts[],
				       size_t natts);

  extern int RuleMatch_EndElement(RuleMatchObject *self, 
				     PyObject *node,
				     ExpatName *name);
  extern int RuleMatch_StartDocument(RuleMatchObject *self,
					PyObject *node);
  extern int RuleMatch_ProcessingInstruction(RuleMatchObject *self,
						PyObject *node,
						PyObject *target,
						PyObject *data);


#ifdef __cpluscplus
}
#endif
#endif
