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

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O:select", kwlist,
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


/** nodefilter objects ***********************************************/

typedef struct NodeFilterObject {
  FilterObject_HEAD
  PyTypeObject *node_type;
  int (*nametest)(struct NodeFilterObject *, PyObject *);
  PyObject *name;
  PyObject *namespace;
} NodeFilterObject;

Py_LOCAL_INLINE(int)
node_nametest(NodeFilterObject *self, PyObject *namespace, PyObject *name)
{
  int rv;
  if (self->namespace == NULL) {
    if (namespace != Py_None)
      return 0;
  } else {
    rv = PyObject_RichCompareBool(self->namespace, namespace, Py_EQ);
    if (rv != 1)
      return rv;
  }
  /* if `name` wasn't supplied, we're done */
  if (self->name == NULL)
    return 1;
  /* otherwise, compare it with the node's local name */
  return PyObject_RichCompareBool(self->name, name, Py_EQ);
}

static int element_nametest(NodeFilterObject *self, PyObject *node)
{
  return node_nametest(self, Element_NAMESPACE_URI(node),
                       Element_LOCAL_NAME(node));
}

static int attr_nametest(NodeFilterObject *self, PyObject *node)
{
  return node_nametest(self, Attr_GET_NAMESPACE_URI(node),
                       Attr_GET_LOCAL_NAME(node));
}

static int namespace_nametest(NodeFilterObject *self, PyObject *node)
{
  return node_nametest(self, Py_None, Namespace_GET_NAME(node));
}

static int pi_nametest(NodeFilterObject *self, PyObject *node)
{
  return node_nametest(self, Py_None, ProcessingInstruction_GET_TARGET(node));
}

static PyObject *nodefilter_new(PyTypeObject *type, PyObject *args,
                                PyObject *kwds)
{
  PyTypeObject *node_type;
  PyObject *namespace=NULL, *name=NULL;
  int (*nametest)(NodeFilterObject *, PyObject *) = NULL;
  NodeFilterObject *filter;

  /* validate the arguments */
  if (!_PyArg_NoKeywords("nodefilter", kwds))
    return NULL;
  if (!PyArg_ParseTuple(args, "O!|OO:nodefilter", &PyType_Type, &node_type,
                        &namespace, &name))
    return NULL;
  if (node_type == DomletteElement_Type) {
    if (namespace) {
      nametest = element_nametest;
      if (namespace == Py_None)
        namespace = NULL;
      if (name == Py_None)
        name = NULL;
    }
  } else if (node_type == DomletteAttr_Type) {
    if (namespace) {
      nametest = attr_nametest;
      if (namespace == Py_None)
        namespace = NULL;
      if (name == Py_None)
        name = NULL;
    }
  } else if (node_type == DomletteNamespace_Type) {
    if (namespace) {
      nametest = namespace_nametest;
      if (namespace == Py_None)
        namespace = NULL;
      if (name == Py_None)
        name = NULL;
    }
  } else if (node_type == DomletteProcessingInstruction_Type) {
    if (namespace) {
      nametest = pi_nametest;
      if (name) {
        PyErr_Format(PyExc_TypeError, 
                     "nodefilter(%s) takes an optional name argument",
                     node_type->tp_name);
        return NULL;
      }
      if (namespace == Py_None)
        name = NULL;
      else
        name = namespace;
      namespace = NULL;
    }
  } else if (PyType_IsSubtype(node_type, DomletteNode_Type)) {
    if (namespace) {
      PyErr_Format(PyExc_TypeError, "nodefilter(%s) takes no arguments",
                   node_type->tp_name);
      return NULL;
    }
  } else {
    PyErr_Format(PyExc_TypeError, 
                 "nodefilter() argument 1 must be a subclass of %s, not %s",
                 DomletteNode_Type->tp_name, node_type->tp_name);
    return NULL;
  }

  filter = (NodeFilterObject *)type->tp_alloc(type, 0);
  if (filter == NULL) {
    return NULL;
  }
  filter->nametest = nametest;
  Py_INCREF(node_type);
  filter->node_type = node_type;
  Py_XINCREF(name);
  filter->name = name;
  Py_XINCREF(namespace);
  filter->namespace = namespace;

  return (PyObject *)filter;
}

static void nodefilter_dealloc(NodeFilterObject *self)
{
  PyObject_GC_UnTrack(self);
  Py_XDECREF(self->name);
  Py_XDECREF(self->namespace);
  filter_dealloc((FilterObject *)self);
}

static PyObject *nodefilter_repr(NodeFilterObject *self)
{
  return PyString_FromFormat("<nodefilter at %p: type '%s'>",
                            self, self->node_type->tp_name);
}

static int nodefilter_traverse(NodeFilterObject *self, visitproc visit,
                               void *arg)
{
  Py_VISIT(self->node_type);
  return filter_traverse((FilterObject *)self, visit, arg);
}

static PyObject *nodefilter_next(NodeFilterObject *self)
{
  PyTypeObject *node_type = self->node_type;
  int (*nametest)(NodeFilterObject *, PyObject *) = self->nametest;
  PyObject *nodes = self->nodes;
  PyObject *(*iternext)(PyObject *);
  PyObject *node;

  /* check if exhausted */
  if (nodes == NULL) 
    return NULL;

  assert(PyIter_Check(nodes));
  iternext = *nodes->ob_type->tp_iternext;
  while ((node = iternext(nodes))) {
    if (PyObject_TypeCheck(node, node_type)) {
      if (nametest != NULL) {
        switch (nametest(self, node)) {
        case 1: 
          return node;
        case 0: 
          break;
        default:
          Py_DECREF(node);
          return NULL;
        }
      } else {
        return node;
      }
    }
    Py_DECREF(node);
  }
  /* iterator exhausted */
  self->nodes = NULL;
  Py_DECREF(nodes);
  return NULL;
}

#define NodeFilter_MEMBER(NAME, TYPE) \
  { #NAME, TYPE, offsetof(NodeFilterObject, NAME), RO }

static PyMemberDef nodefilter_members[] = {
  NodeFilter_MEMBER(node_type, T_OBJECT),
  NodeFilter_MEMBER(name, T_OBJECT),
  NodeFilter_MEMBER(namespace, T_OBJECT),
  { NULL }
};

static PyTypeObject NodeFilter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".nodefilter",
  /* tp_basicsize      */ sizeof(NodeFilterObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) nodefilter_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) nodefilter_repr,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) 0,
  /* tp_as_mapping     */ (PyMappingMethods *) 0,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) 0,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) nodefilter_traverse,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) nodefilter_next,
  /* tp_methods        */ (PyMethodDef *) 0,
  /* tp_members        */ (PyMemberDef *) nodefilter_members,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) &Filter_Type,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) nodefilter_new,
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
    &NodeFilter_Type,
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
