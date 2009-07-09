/***********************************************************************
 * amara/xpath/src/paths.c
 ***********************************************************************/

static char module_doc[] = "\
XPath PathExpr as types\n\
";

#include "Python.h"
#include "structmember.h"

#define MODULE_NAME "amara.xpath.locationpaths._paths"
#define MODULE_INITFUNC init_paths

/** reverseiter object ***********************************************/

typedef struct {
  PyObject_HEAD
  Py_ssize_t it_index;
  PyObject *it_seq;
} ReverseIterObject;

static void reviter_dealloc(ReverseIterObject *it)
{
  PyObject_GC_UnTrack(it);
  Py_XDECREF(it->it_seq);
  PyObject_GC_Del(it);
}

static int reviter_traverse(ReverseIterObject *it, visitproc visit, void *arg)
{
  Py_VISIT(it->it_seq);
  return 0;
}

static PyObject *reviter_next(ReverseIterObject *it)
{
  Py_ssize_t index = it->it_index;
  PyObject *seq = it->it_seq;
  PyObject *item;

  if (index >= 0) {
    assert(index < PyTuple_GET_SIZE(seq));
    item = PyTuple_GET_ITEM(seq, index);
    it->it_index--;
    Py_INCREF(item);
    return item;
  }
  if (seq != NULL) {
    it->it_seq = NULL;
    Py_DECREF(seq);
  }
  return NULL;
}

PyTypeObject ReverseIter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".reverseiter",
  /* tp_basicsize      */ sizeof(ReverseIterObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) reviter_dealloc,
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
  /* tp_traverse       */ (traverseproc) reviter_traverse,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) reviter_next,
  /* tp_methods        */ (PyMethodDef *) 0,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
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

static PyObject *ReverseIter_New(PyObject *iterable)
{
  PyObject *seq;
  ReverseIterObject *it;

  seq = PySequence_Tuple(iterable);
  if (seq == NULL) return NULL;

  it = PyObject_GC_New(ReverseIterObject, &ReverseIter_Type);
  if (it == NULL) return NULL;

  it->it_index = PyTuple_GET_SIZE(seq) - 1;
  it->it_seq = seq;
  PyObject_GC_Track(it);
  return (PyObject *)it;
}

/** stepiter object **************************************************/

typedef struct {
  PyObject_HEAD
  PyObject *context;
  PyObject *context_nodes;
  PyObject *current_nodes;
  PyObject *axis;
  PyObject *node_test;
  PyObject *predicates;
  int reversed;
} StepIterObject;

static void stepiter_dealloc(StepIterObject *self)
{
  PyObject_GC_UnTrack(self);
  Py_XDECREF(self->context);
  Py_XDECREF(self->context_nodes);
  Py_XDECREF(self->current_nodes);
  Py_XDECREF(self->axis);
  Py_XDECREF(self->node_test);
  Py_XDECREF(self->predicates);
  self->ob_type->tp_free((PyObject *)self);
}

static int stepiter_traverse(StepIterObject *self, visitproc visit, void *arg)
{
  Py_VISIT(self->context);
  Py_VISIT(self->context_nodes);
  Py_VISIT(self->current_nodes);
  Py_VISIT(self->axis);
  Py_VISIT(self->node_test);
  Py_VISIT(self->predicates);
  return 0;
}

static PyObject *stepiter_call(StepIterObject *self, PyObject *args,
                               PyObject *kwds)
{
  PyObject *context, *nodes = Py_None;
  static char *kwlist[] = { "context", "nodes", NULL };

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O:stepiter", kwlist,
                                   &context, &nodes)) {
    return NULL;
  }

  if (nodes == Py_None) {
    PyObject *node, *seq = PyTuple_New(1);
    if (seq == NULL) {
      return NULL;
    }
    node = PyObject_GetAttrString(context, "node");
    if (node == NULL) {
      Py_DECREF(seq);
      return NULL;
    }
    PyTuple_SET_ITEM(seq, 0, node);
    nodes = PyObject_GetIter(seq);
    Py_DECREF(seq);
  } else {
    nodes = PyObject_GetIter(nodes);
  }
  if (nodes == NULL) {
    return NULL;
  }
  Py_XDECREF(self->context_nodes);
  self->context_nodes = nodes;
  Py_XDECREF(self->current_nodes);
  self->current_nodes = NULL;
  Py_INCREF(context);
  self->context = context;
  Py_INCREF(self);
  return (PyObject *)self;
}

