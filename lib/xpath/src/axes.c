#include "Python.h"
#include "structmember.h"

/* Backward compat code recommended in PEP 353 */
#if PY_VERSION_HEX < 0x02050000
    typedef int Py_ssize_t;
#endif

#include "domlette_interface.h"
#include "node.h"
#include "element.h"
#include "attr.h"

#define MODULE_NAME "amara.xpath.locationpaths._axes"
#define MODULE_INITFUNC init_axes

static PyObject *xmlns_namespace;

/** AncestorAxis object *******************************************/

typedef struct {
  PyObject_HEAD
  PyObject *node;
} ancestor_axis;

static PyObject *ancestor_axis_new(PyTypeObject *type, PyObject *args,
                                   PyObject *kwds)
{
  PyObject *node;
  ancestor_axis *axis;

  if (!PyArg_ParseTuple(args, "O!:ancestor_axis",
                        Domlette->Node_Type, &node)) {
    return NULL;
  }

  axis = (ancestor_axis *)type->tp_alloc(type, 0);
  if (axis == NULL) {
    return NULL;
  }
  node = (PyObject *) Node_GET_PARENT(node);
  Py_XINCREF(node);
  axis->node = node;
  return (PyObject *)axis;
}

static void ancestor_axis_dealloc(ancestor_axis *self)
{
  Py_CLEAR(self->node);
  self->ob_type->tp_free(self);
}

static PyObject *ancestor_axis_next(ancestor_axis *self)
{
  PyObject *node = self->node;

  if (node != NULL) {
    self->node = (PyObject *) Node_GET_PARENT(node);
    Py_XINCREF(self->node);
    /* give our reference on `node` to the caller */
    return node;
  }
  return NULL;
}

static PyTypeObject ancestor_axis_type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME "." "ancestor_axis",
  /* tp_basicsize      */ sizeof(ancestor_axis),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) ancestor_axis_dealloc,
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
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) ancestor_axis_next,
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
  /* tp_new            */ (newfunc) ancestor_axis_new,
  /* tp_free           */ 0,
};

/** AncestorOrSelfAxis object ****************************************/

static PyObject *ancestor_self_axis_new(PyTypeObject *type, PyObject *args,
                                        PyObject *kwds)
{
  PyObject *node;
  ancestor_axis *axis;

  if (!PyArg_ParseTuple(args, "O!:ancestor_or_self_axis",
                        Domlette->Node_Type, &node)) {
    return NULL;
  }

  axis = (ancestor_axis *)type->tp_alloc(type, 0);
  if (axis == NULL) {
    return NULL;
  }
  Py_INCREF(node);
  axis->node = node;
  return (PyObject *)axis;
}

static PyTypeObject ancestor_self_axis_type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME "." "ancestor_or_self_axis",
  /* tp_basicsize      */ sizeof(ancestor_axis),
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
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) 0,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) &ancestor_axis_type,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) ancestor_self_axis_new,
  /* tp_free           */ 0,
};

/** AttributeAxis object *********************************************/

typedef struct {
  PyObject_HEAD
  PyObject *adict;
  Py_ssize_t pos;
} attribute_axis;

static PyObject *attribute_axis_new(PyTypeObject *type, PyObject *args,
                                   PyObject *kwds)
{
  PyObject *node;
  attribute_axis *axis;

  if (!PyArg_ParseTuple(args, "O!:attribute_axis",
                        Domlette->Node_Type, &node)) {
    return NULL;
  }

  axis = (attribute_axis *)type->tp_alloc(type, 0);
  if (axis == NULL) {
    return NULL;
  }
  if (Element_Check(node)) {
    axis->adict = Element_ATTRIBUTES(node);
    Py_XINCREF(axis->adict);
  } else {
    axis->adict = NULL;
  }
  axis->pos = 0;
  return (PyObject *)axis;
}

