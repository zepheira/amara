#include "Python.h"
#include "structmember.h"
#include "domlette_interface.h"

#define MODULE_NAME "amara.xpath.locationpaths._nodetests"
#define MODULE_INITFUNC init_nodetests

/** Filter object ****************************************************/

#define FilterObject_HEAD \
  PyObject_HEAD \
  PyObject *nodes;

typedef struct {
  FilterObject_HEAD
} FilterObject;

static PyObject *filter_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = { NULL };

  if (!PyArg_ParseTupleAndKeywords(args, kwds, ":filter", kwlist)) {
    return NULL;
  }

  return type->tp_alloc(type, 0);
}

static void filter_dealloc(FilterObject *self)
{
  PyObject_GC_UnTrack(self);
  Py_XDECREF(self->nodes);
  self->ob_type->tp_free(self);
}

static int filter_traverse(FilterObject *self, visitproc visit, void *arg)
{
  Py_VISIT(self->nodes);
  return 0;
}

static PyObject *filter_call(PyObject *self, PyObject *args, PyObject *kwds)
{
  FilterObject *filter = (FilterObject *)self;
  PyObject *context, *nodes = Py_None;
  static char *kwlist[] = { "context", "nodes", NULL };

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O", kwlist,
                                   &context, &nodes)) {
    context = NULL; /* silence GCC warning */
    return NULL;
  }

  if (nodes == Py_None) {
    PyObject *seq = PyTuple_New(1);
    if (seq == NULL) {
      return NULL;
    }
    PyTuple_SET_ITEM(seq, 0, PyObject_GetAttrString(context, "node"));
    if (PyTuple_GET_ITEM(seq, 0) == NULL) {
      Py_DECREF(seq);
      return NULL;
    }
    nodes = PyObject_GetIter(seq);
    Py_DECREF(seq);
  } else {
    nodes = PyObject_GetIter(nodes);
  }
  if (nodes == NULL) {
    return NULL;
  }
  Py_XDECREF(filter->nodes);
  filter->nodes = nodes;

  Py_INCREF(self);
  return self;
}

static PyMethodDef filter_methods[] = {
  { "select", (PyCFunction) filter_call, METH_KEYWORDS, NULL },
  { NULL }
};

static PyTypeObject Filter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".filter",
  /* tp_basicsize      */ sizeof(FilterObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) filter_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) 0,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) 0,
  /* tp_as_mapping     */ (PyMappingMethods *) 0,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) filter_call,
  /* tp_str            */ (reprfunc) 0,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT |
                           Py_TPFLAGS_BASETYPE |
                           Py_TPFLAGS_HAVE_GC),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) filter_traverse,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) filter_methods,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) filter_new,
  /* tp_free           */ 0,
};


/** namefilter object ************************************************/

typedef struct {
  FilterObject_HEAD
  int nodeType;
  PyObject *namespaceURI;
  PyObject *localName;
} NameFilterObject;

static PyObject *namefilter_new(PyTypeObject *type, PyObject *args,
                                PyObject *kwds)
{
  PyObject *namespaceURI, *localName;
  int typeCode;
  NameFilterObject *filter;
  static char *kwlist[] = { "nodeType", "namespaceURI", "localName", NULL };

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "iOO:namefilter", kwlist,
                                   &typeCode, &namespaceURI, &localName)) {
    return NULL;
  }

  switch (typeCode) {
  case ELEMENT_NODE:
  case ATTRIBUTE_NODE:
  case PROCESSING_INSTRUCTION_NODE:
  case XPATH_NAMESPACE_NODE:
    break;
  default:
    PyErr_Format(PyExc_ValueError, "invalid node type: %d", typeCode);
    return NULL;
  }

  filter = (NameFilterObject *)type->tp_alloc(type, 0);
  if (filter == NULL) {
    return NULL;
  }
  filter->nodeType = typeCode;
  Py_INCREF(namespaceURI);
  filter->namespaceURI = namespaceURI;
  Py_INCREF(localName);
  filter->localName = localName;

  return (PyObject *)filter;
}

static void namefilter_dealloc(NameFilterObject *self)
{
  PyObject_GC_UnTrack(self);
  Py_DECREF(self->namespaceURI);
  Py_DECREF(self->localName);
  filter_dealloc((FilterObject *)self);
}