static PyObject *stepiter_next(StepIterObject *self)
{
  PyObject *context_nodes = self->context_nodes;
  PyObject *current_nodes = self->current_nodes;
  PyObject *node, *nodes, *args;

  if (current_nodes) {
    assert(PyIter_Check(current_nodes));
    node = current_nodes->ob_type->tp_iternext(current_nodes);
    if (node) return node;
    /* The current node iterator is exhausted, get the next one. */
    self->current_nodes = NULL;
    Py_DECREF(current_nodes);
  }

  if (context_nodes) {
    assert(PyIter_Check(context_nodes));
    node = context_nodes->ob_type->tp_iternext(context_nodes);
    if (node == NULL) {
    /* The context node iterator is exhausted, signal complete. */
      self->context_nodes = NULL;
      Py_DECREF(context_nodes);
      return NULL;
    }
    /* nodes = axis(node) */
    args = PyTuple_New(1);
    if (args == NULL) {
      Py_DECREF(node);
      return NULL;
    }
    PyTuple_SET_ITEM(args, 0, node); /* let the tuple own the reference */
    nodes = PyObject_Call(self->axis, args, NULL);
    Py_DECREF(args);
    if (nodes == NULL) return NULL;

    /* if node_test: nodes = node_test(context, nodes) */
    if (self->node_test) {
      args = PyTuple_New(2);
      if (args == NULL) {
        Py_DECREF(nodes);
        return NULL;
      }
      Py_INCREF(self->context);
      PyTuple_SET_ITEM(args, 0, self->context);
      PyTuple_SET_ITEM(args, 1, nodes);
      nodes = PyObject_Call(self->node_test, args, NULL);
      Py_DECREF(args);
      if (nodes == NULL) return NULL;
    }

    /* for pred in predicates: nodes = pred(context, nodes) */
    if (self->predicates) {
      Py_ssize_t i;
      for (i = 0; i < PyTuple_GET_SIZE(self->predicates); i++) {
        PyObject *predicate = PyTuple_GET_ITEM(self->predicates, i);
        args = PyTuple_New(2);
        if (args == NULL) {
          Py_DECREF(nodes);
          return NULL;
        }
        Py_INCREF(self->context);
        PyTuple_SET_ITEM(args, 0, self->context);
        PyTuple_SET_ITEM(args, 1, nodes);
        nodes = PyObject_Call(predicate, args, NULL);
        Py_DECREF(args);
        if (nodes == NULL) return NULL;
      }
    }

    if (self->reversed) {
      self->current_nodes = ReverseIter_New(nodes);
      Py_DECREF(nodes);
      if (self->current_nodes == NULL) return NULL;
    } else {
      self->current_nodes = nodes;
    }
    return stepiter_next(self);
  }
  /* iterators exhausted */
  return NULL;
}

static PyObject *stepiter_new(PyTypeObject *type, PyObject *args,
                              PyObject *kwds)
{
  PyObject *axis, *node_test, *predicates = Py_None;
  int reversed;
  Py_ssize_t i;
  StepIterObject *step;

  if (!PyArg_ParseTuple(args, "OiO|O:stepiter",
                        &axis, &reversed, &node_test, &predicates)) {
    return NULL;
  }

  if (!PyCallable_Check(axis)) {
    PyErr_SetString(PyExc_ValueError, "argument 1 must be callable");
    return NULL;
  }
  if (node_test != Py_None) {
    if (!PyCallable_Check(node_test)) {
      PyErr_SetString(PyExc_ValueError, "argument 3 must be callable or None");
      return NULL;
    }
  } else {
    node_test = NULL;
  }
  if (predicates != Py_None) {
    predicates = PySequence_Tuple(predicates);
    if (predicates == NULL) {
      PyErr_SetString(PyExc_ValueError,
                      "argument 4 must be a sequence of callables or None");
      return NULL;
    }
    for (i = 0; i < PyTuple_GET_SIZE(predicates); i++) {
      if (!PyCallable_Check(PyTuple_GET_ITEM(predicates, i))) {
        PyErr_SetString(PyExc_ValueError,
                        "argument 4 must be a sequence of callables or None");
        Py_DECREF(predicates);
        return NULL;
      }
    }
  } else {
    predicates = NULL;
  }

  step = (StepIterObject *) type->tp_alloc(type, 0);
  if (step == NULL) {
    Py_XDECREF(predicates);
    return NULL;
  }
  Py_INCREF(axis);
  step->axis = axis;
  step->reversed = reversed;
  Py_XINCREF(node_test);
  step->node_test = node_test;
  step->predicates = predicates;
  return (PyObject *)step;
}

static PyMethodDef stepiter_methods[] = {
  { "select", (PyCFunction) stepiter_call, METH_KEYWORDS, NULL },
  { NULL }
};

static PyTypeObject StepIter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".stepiter",
  /* tp_basicsize      */ sizeof(StepIterObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) stepiter_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) 0,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) 0,
  /* tp_as_mapping     */ (PyMappingMethods *) 0,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) stepiter_call,
  /* tp_str            */ (reprfunc) 0,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT |
                           Py_TPFLAGS_HAVE_GC),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) stepiter_traverse,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) stepiter_next,
  /* tp_methods        */ (PyMethodDef *) stepiter_methods,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) stepiter_new,
  /* tp_free           */ 0,
};

/** pathiter object **************************************************/