static void attribute_axis_dealloc(attribute_axis *self)
{
  Py_XDECREF(self->adict);
  self->ob_type->tp_free(self);
}

static PyObject *attribute_axis_next(attribute_axis *self)
{
  if (self->adict != NULL) {
    AttrObject *attr;
    while ((attr = AttributeMap_Next(self->adict, &self->pos))) {
      Py_INCREF(attr);
      return (PyObject *)attr;
    }
    Py_CLEAR(self->adict);
  }
  return NULL;
}

static PyTypeObject attribute_axis_type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME "." "attribute_axis",
  /* tp_basicsize      */ sizeof(attribute_axis),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) attribute_axis_dealloc,
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
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) attribute_axis_next,
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
  /* tp_new            */ (newfunc) attribute_axis_new,
  /* tp_free           */ 0,
};

/** ChildAxis object *************************************************/

typedef struct {
  PyObject_HEAD
  NodeObject *node;
  int index;
} child_axis;

Py_LOCAL_INLINE(PyObject *)
child_axis_init(child_axis *axis, NodeObject *node)
{
  if (Element_Check(node) || Entity_Check(node))
    Py_INCREF(node);
  else
    node = NULL; /* mark iterator as done */
  axis->node = node;
  return (PyObject *)axis;
}

static PyObject *child_axis_new(PyTypeObject *type, PyObject *args,
                                PyObject *kwds)
{
  NodeObject *node;
  child_axis *axis;

  if (!PyArg_ParseTuple(args, "O!:child_axis",
                        Domlette->Node_Type, &node)) {
    return NULL;
  }

  axis = (child_axis *)type->tp_alloc(type, 0);
  if (axis == NULL) {
    return NULL;
  }
  return child_axis_init(axis, node);
}

static void child_axis_dealloc(child_axis *self)
{
  Py_XDECREF((PyObject *)self->node);
  self->ob_type->tp_free(self);
}

static PyObject *child_axis_next(child_axis *self)
{
  NodeObject *node = self->node;
  int index = self->index;
  if (node == NULL) return NULL;

  if (index < Container_GET_COUNT(node)) {
    node = Container_GET_CHILD(node, index);
    self->index++;
    Py_INCREF(node);
    return (PyObject *)node;
  }

  self->node = NULL;
  Py_DECREF(node);
  return NULL;
}

static PyTypeObject child_axis_type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME "." "child_axis",
  /* tp_basicsize      */ sizeof(child_axis),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) child_axis_dealloc,
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
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) child_axis_next,
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
  /* tp_new            */ (newfunc) child_axis_new,
  /* tp_free           */ 0,
};

static PyObject *get_child_axis(NodeObject *node)
{
  child_axis *axis = PyObject_New(child_axis, &child_axis_type);
  if (axis == NULL)
    return NULL;
  axis->index = 0;
  return child_axis_init(axis, node);
}

/** DescendantAxis object ********************************************/

typedef struct {
  PyObject_HEAD
  PyObject *stack;
  Py_ssize_t depth;
} descendant_axis;

static PyObject *descendant_axis_new(PyTypeObject *type, PyObject *args,
                                    PyObject *kwds)
{
  PyObject *stack;
  NodeObject *node;
  descendant_axis *axis;

  if (!PyArg_ParseTuple(args, "O!:descendant_axis",
                        Domlette->Node_Type, &node)) {
    return NULL;
  }

  stack = PyList_New(1);
  if (stack == NULL) {
    return NULL;
  }
  if (PyList_SET_ITEM(stack, 0, get_child_axis(node)) == NULL) {
    Py_DECREF(stack);
    return NULL;
  }

  axis = (descendant_axis *)type->tp_alloc(type, 0);
  if (axis == NULL) {
    Py_DECREF(stack);
    return NULL;
  }
  axis->stack = stack;
  return (PyObject *)axis;
}

