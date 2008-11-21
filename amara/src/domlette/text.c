#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

/* nothing to see here */

/** Public C API *******************************************************/

/* Remove the preprocessor macros so that we can export the entry points. */

#undef Text_New
TextObject *Text_New(PyObject *data)
{
  return CharacterData_New(TextObject, &DomletteText_Type, data);
}

/** Python Methods ****************************************************/

static PyMethodDef text_methods[] = {
  { NULL }
};

/** Python Members *****************************************************/

static PyMethodDef text_members[] = {
  { NULL }
};

/** Python Computed Members ********************************************/

static PyGetSetDef text_getset[] = {
  { NULL }
};

/** Type Object ********************************************************/

static char text_doc[] = "\
text(data) -> text object\n\
\n\
The `text` interface represents the contents of a text node.";

PyTypeObject DomletteText_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "text",
  /* tp_basicsize      */ sizeof(TextObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) 0,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) 0,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) 0,
  /* tp_as_mapping     */ (PyMappingMethods *) 0,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) 0,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT |
                           Py_TPFLAGS_BASETYPE),
  /* tp_doc            */ (char *) text_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) text_methods,
  /* tp_members        */ (PyMemberDef *) text_members,
  /* tp_getset         */ (PyGetSetDef *) text_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) 0,
  /* tp_free           */ 0,
};

/** Module Interface **************************************************/

int DomletteText_Init(PyObject *module)
{
  PyObject *dict, *value;

  DomletteText_Type.tp_base = &DomletteCharacterData_Type;
  if (PyType_Ready(&DomletteText_Type) < 0)
    return -1;

  dict = DomletteText_Type.tp_dict;

  value = PyString_FromString("text");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_type", value))
    return -1;
  Py_DECREF(value);
  /* add the "typecode" character for use with `xml_nodeid` */
  value = PyString_FromString("t");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_typecode", value) < 0)
    return -1;
  Py_DECREF(value);

  if (PyDict_SetItemString(dict, "xsltOutputEscaping", Py_True))
    return -1;

  Py_INCREF(&DomletteText_Type);
  return PyModule_AddObject(module, "text", (PyObject*)&DomletteText_Type);
}

void DomletteText_Fini(void)
{
  PyType_CLEAR(&DomletteText_Type);
}