static PyObject *namefilter_next(NameFilterObject *self)
{
  PyObject *nodes = self->nodes;
  PyObject *(*iternext)(PyObject *);
  PyTypeObject *nodeType;
  PyObject *node, *namespaceURI, *localName;

  switch (self->nodeType) {
  case ELEMENT_NODE:
    nodeType = Domlette->Element_Type;
    break;
  case ATTRIBUTE_NODE:
    nodeType = Domlette->Attr_Type;
    break;
  case PROCESSING_INSTRUCTION_NODE:
    nodeType = Domlette->ProcessingInstruction_Type;
    break;
  case XPATH_NAMESPACE_NODE:
    nodeType = Domlette->Namespace_Type;
    break;
  default:
    PyErr_BadInternalCall();
    return NULL;
  }

  if (nodes == NULL) return NULL;

  assert(PyIter_Check(nodes));
  iternext = *nodes->ob_type->tp_iternext;
  while ((node = iternext(nodes))) {
    int ok;
    if (PyObject_TypeCheck(node, nodeType)) {
      switch (self->nodeType) {
      case ELEMENT_NODE:
        namespaceURI = Element_GET_NAMESPACE_URI(node);
        localName = Element_GET_LOCAL_NAME(node);
        break;
      case ATTRIBUTE_NODE:
        namespaceURI = Attr_GET_NAMESPACE_URI(node);
        localName = Attr_GET_LOCAL_NAME(node);
        break;
      case PROCESSING_INSTRUCTION_NODE:
        namespaceURI = Py_None;
        localName = ProcessingInstruction_GET_TARGET(node);
        break;
      case XPATH_NAMESPACE_NODE:
        namespaceURI = Py_None;
        localName = Namespace_GET_NAME(node);
        break;
      default: /* not reached */
        PyErr_BadInternalCall();
      error:
        Py_DECREF(node);
        return NULL;
      }
      if (self->namespaceURI == Py_None) {
        ok = namespaceURI == Py_None;
      } else {
        ok = PyObject_RichCompareBool(self->namespaceURI, namespaceURI, Py_EQ);
        if (ok < 0) goto error;
      }
      if (ok) {
        if (self->localName == Py_None) return node;
        switch (PyObject_RichCompareBool(self->localName, localName, Py_EQ)) {
        case 1: return node;
        case 0: break;
        default: goto error;
        }
      }
    }
    Py_DECREF(node);
  }
  /* iterator exhausted */
  self->nodes = NULL;
  Py_DECREF(nodes);
  return NULL;
}

#define NameFilter_MEMBER(NAME, TYPE) \
  { #NAME, TYPE, offsetof(NameFilterObject, NAME), RO }

static PyMemberDef namefilter_members[] = {
  NameFilter_MEMBER(nodeType, T_INT),
  NameFilter_MEMBER(namespaceURI, T_OBJECT),
  NameFilter_MEMBER(localName, T_OBJECT),
  { NULL }
};

static PyTypeObject NameFilter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".namefilter",
  /* tp_basicsize      */ sizeof(NameFilterObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) namefilter_dealloc,
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
  /* tp_flags          */ Py_TPFLAGS_DEFAULT,
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) namefilter_next,
  /* tp_methods        */ (PyMethodDef *) 0,
  /* tp_members        */ (PyMemberDef *) namefilter_members,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) &Filter_Type,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) namefilter_new,
  /* tp_free           */ 0,
};


/** typefilter object ************************************************/

typedef struct {
  FilterObject_HEAD
  PyTypeObject *nodeType;
} TypeFilterObject;

static PyObject *typefilter_new(PyTypeObject *type, PyObject *args,
                                PyObject *kwds)
{
  int typeCode;
  PyTypeObject *nodeType;
  TypeFilterObject *filter;

  if (!PyArg_ParseTuple(args, "i:typefilter", &typeCode)) {
    return NULL;
  }

  switch (typeCode) {
  case ELEMENT_NODE:
    nodeType = Domlette->Element_Type;
    break;
  case ATTRIBUTE_NODE:
    nodeType = Domlette->Attr_Type;
    break;
  case TEXT_NODE:
    nodeType = Domlette->Text_Type;
    break;
  case PROCESSING_INSTRUCTION_NODE:
    nodeType = Domlette->ProcessingInstruction_Type;
    break;
  case COMMENT_NODE:
    nodeType = Domlette->Comment_Type;
    break;
  case XPATH_NAMESPACE_NODE:
    nodeType = Domlette->Namespace_Type;
    break;
  default:
    PyErr_Format(PyExc_ValueError, "invalid node type: %d", typeCode);
    return NULL;
  }
  filter = (TypeFilterObject *)type->tp_alloc(type, 0);
  if (filter == NULL) {
    return NULL;
  }
  Py_INCREF(nodeType);
  filter->nodeType = nodeType;

  return (PyObject *)filter;
}