static void descendant_axis_dealloc(descendant_axis *self)
{
  Py_XDECREF(self->stack);
  self->ob_type->tp_free(self);
}

static PyObject *descendant_axis_next(descendant_axis *self)
{
  PyObject *stack, *nodeiter, *node;
  iternextfunc iternext;
  Py_ssize_t depth;

  stack = self->stack;
  for (depth = self->depth; depth >= 0; depth--) {
    nodeiter = PyList_GET_ITEM(stack, depth);
    assert(PyIter_Check(nodeiter));
    iternext = nodeiter->ob_type->tp_iternext;
    while ((node = iternext(nodeiter))) {
      /* If `node` is an Element, add its iterator to our stack for the
       * iteration. */
      if (Element_Check(node)) {
        nodeiter = get_child_axis((NodeObject *)node);
        if (nodeiter == NULL) {
          Py_DECREF(node);
          return NULL;
        }
        if (++depth < PyList_GET_SIZE(stack)) {
          Py_DECREF(PyList_GET_ITEM(stack, depth));
          PyList_SET_ITEM(stack, depth, nodeiter);
        } else {
          if (PyList_Append(stack, nodeiter) < 0) {
            Py_DECREF(nodeiter);
            Py_DECREF(node);
            return NULL;
          }
          Py_DECREF(nodeiter);
        }
      }
      self->depth = depth;
      return node;
    }
  }
  return NULL;
}

static PyTypeObject descendant_axis_type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME "." "descendant_axis",
  /* tp_basicsize      */ sizeof(descendant_axis),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) descendant_axis_dealloc,
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
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) descendant_axis_next,
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
  /* tp_new            */ (newfunc) descendant_axis_new,
  /* tp_free           */ 0,
};

/** DescendantOrSelfAxis object **************************************/

static PyObject *descendant_self_axis_new(PyTypeObject *type, PyObject *args,
                                          PyObject *kwds)
{
  PyObject *node;
  descendant_axis *axis;

  if (!PyArg_ParseTuple(args, "O!:descendant_or_self_axis",
                        Domlette->Node_Type, &node)) {
    return NULL;
  }

  axis = (descendant_axis *)type->tp_alloc(type, 0);
  if (axis == NULL) {
    return NULL;
  }
  Py_INCREF(node);
  axis->stack = node;
  return (PyObject *)axis;
}

static PyObject *descendant_self_axis_next(descendant_axis *self)
{
  PyObject *node, *stack;

  node = self->stack;
  if (PyList_CheckExact(node)) {
    return descendant_axis_next(self);
  }

  assert(Node_Check(node));
  stack = PyList_New(1);
  if (stack == NULL) return NULL;
  if (PyList_SET_ITEM(stack, 0, get_child_axis((NodeObject *)node)) == NULL) {
    Py_DECREF(stack);
    return NULL;
  }
  self->stack = stack;
  return node;
}

static PyTypeObject descendant_self_axis_type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME "." "descendant_or_self_axis",
  /* tp_basicsize      */ sizeof(descendant_axis),
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
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) descendant_self_axis_next,
  /* tp_methods        */ (PyMethodDef *) 0,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) &descendant_axis_type,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) descendant_self_axis_new,
  /* tp_free           */ 0,
};

/** FollowingSiblingAxis object **************************************/

typedef struct {
  PyObject_HEAD
  NodeObject *parent;
  Py_ssize_t index;
  Py_ssize_t count;
} followingsibling_axis;

