#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

typedef struct {
  PyObject_HEAD
  PyObject *nodes;
} NamedNodeMapObject;

/** Public C API ******************************************************/

/** Python Methods ****************************************************/

static char namednodemap_getNamedItemNS_doc[] = "\
getNamedItemNS(namespaceURI, localName) -> Node\n\
\n\
Retrieves a node specified by local name and namespace URI or None \
if they do not identify a node in this map.";

static PyObject *namednodemap_getNamedItemNS(NamedNodeMapObject *self,
                                             PyObject *args)
{
  PyObject *namespaceURI, *localName, *node;

  if (!PyArg_ParseTuple(args, "OO:getNamedItemNS", &namespaceURI, &localName))
    return NULL;

  /* Simply reuse 'args' as it is already a tuple in proper form. */
  if ((node = PyDict_GetItem(self->nodes, args)) == NULL) {
    node = Py_None;
  }
  Py_INCREF(node);
  return node;
}

static char namednodemap_item_doc[] = "\
item(index) -> Node\n\
\n\
Returns the node specified by index. If index is greater than or equal \
to the number of nodes in this map, this returns None.";

static PyObject *namednodemap_item(NamedNodeMapObject *self, PyObject *arg)
{
  Py_ssize_t index, pos;
  PyObject *key, *node;

  if ((index = PyInt_AsLong(arg)) < 0 && PyErr_Occurred()) {
    return NULL;
  }

  if (index <= 0 || index > PyDict_Size(self->nodes)) {
    /* The index is out of bounds for this map, return None. */
    node = Py_None;
  } else {
    /* Walk the dict until the specified index is reached. */
    pos = 0;
    while (PyDict_Next(self->nodes, &pos, &key, &node) && --index > 0);
  }
  Py_INCREF(node);
  return node;
}

static char namednodemap_has_key_doc[] =
"D.has_key(k) -> 1 if D has a key k, else 0";

static PyObject *namednodemap_has_key(NamedNodeMapObject *self,
                                      PyObject *key)
{
  PyObject *result;

  if (PyDict_GetItem(self->nodes, key)) {
    result = Py_True;
  } else {
    result = Py_False;
  }
  Py_INCREF(result);
  return result;
}

static char namednodemap_get_doc[] =
"D.get(k[,d]) -> D[k] if D.has_key(k), else d.  d defaults to None.";

static PyObject *namednodemap_get(NamedNodeMapObject *self, PyObject *args)
{
  PyObject *key, *def=Py_None;

  if (!PyArg_ParseTuple(args, "O|O:get", &key, &def))
    return NULL;
  return PyObject_CallMethod(self->nodes, "get", "(OO)", key, def);
}

static char namednodemap_keys_doc[] =
"D.keys() -> list of D's keys";

static PyObject *namednodemap_keys(NamedNodeMapObject *self)
{
  return PyDict_Keys(self->nodes);
}

static char namednodemap_values_doc[] =
"D.values() -> list of D's values";

static PyObject *namednodemap_values(NamedNodeMapObject *self)
{
  return PyDict_Values(self->nodes);
}

static char namednodemap_items_doc[] =
  "D.items() -> list of D's (key, value) pairs, as 2-tuples";

static PyObject *namednodemap_items(NamedNodeMapObject *self)
{
  return PyDict_Items(self->nodes);
}

static char namednodemap_iterkeys_doc[] =
"D.iterkeys() -> an iterator over the keys of D";

static PyObject *namednodemap_iterkeys(NamedNodeMapObject *self)
{
  return PyObject_CallMethod(self->nodes, "iterkeys", NULL);
}

static char namednodemap_itervalues_doc[] =
"D.itervalues() -> an iterator over the values of D";

static PyObject *namednodemap_itervalues(NamedNodeMapObject *self)
{
  return PyObject_CallMethod(self->nodes, "itervalues", NULL);
}

static char namednodemap_iteritems_doc[] =
"D.iteritems() -> an iterator over the (key, value) items of D";

static PyObject *namednodemap_iteritems(NamedNodeMapObject *self)
{
  return PyObject_CallMethod(self->nodes, "iteritems", NULL);
}

static char namednodemap_copy_doc[] =
"D.copy() -> a shallow copy of D";

static PyObject *namednodemap_copy(NamedNodeMapObject *self)
{
  return PyDict_Copy(self->nodes);
}

