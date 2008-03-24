#ifndef DOMLETTE_READER_H
#define DOMLETTE_READER_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"

  extern char Parse_doc[];
  PyObject *Domlette_Parse(PyObject *self, PyObject *args, PyObject *kw);

  extern char NonvalParse_doc[];
  PyObject *Domlette_NonvalParse(PyObject *self, PyObject *args, PyObject *kw);

  extern char ValParse_doc[];
  PyObject *Domlette_ValParse(PyObject *self, PyObject *args, PyObject *kw);

  extern char ParseFragment_doc[];
  PyObject *Domlette_ParseFragment(PyObject *self, PyObject *args,
                                   PyObject *kw);

  int DomletteReader_Init(PyObject *module);
  void DomletteReader_Fini(void);

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_READER_H */