static PyObject *followingsibling_axis_new(PyTypeObject *type, PyObject *args,
                                          PyObject *kwds)
{
  NodeObject *node;
  followingsibling_axis *axis;

  if (!PyArg_ParseTuple(args, "O!:following_sibling_axis",
                        Domlette->Node_Type, &node)) {
    return NULL;
  }

  axis = (followingsibling_axis *)type->tp_alloc(type, 0);
  if (axis == NULL) {
    return NULL;
  }
  axis->parent = Node_GET_PARENT(node);
  Py_XINCREF(axis->parent);
  if (axis->parent) {
    assert(Element_Check(axis->parent) || Entity_Check(axis->parent));
    axis->count = Container_GET_COUNT(axis->parent);
    for (axis->index = 0; axis->index < axis->count; axis->index++) {
      if (Container_GET_CHILD(axis->parent, axis->index) == node) {
        /* advance to the following node */
        axis->index++;
        break;
      }
    }
  } else {
    axis->index = axis->count = 0;
  }
  return (PyObject *)axis;
}

static void followingsibling_axis_dealloc(followingsibling_axis *self)
{
  Py_XDECREF(self->parent);
  self->ob_type->tp_free(self);
}

static PyObject *followingsibling_axis_next(followingsibling_axis *self)
{
  PyObject *node;

  if (self->index < self->count) {
    node = (PyObject *)Container_GET_CHILD(self->parent, self->index++);
    Py_INCREF(node);
    return node;
  }
  return NULL;
}

static PyTypeObject followingsibling_axis_type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME "." "following_sibling_axis",
  /* tp_basicsize      */ sizeof(followingsibling_axis),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) followingsibling_axis_dealloc,
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
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) followingsibling_axis_next,
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
  /* tp_new            */ (newfunc) followingsibling_axis_new,
  /* tp_free           */ 0,
};

/** NamespaceAxis object ******************************************/

typedef struct {
  PyObject_HEAD
  PyObject *namespaces;
  Py_ssize_t pos;
} namespace_axis;

static PyObject *namespace_axis_new(PyTypeObject *type, PyObject *args,
                                    PyObject *kwds)
{
  PyObject *node;
  namespace_axis *axis;

  if (!PyArg_ParseTuple(args, "O!:namespace_axis",
                        Domlette->Node_Type, &node))
    return NULL;

  axis = (namespace_axis *)type->tp_alloc(type, 0);
  if (axis == NULL) {
    return NULL;
  }
  if (Element_Check(node)) {
    axis->namespaces = Element_InscopeNamespaces(Element(node));
    if (axis->namespaces == NULL) {
      Py_DECREF(axis);
      return NULL;
    }
    axis->pos = 0;
  }
  return (PyObject *)axis;
}

static void namespace_axis_dealloc(namespace_axis *self)
{
  Py_CLEAR(self->namespaces);
  self->ob_type->tp_free(self);
}

static PyObject *namespace_axis_next(namespace_axis *self)
{
  if (self->namespaces != NULL) {
    NamespaceObject *node;
    while ((node = NamespaceMap_Next(self->namespaces, &self->pos))) {
      Py_INCREF(node);
      return (PyObject *)node;
    }
    Py_CLEAR(self->namespaces);
  }
  return NULL;
}

static PyTypeObject namespace_axis_type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME "." "namespace_axis",
  /* tp_basicsize      */ sizeof(namespace_axis),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) namespace_axis_dealloc,
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
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) namespace_axis_next,
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
  /* tp_new            */ (newfunc) namespace_axis_new,
  /* tp_free           */ 0,
};

/** Module Initialization ********************************************/

static PyMethodDef module_methods[] = {
  { NULL }
};

PyMODINIT_FUNC MODULE_INITFUNC(void)
{
  PyObject *module;
  PyTypeObject *typelist[] = {
    &ancestor_axis_type,
    &ancestor_self_axis_type,
    &attribute_axis_type,
    &child_axis_type,
    &descendant_axis_type,
    &descendant_self_axis_type,
    &followingsibling_axis_type,
    &namespace_axis_type,
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

  /* get the namespace constants */
  module = PyImport_ImportModule("amara");
  if (module == NULL) return;
  xmlns_namespace = PyObject_GetAttrString(module, "XMLNS_NAMESPACE");
  if (xmlns_namespace == NULL) return;
  Py_DECREF(module);
}
