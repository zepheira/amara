/***********************************************************************
 * amara/xslt/src/xslt_tree.c
 ***********************************************************************/

static char module_doc[] = "\
Node classes for the stylesheet tree\n\
";

//#include "stylesheet_reader.h"
#include "xslt_node.h"
#include "xslt_root.h"
#include "xslt_element.h"
#include "xslt_text.h"

#define MODULE_NAME "amara.xslt.tree._tree"
#define MODULE_INITFUNC init_tree

static char newobj_doc[] = "helper for pickle protocols 0 and 1";

static PyObject *xslt_newobj(PyObject *module, PyObject *args)
{
  PyObject *cls, *newargs, *obj;
  PyTypeObject *type;
  Py_ssize_t n;

  n = PyTuple_Size(args);
  if (n < 1) {
    PyErr_SetString(PyExc_TypeError, "__newobj__ takes at least 1 argument");
    return NULL;
  }

  cls = PyTuple_GET_ITEM(args, 0);
  if (!PyType_Check(cls)) {
    PyErr_Format(PyExc_TypeError,
                 "__newobj__ argument 1 must be %.50s, not %.50s",
                 PyType_Type.tp_name,
                 cls == Py_None ? "None" : cls->ob_type->tp_name);
    return NULL;
  }

  type = (PyTypeObject *) cls;
  if (type->tp_new == NULL) {
    PyErr_Format(PyExc_TypeError, "type '%.100s' has NULL tp_new slot",
                 type->tp_name);
    return NULL;
  }

  /* create the argument tuple for the __new__ method */
  newargs = PyTuple_New(n - 1);
  if (newargs == NULL)
    return NULL;
  while (n > 1) {
    PyObject *item = PyTuple_GET_ITEM(args, n--);
    Py_INCREF(item);
    PyTuple_SET_ITEM(newargs, n, item);
  }

  /* call __new__ */
  obj = type->tp_new(type, newargs, NULL);
  Py_DECREF(newargs);

  return obj;
}

static struct PyMethodDef module_methods[] = {
  { "__newobj__", xslt_newobj, METH_VARARGS, newobj_doc },
  { NULL }
};

static void module_dealloc(void *arg)
{
  //StylesheetReader_Fini();
  XsltNode_Fini();
  XsltRoot_Fini();
  XsltElement_Fini();
  XsltText_Fini();
}

PyMODINIT_FUNC MODULE_INITFUNC(void)
{
  PyObject *module, *cobj;

  module = Py_InitModule3(MODULE_NAME, module_methods, module_doc);
  if (module == NULL) return;

  /* initialize the sub-components */
  //if (StylesheetReader_Init(module) == -1) return;
  if (XsltNode_Init(module) == -1) return;
  if (XsltRoot_Init(module) == -1) return;
  if (XsltElement_Init(module) == -1) return;
  if (XsltText_Init(module) == -1) return;

  /* Trick to enable module finalization */
  cobj = PyCObject_FromVoidPtr(NULL, module_dealloc);
  if (cobj) {
    PyModule_AddObject(module, "CAPI", cobj);
  }
  return;
}
