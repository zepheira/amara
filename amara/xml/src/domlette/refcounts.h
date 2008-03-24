#ifndef DOMLETTE_REFCOUNTS_H
#define DOMLETTE_REFCOUNTS_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

  int test_refcounts(PyObject *tester, PyObject *document);

#ifdef __cplusplus
}
#endif

#endif /* def DOMLETTE_REFCOUNTS_H */
