#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

/* nothing to see here */

/** Public C API *******************************************************/

/* Remove the preprocessor macros so that we can export the entry points. */

#undef Comment_New
CommentObject *Comment_New(PyObject *data)
{
  return CharacterData_New(CommentObject, &DomletteComment_Type, data);
}

/** Python Methods ****************************************************/

static PyMethodDef comment_methods[] = {
  { NULL }
};

/** Python Members *****************************************************/

static PyMethodDef comment_members[] = {
  { NULL }
};

/** Python Computed Members ********************************************/

static PyGetSetDef comment_getset[] = {
  { NULL }
};

/** Type Object ********************************************************/

static char comment_doc[] = "\
comment(data) -> comment object\n\
\n\
This interface represents the content of a comment, i.e., all the characters\n\
between the starting '<!--' and ending '-->'.";

PyTypeObject DomletteComment_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "comment",
  /* tp_basicsize      */ sizeof(CommentObject),
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
  /* tp_doc            */ (char *) comment_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) comment_methods,
  /* tp_members        */ (PyMemberDef *) comment_members,
  /* tp_getset         */ (PyGetSetDef *) comment_getset,
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

int DomletteComment_Init(PyObject *module)
{
  PyObject *dict, *value;

  DomletteComment_Type.tp_base = &DomletteCharacterData_Type;
  if (PyType_Ready(&DomletteComment_Type) < 0)
    return -1;

  dict = DomletteComment_Type.tp_dict;

  value = PyString_FromString("comment");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_type", value))
    return -1;
  Py_DECREF(value);
  /* add the "typecode" character for use with `xml_nodeid` */
  value = PyString_FromString("c");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_typecode", value) < 0)
    return -1;
  Py_DECREF(value);

  Py_INCREF(&DomletteComment_Type);
  return PyModule_AddObject(module, "comment",
                            (PyObject*) &DomletteComment_Type);
}

void DomletteComment_Fini(void)
{
  PyType_CLEAR(&DomletteComment_Type);
}