static void typefilter_dealloc(TypeFilterObject *self)
{
  PyObject_GC_UnTrack(self);
  Py_DECREF((PyObject *)(self->nodeType));
  filter_dealloc((FilterObject *)self);
}

static int typefilter_traverse(TypeFilterObject *self, visitproc visit,
                               void *arg)
{
  Py_VISIT(self->nodeType);
  return filter_traverse((FilterObject *)self, visit, arg);
}

static PyObject *typefilter_next(TypeFilterObject *self)
{
  PyObject *nodes = self->nodes;
  PyTypeObject *nodeType = self->nodeType;
  PyObject *(*iternext)(PyObject *);
  PyObject *node;

  if (nodes == NULL) return NULL;

  assert(PyIter_Check(nodes));
  iternext = *nodes->ob_type->tp_iternext;
  while ((node = iternext(nodes))) {
    if (PyObject_TypeCheck(node, nodeType)) {
      return node;
    }
    Py_DECREF(node);
  }
  /* iterator exhausted */
  self->nodes = NULL;
  Py_DECREF(nodes);
  return NULL;
}

static PyTypeObject TypeFilter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".typefilter",
  /* tp_basicsize      */ sizeof(TypeFilterObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) typefilter_dealloc,
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
                           Py_TPFLAGS_HAVE_GC),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) typefilter_traverse,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) typefilter_next,
  /* tp_methods        */ (PyMethodDef *) 0,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) &Filter_Type,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) typefilter_new,
  /* tp_free           */ 0,
};

/** positionfilter object ********************************************/

typedef struct {
  FilterObject_HEAD
  int position;
} PositionFilterObject;

static PyObject *positionfilter_new(PyTypeObject *type, PyObject *args,
                                    PyObject *kwds)
{
  int position;
  PositionFilterObject *filter;
  static char *kwlist[] = { "position", NULL };

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "i:positionfilter", kwlist,
                                   &position)) {
    return NULL;
  }

  if (position < 1) {
    PyErr_SetString(PyExc_ValueError, "position must be positive");
    return NULL;
  }

  filter = (PositionFilterObject *)type->tp_alloc(type, 0);
  if (filter == NULL) {
    return NULL;
  }
  filter->position = position;

  return (PyObject *)filter;
}

static PyObject *positionfilter_next(PositionFilterObject *self)
{
  PyObject *nodes = self->nodes;
  PyObject *(*iternext)(PyObject *);
  int position = self->position;
  PyObject *node;

  if (nodes == NULL) return NULL;

  assert(PyIter_Check(nodes));
  iternext = nodes->ob_type->tp_iternext;
  /* skip over nodes until `position` is reached (1-based index) */
  while (--position > 0) {
    node = iternext(nodes);
    if (node == NULL) return NULL;
    Py_DECREF(node);
  }
  node = iternext(nodes);
  /* the only possible result is found, get rid of the iterator */
  self->nodes = NULL;
  Py_DECREF(nodes);
  return node;
}

static PyTypeObject PositionFilter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".positionfilter",
  /* tp_basicsize      */ sizeof(PositionFilterObject),
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
  /* tp_flags          */ Py_TPFLAGS_DEFAULT,
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) positionfilter_next,
  /* tp_methods        */ (PyMethodDef *) 0,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) &Filter_Type,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) positionfilter_new,
  /* tp_free           */ 0,
};


static PyMethodDef module_methods[] = {
  { NULL }
};

PyMODINIT_FUNC MODULE_INITFUNC(void)
{
  PyObject *module;
  PyTypeObject *typelist[] = {
    &Filter_Type,
    &NameFilter_Type,
    &TypeFilter_Type,
    &PositionFilter_Type,
    NULL
  };
  int i;

  module = Py_InitModule(MODULE_NAME, module_methods);
  if (module == NULL) return;

  Domlette_IMPORT;

  for (i = 0; typelist[i]; i++) {
    const char *name = typelist[i]->tp_name + sizeof(MODULE_NAME);
    assert (name != NULL);
    typelist[i]->tp_iter = PyObject_SelfIter;
    if (PyType_Ready(typelist[i]) < 0) {
      return;
    }
    Py_INCREF(typelist[i]);
    if (PyModule_AddObject(module, name, (PyObject *)typelist[i]) < 0) {
      return;
    }
  }
}