#define NamedNodeMap_METHOD(NAME, FLAGS)             \
  { #NAME, (PyCFunction) namednodemap_##NAME, FLAGS, \
      namednodemap_##NAME##_doc }

static PyMethodDef namednodemap_methods[] = {
  NamedNodeMap_METHOD(getNamedItemNS, METH_VARARGS),
  NamedNodeMap_METHOD(item, METH_O),
  /* Python Mapping Interface */
  NamedNodeMap_METHOD(has_key, METH_O),
  NamedNodeMap_METHOD(get, METH_VARARGS),
  NamedNodeMap_METHOD(keys, METH_NOARGS),
  NamedNodeMap_METHOD(values, METH_NOARGS),
  NamedNodeMap_METHOD(items, METH_NOARGS),
  NamedNodeMap_METHOD(iterkeys, METH_NOARGS),
  NamedNodeMap_METHOD(itervalues, METH_NOARGS),
  NamedNodeMap_METHOD(iteritems, METH_NOARGS),
  NamedNodeMap_METHOD(copy, METH_NOARGS),
  { NULL }
};

static Py_ssize_t namednodemap_length(PyObject *self)
{
  return PyDict_Size(((NamedNodeMapObject *)self)->nodes);
}

static PyObject *namednodemap_subscript(NamedNodeMapObject *self,
                                        PyObject *key)
{
  PyObject *value = PyDict_GetItem(self->nodes, key);
  if (value == NULL) {
    PyErr_SetObject(PyExc_KeyError, value);
  } else {
    Py_INCREF(value);
  }
  return value;
}

static PyMappingMethods namednodemap_as_mapping = {
  /* mp_length        */ namednodemap_length,
  /* mp_subscript     */ (binaryfunc) namednodemap_subscript,
  /* mp_ass_subscript */ (objobjargproc) 0,
};

static int namednodemap_contains(NamedNodeMapObject *self, PyObject *key)
{
  return PyDict_GetItem(self->nodes, key) != NULL;
}

static PySequenceMethods namednodemap_as_sequence = {
  /* sq_length         */ 0,
  /* sq_concat         */ (binaryfunc) 0,
  /* sq_repeat         */ 0,
  /* sq_item           */ 0,
  /* sq_slice          */ 0,
  /* sq_ass_item       */ 0,
  /* sq_ass_slice      */ 0,
  /* sq_contains       */ (objobjproc) namednodemap_contains,
  /* sq_inplace_concat */ (binaryfunc) 0,
  /* sq_inplace_repeat */ 0,
};

/** Python Members ****************************************************/

static PyMemberDef namednodemap_members[] = {
  { NULL }
};

/** Python Computed Members *******************************************/

static PyObject *get_length(NamedNodeMapObject *self, void *arg)
{
  Py_ssize_t length;

  if ((length = PyDict_Size(self->nodes)) < 0) {
    return NULL;
  }
  return PyInt_FromLong(length);
}

static PyGetSetDef namednodemap_getset[] = {
  { "length", (getter) get_length },
  { NULL }
};

/** Type Object ********************************************************/

static void namednodemap_dealloc(NamedNodeMapObject *self)
{
  PyObject_GC_UnTrack(self);

  Py_DECREF(self->nodes);
  self->nodes = NULL;

  PyObject_GC_Del(self);
}

static PyObject *namednodemap_repr(NamedNodeMapObject *self)
{
  return PyString_FromFormat("<NamedNodeMap at %p: %" PY_FORMAT_SIZE_T "d nodes>",
                             self,
                             PyObject_Size(self->nodes));
}

static PyObject *namednodemap_str(NamedNodeMapObject *self)
{
  return PyObject_Str(self->nodes);
}

static int namednodemap_traverse(NamedNodeMapObject *self, visitproc visit,
                                 void *arg)
{
  Py_VISIT(self->nodes);
  return 0;
}

static PyObject *namednodemap_iter(NamedNodeMapObject *self)
{
  return PyObject_GetIter(self->nodes);
}

static char namednodemap_doc[] = "\
Objects implementing the NamedNodeMap interface are used to \
represent collections of nodes that can be accessed by name. \
Note that NamedNodeMaps are not maintained in any particular order. \
Objects contained in an object implementing NamedNodeMap may \
also be accessed by an ordinal index, but this is simply to allow \
convenient enumeration of the contents of a NamedNodeMap, \
and does not imply that the DOM specifies an order to these Nodes.";

static PyTypeObject NamedNodeMap_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "NamedNodeMap",
  /* tp_basicsize      */ sizeof(NamedNodeMapObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) namednodemap_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) namednodemap_repr,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) &namednodemap_as_sequence,
  /* tp_as_mapping     */ (PyMappingMethods *) &namednodemap_as_mapping,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) namednodemap_str,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
  /* tp_doc            */ (char *) namednodemap_doc,
  /* tp_traverse       */ (traverseproc) namednodemap_traverse,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) namednodemap_iter,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) namednodemap_methods,
  /* tp_members        */ (PyMemberDef *) namednodemap_members,
  /* tp_getset         */ (PyGetSetDef *) namednodemap_getset,
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

PyObject *NamedNodeMap_New(PyObject *dict)
{
  NamedNodeMapObject *self;

  assert(PyDict_Check(dict));

  self = PyObject_GC_New(NamedNodeMapObject, &NamedNodeMap_Type);
  if (self != NULL) {
    Py_INCREF(dict);
    self->nodes = dict;
    PyObject_GC_Track(self);
  }
  return (PyObject *) self;
}

/** Module Interface **************************************************/

int DomletteNamedNodeMap_Init(PyObject *module)
{
  if (PyType_Ready(&NamedNodeMap_Type) < 0)
    return -1;

  Py_INCREF(&NamedNodeMap_Type);
  return PyModule_AddObject(module, "NamedNodeMap",
                            (PyObject*) &NamedNodeMap_Type);
}

void DomletteNamedNodeMap_Fini(void)
{
  PyType_CLEAR(&NamedNodeMap_Type);
}