typedef struct {
  PyObject_HEAD
  PyObject *steps;
} PathIterObject;

static void pathiter_dealloc(PathIterObject *self)
{
  PyObject_GC_UnTrack(self);
  Py_XDECREF(self->steps);
  self->ob_type->tp_free((PyObject *)self);
}

static int pathiter_traverse(PathIterObject *self, visitproc visit, void *arg)
{
  Py_VISIT(self->steps);
  return 0;
}

static PyObject *pathiter_call(PathIterObject *self, PyObject *args,
                               PyObject *kwds)
{
  PyObject *context, *nodes = Py_None;
  static char *kwlist[] = { "context", "nodes", NULL };
  PyObject *steps = self->steps;
  Py_ssize_t i, size = PyTuple_GET_SIZE(steps);

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O:pathiter", kwlist,
                                   &context, &nodes)) {
    return NULL;
  }

  if (nodes == Py_None) {
    nodes = PyTuple_New(1);
    if (nodes == NULL) {
      return NULL;
    }
    PyTuple_SET_ITEM(nodes, 0, PyObject_GetAttrString(context, "node"));
    if (PyTuple_GET_ITEM(nodes, 0) == NULL) {
      Py_DECREF(nodes);
      return NULL;
    }
  } else {
    Py_INCREF(nodes);
  }

  for (i = 0; i < size; i++) {
    args = PyTuple_New(2);
    if (args == NULL) {
      Py_DECREF(nodes);
      return NULL;
    }
    Py_INCREF(context);
    PyTuple_SET_ITEM(args, 0, context);
    PyTuple_SET_ITEM(args, 1, nodes);
    nodes = PyObject_Call(PyTuple_GET_ITEM(steps, i), args, NULL);
    Py_DECREF(args);
    if (nodes == NULL) break;
  }
  return nodes;
}

static PyObject *pathiter_new(PyTypeObject *type, PyObject *args,
                              PyObject *kwds)
{
  PyObject *steps;
  PathIterObject *self;
  static char *kwlist[] = { "steps", NULL };

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:pathiter", kwlist, &steps)) {
    return NULL;
  }

  self = (PathIterObject *) type->tp_alloc(type, 0);
  if (self) {
    self->steps = PySequence_Tuple(steps);
    if (self->steps == NULL) {
      Py_DECREF(self);
      self = NULL;
    }
  }
  return (PyObject *)self;
}

static PyMethodDef pathiter_methods[] = {
  { "select", (PyCFunction) pathiter_call, METH_KEYWORDS, NULL },
  { NULL }
};

PyTypeObject PathIter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".pathiter",
  /* tp_basicsize      */ sizeof(PathIterObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) pathiter_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) 0,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) 0,
  /* tp_as_mapping     */ (PyMappingMethods *) 0,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) pathiter_call,
  /* tp_str            */ (reprfunc) 0,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT |
                           Py_TPFLAGS_HAVE_GC),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) pathiter_traverse,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) pathiter_methods,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) pathiter_new,
  /* tp_free           */ 0,
};

/** unioniter ********************************************************/

static PyObject *UnionIter(PyObject *module, PyObject *args)
{
  Py_ssize_t i;
  PyObject *set, *iter, *item, *nodes;
  iternextfunc iternext;

  set = PyDict_New();
  if (set == NULL) {
    return NULL;
  }
  /* For each expression, add its node-set to the combined node-set */
  i = PyTuple_GET_SIZE(args);
  while (--i >= 0) {
    iter = PyObject_GetIter(PyTuple_GET_ITEM(args, i));
    if (iter == NULL) {
      Py_DECREF(set);
      return NULL;
    }
    assert(PyIter_Check(iter));
    iternext = iter->ob_type->tp_iternext;
    while ((item = iternext(iter))) {
      if (PyDict_SetItem(set, item, Py_True) < 0) {
        Py_DECREF(item);
        Py_DECREF(set);
        return NULL;
      }
      Py_DECREF(item);
    }
  }
  /* Convert node-set to ordered node-list */
  nodes = PyDict_Keys(set);
  Py_DECREF(set);
  if (nodes == NULL) {
    return NULL;
  }
  if (PyList_Sort(nodes) < 0) {
    Py_DECREF(nodes);
    return NULL;
  }

  iter = PyObject_GetIter(nodes);
  Py_DECREF(nodes);
  return iter;
}

/** Module Initialization ********************************************/

static PyMethodDef module_methods[] = {
  { "unioniter", UnionIter, METH_VARARGS },
  { NULL }
};

PyMODINIT_FUNC MODULE_INITFUNC(void)
{
  PyObject *module;
  PyTypeObject *typelist[] = {
    &StepIter_Type,
    &PathIter_Type,
    NULL
  };
  int i;

  module = Py_InitModule3(MODULE_NAME, module_methods, module_doc);
  if (module == NULL) return;

  if (PyType_Ready(&ReverseIter_Type) < 0) return;

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
