#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

/* defined here as other implementations shouldn't be mucking with the
 * internals.
 */
#define Container_SET_COUNT(op, v) (Container_GET_COUNT(op) = (v))
#define Container_GET_NODES(op) (((ContainerObject *)(op))->nodes)
#define Container_SET_NODES(op, v) (Container_GET_NODES(op) = (v))
#define Container_GET_ALLOCATED(op) (((ContainerObject *)(op))->allocated)
#define Container_SET_ALLOCATED(op, v) (Container_GET_ALLOCATED(op) = (v))
#define Container_GET_CHILD(op, i) (((ContainerObject *)(op))->nodes[i])
#define Container_SET_CHILD(op, i, v) (Container_GET_CHILD((op), (i)) = (v))

static PyObject *inserted_event;
static PyObject *removed_event;

/* Ensure `nodes` has room for at least `newsize` elements, and set
 * `count` to `newsize`.  If `newsize` > `count` on entry, the content
 * of the new slots at exit is undefined heap trash; it's the caller's
 * responsiblity to overwrite them with sane values.
 * The number of allocated elements may grow, shrink, or stay the same.
 * Failure is impossible if `newsize <= `allocated` on entry, although
 * that partly relies on an assumption that the system realloc() never
 * fails when passed a number of bytes <= the number of bytes last
 * allocated (the C standard doesn't guarantee this, but it's hard to
 * imagine a realloc implementation where it wouldn't be true).
 * Note that `self->nodes` may change, and even if `newsize` is less
 * than `count` on entry.
 */
Py_LOCAL_INLINE(int)
container_resize(ContainerObject *self, Py_ssize_t newsize) {
  NodeObject **nodes;
  size_t new_allocated;
  Py_ssize_t allocated = self->allocated;

  /* Bypass realloc() when a previous overallocation is large enough
     to accommodate the newsize.  If the newsize falls lower than half
     the allocated size, then proceed with the realloc() to shrink the list.
  */
  if (allocated >= newsize && newsize >= (allocated >> 1)) {
    self->count = newsize;
    return 0;
  }

  /* This over-allocates proportional to the list size, making room
   * for additional growth.  The over-allocation is mild, but is
   * enough to give linear-time amortized behavior over a long
   * sequence of appends() in the presence of a poorly-performing
   * system realloc().
   * The growth pattern is:  0, 4, 8, 16, 25, 35, 46, 58, 72, 88, ...
   */
  new_allocated = (newsize >> 3) + (newsize < 9 ? 3 : 6) + newsize;
  if (newsize == 0)
    new_allocated = 0;
  nodes = self->nodes;
  if (new_allocated <= ((~(size_t)0) / sizeof(NodeObject *)))
    PyMem_Resize(nodes, NodeObject *, new_allocated);
  else
    nodes = NULL;
  if (nodes == NULL) {
    PyErr_NoMemory();
    return -1;
  }
  self->nodes = nodes;
  self->count = newsize;
  self->allocated = new_allocated;
  return 0;
}

Py_LOCAL_INLINE(int)
ensure_arguments(NodeObject *self, NodeObject *child)
{
  /* check argument types */
  if (self == NULL || !Container_Check(self) || child == NULL) {
    PyErr_BadInternalCall();
    return 0;
  }
  /* everything is OK */
  return 1;
}

Py_LOCAL_INLINE(int)
ensure_hierarchy(NodeObject *self, NodeObject *child)
{
  /* check argument types */
  if (!ensure_arguments(self, child))
    return 0;
  /* check for allowed child node types */
  if (!(Element_Check(child) || Text_Check(child) || Comment_Check(child) ||
        ProcessingInstruction_Check(child))) {
    PyErr_Format(PyExc_ValueError, "'%s' objects are not allowed as children",
                 child->ob_type->tp_name);
    return 0;
  }
  /* check for circular insertions; `child` as an ancestor of `self` */
  do {
    if (child == self) {
      PyErr_Format(PyExc_ValueError, "child is already an ancestor");
      return 0;
    }
    self = Node_GET_PARENT(self);
  } while (self != NULL);
  /* everything is OK */
  return 1;
}

Py_LOCAL_INLINE(int)
try_dispatch_event(NodeObject *self, PyObject *event, NodeObject *target)
{
  if (!Element_CheckExact(self) && !Entity_CheckExact(self)) {
    return Node_DispatchEvent(self, event, target);
  }
  return 0;
}

Py_LOCAL_INLINE(Py_ssize_t)
container_index(NodeObject *self, NodeObject *child,
                Py_ssize_t start, register Py_ssize_t stop)
{
  register NodeObject **nodes = Container_GET_NODES(self);
  register Py_ssize_t count = Container_GET_COUNT(self);
  register Py_ssize_t index;

  if (start < 0) {
    start += count;
    if (start < 0)
      start = 0;
  }
  if (stop < 0) {
    stop += count;
    if (stop < 0)
      stop = 0;
  } else if (stop > count) {
    stop = count;
  }
  for (index = start; index < stop; index++) {
    if (nodes[index] == child)
      return index;
  }
  PyErr_Format(PyExc_ValueError, "child not in children");
  return -1;
}

/** Public C API ******************************************************/

void _Container_Del(NodeObject *node)
{
  NodeObject **nodes = Container_GET_NODES(node);
  if (nodes) {
    Py_ssize_t i = Container_GET_COUNT(node);
    while (--i >= 0) {
      Py_DECREF(nodes[i]);
    }
    PyMem_Free(nodes);
  }
  _Node_Del(node);
}

/* Semi-private routine for bulk addition of children to a node.
 * This routine is valid for newly contructed container-style nodes which
 * haven't had any children added to them.
 */
int _Container_SetChildren(NodeObject *self, NodeObject **array,
                           Py_ssize_t size)
{
  NodeObject **nodes;
  Py_ssize_t i;

  if (!Container_Check(self) || Container_GET_NODES(self) != NULL) {
    PyErr_BadInternalCall();
    return -2;
  }

  /* Create a copy of the array */
  nodes = PyMem_New(NodeObject *, size);
  if (nodes == NULL) {
    PyErr_NoMemory();
    return -2;
  }
  memcpy(nodes, array, sizeof(NodeObject *)*size);

  /* Set the parent relationship */
  for (i = 0; i < size; i++) {
    assert(Node_GET_PARENT(nodes[i]) == NULL);
    Py_INCREF(self);
    Node_SET_PARENT(nodes[i], self);
  }

  /* Save the new array */
  Container_SET_NODES(self, nodes);
  Container_SET_COUNT(self, size);
  Container_SET_ALLOCATED(self, size);

  if (!Element_CheckExact(self) && !Entity_CheckExact(self)) {
    for (i = 0; i < size; i++) {
      if (Node_DispatchEvent(self, inserted_event, nodes[i]) < 0)
        return -1;
    }
  }
  return 0;
}

int Container_Remove(NodeObject *self, NodeObject *child)
{
  register NodeObject **nodes;
  register Py_ssize_t count, index;

  if (!ensure_arguments(self, child))
    return -1;

  /* Find the index of the child to be removed */
  nodes = Container_GET_NODES(self);
  count = Container_GET_COUNT(self);
  for (index = count; --index >= 0;) {
    if (nodes[index] == child)
      break;
  }
  if (index == -1) {
    PyErr_Format(PyExc_ValueError, "child not in children");
    return -1;
  }

  /* Announce the removal of the child. */
  if (try_dispatch_event(self, removed_event, child) < 0)
    return -1;

  /* Set the parent to NULL, indicating no parent */
  assert(Node_GET_PARENT(child) == self);
  Py_DECREF(Node_GET_PARENT(child));
  Node_SET_PARENT(child, NULL);

  /* Now shift the nodes in the array over the top of the removed node */
  memmove(&nodes[index], &nodes[index+1],
          (count - (index + 1)) * sizeof(NodeObject *));
  container_resize((ContainerObject *)self, count - 1);

  /* Drop the reference to the removed node as it is no longer in the array */
  Py_DECREF(child);

  return 0;
}

int Container_Append(NodeObject *self, NodeObject *child)
{
  Py_ssize_t count;

  if (!ensure_hierarchy(self, child))
    return -1;

  /* Make room for the new child */
  count = Container_GET_COUNT(self);
  if (container_resize((ContainerObject *)self, count+1) < 0)
    return -1;

  /* If the child has a previous parent, remove it from that parent */
  if (Node_GET_PARENT(child) != NULL) {
    if (Container_Remove(Node_GET_PARENT(child), child) < 0) {
      /* Forget the new size; it is OK to leave the resize intact */
      Container_SET_COUNT(self, count);
      return -1;
    }
    assert(Node_GET_PARENT(child) == NULL);
  }

  /* Add the new child to the end of our array */
  Py_INCREF(child);
  Container_SET_CHILD(self, count, child);

  /* Set the parent relationship */
  Py_INCREF(self);
  Node_SET_PARENT(child, self);

  /* Almost done; announce the addition of the child. */
  return try_dispatch_event(self, inserted_event, child);
}

int Container_Insert(NodeObject *self, Py_ssize_t where, NodeObject *child)
{
  register NodeObject **nodes;
  register Py_ssize_t count, i;

  if (!ensure_hierarchy(self, child)) {
    return -1;
  }

  /* Find the index of the reference node */
  count = Container_GET_COUNT(self);
  if (count == PY_SSIZE_T_MAX) {
    PyErr_SetString(PyExc_OverflowError, "cannot add more nodes to children");
    return -1;
  }

  /* Make room for the new child */
  if (container_resize((ContainerObject *)self, count+1) == -1)
    return -1;

  /* If the child has a previous parent, remove it from that parent */
  if (Node_GET_PARENT(child) != NULL) {
    if (Container_Remove(Node_GET_PARENT(child), child) < 0) {
      /* Forget the new size; it is OK to leave the resize intact */
      Container_SET_COUNT(self, count);
      return -1;
    }
    assert(Node_GET_PARENT(child) == NULL);
  }

  if (where < 0) {
    where += count;
    if (where < 0)
      where = 0;
  } else if (where > count)
    where = count;

  /* The pointer to nodes may have changed do to the resize */
  nodes = Container_GET_NODES(self);
  /* Shift the effected nodes up one */
  for (i = count; --i >= where;)
    nodes[i+1] = nodes[i];
  /* Insert the newChild at the found index in the array */
  Py_INCREF(child);
  Container_SET_CHILD(self, where, child);

  /* Set the parent relationship */
  Py_INCREF(self);
  Node_SET_PARENT(child, self);

  /* Almost done; announce the addition of the child. */
  return try_dispatch_event(self, inserted_event, child);
}

int Container_Replace(NodeObject *self, NodeObject *oldChild,
                      NodeObject *newChild)
{
  register NodeObject **nodes;
  register Py_ssize_t count, index;

  /* Find the index of the child to be replaced */
  nodes = Container_GET_NODES(self);
  count = Container_GET_COUNT(self);
  for (index = count; --index >= 0;) {
    if (nodes[index] == oldChild)
      break;
  }
  if (index == -1) {
    PyErr_Format(PyExc_ValueError, "child not in children");
    return -1;
  }
  assert(Node_GET_PARENT(oldChild) == self);

  /* Special case, oldChild is newChild -- nothing to do */
  if (oldChild == newChild)
    return 0;

  /* Announce the removal of `oldChild`. */
  if (try_dispatch_event(self, removed_event, oldChild) < 0)
    return -1;

  /* If `newChild` has a previous parent, remove it from that parent */
  if (Node_GET_PARENT(newChild) != NULL) {
    if (Container_Remove(Node_GET_PARENT(newChild), newChild) < 0) {
      return -1;
    }
    assert(Node_GET_PARENT(newChild) == NULL);
  }

  /* Set the parent for `oldChild` to NULL, indicating no parent */
  Py_DECREF(Node_GET_PARENT(oldChild));
  Node_SET_PARENT(oldChild, NULL);

  /* Remove it from the nodes array (just drop the reference to it as its
   * spot will soon be taken by `newChild`) */
  Py_DECREF(oldChild);

  /* Insert `newChild` at the found index in the array */
  Py_INCREF(newChild);
  Container_SET_CHILD(self, index, newChild);

  /* Set the parent relationship */
  Py_INCREF(self);
  Node_SET_PARENT(newChild, self);

  /* Almost done; announce the insertion of `newChild`. */
  return try_dispatch_event(self, inserted_event, newChild);
}

Py_ssize_t Container_Index(NodeObject *self, NodeObject *child)
{
  if (!ensure_arguments(self, child))
    return -1;
  return container_index(self, child, 0, Container_GET_COUNT(self));
}

/** Python Methods ****************************************************/

static char xml_normalize_doc[] = "\
Puts all Text nodes in the full depth of the sub-tree underneath this Node,\n\
including attribute nodes, into a \"normal\" form where only structure\n\
(e.g., elements, comments, processing instructions, CDATA sections, and\n\
entity references) separates Text nodes, i.e., there are neither adjacent\n\
Text nodes nor empty Text nodes.";

static PyObject *xml_normalize(NodeObject *self, PyObject *args)
{
  Py_ssize_t i, count;

  if (!PyArg_ParseTuple(args, ":xml_normalize"))
    return NULL;

  if (Container_GET_COUNT(self) < 2) {
    Py_INCREF(Py_None);
    return Py_None;
  }

  /* Count to the length minus 1 as the last node has no following sibling
   * with which to be merged. */
  for (i = 0, count = Container_GET_COUNT(self); i < count; i++) {
    NodeObject *current = Container_GET_CHILD(self, i);
    /* If this node is a Text node, determine if following siblings are also
     * Text nodes.
     */
    if (Text_Check(current)) {
      /* Loop over the following siblings */
      for (i++; i < count; count--) {
        PyObject *current_value, *next_value, *new_value;
        Py_UNICODE *raw_value;
        NodeObject *next = Container_GET_CHILD(self, i);
        if (!Text_Check(next)) break;
        /* Adjacent Text nodes; merge their data. */
        current_value = Text_GET_VALUE(current);
        next_value = Text_GET_VALUE(next);
        new_value = PyUnicode_FromUnicode(NULL,
                                          PyUnicode_GET_SIZE(current_value) +
                                          PyUnicode_GET_SIZE(next_value));
        if (new_value == NULL) return NULL;
        raw_value = PyUnicode_AS_UNICODE(new_value);
        Py_UNICODE_COPY(raw_value, PyUnicode_AS_UNICODE(current_value),
                        PyUnicode_GET_SIZE(current_value));
        raw_value += PyUnicode_GET_SIZE(current_value);
        Py_UNICODE_COPY(raw_value, PyUnicode_AS_UNICODE(next_value),
                        PyUnicode_GET_SIZE(next_value));
        Text_SET_VALUE(current, new_value);
        Py_DECREF(current_value);

        /* Remove the sibling. */
        if (Container_Remove(self, next) < 0)
          return NULL;
      }
    }
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static char xml_remove_doc[] = "xml_remove(child) -> child\n\n\
Removes the child node indicated by `child` from the children.";

static PyObject *xml_remove(NodeObject *self, PyObject *args)
{
  NodeObject *child;

  if (!PyArg_ParseTuple(args, "O!:xml_remove", &DomletteNode_Type, &child))
    return NULL;

  if (Container_Remove(self, child) == -1)
    return NULL;

  Py_INCREF(child);
  return (PyObject *)child;
}

static char xml_append_doc[] = "xml_append(child) -> child\n\n\
Adds the node `child` to the end of the children of this node.";

static PyObject *xml_append(NodeObject *self, PyObject *args)
{
  NodeObject *child;

  if (!PyArg_ParseTuple(args,"O!:xml_append", &DomletteNode_Type, &child))
    return NULL;

  if (Container_Append(self, child) == -1)
    return NULL;

  Py_INCREF(child);
  return (PyObject *)child;
}

static char xml_insert_doc[] = "xml_insert(index, child) -> child\n\n\
Insert a new node `child` in the children before position `index`.\n\
Negative values are treated as being relative to the end of the children.";

static PyObject *xml_insert(NodeObject *self, PyObject *args)
{
  Py_ssize_t index;
  NodeObject *child;

  if (!PyArg_ParseTuple(args, "nO!:xml_insert", &index,
                        &DomletteNode_Type, &child))
    return NULL;

  if (Container_Insert(self, index, child) == -1)
    return NULL;

  Py_INCREF(child);
  return (PyObject *)child;
}

static char xml_replace_doc[] = "xml_replace(old, new) -> old\n\n\
Replaces the node `old` with the node `new` in the children.";

static PyObject *xml_replace(NodeObject *self, PyObject *args)
{
  NodeObject *oldChild, *newChild;

  if (!PyArg_ParseTuple(args, "O!O!:xml_replace",
                        &DomletteNode_Type, &oldChild,
                        &DomletteNode_Type, &newChild))
    return NULL;

  if (Container_Replace(self, oldChild, newChild) < 0)
    return NULL;

  Py_INCREF(oldChild);
  return (PyObject *)oldChild;
}

static char xml_index_doc[] = "xml_index(child[, start, [stop]) -> integer\n\n\
Returns the index of `child` in the children.";

static PyObject *xml_index(NodeObject *self, PyObject *args)
{
  NodeObject *child;
  Py_ssize_t index, start=0, stop=Container_GET_COUNT(self);

  if (!PyArg_ParseTuple(args, "O!|O&O&:index",
                        &DomletteNode_Type, &child,
                        _PyEval_SliceIndex, &start,
                        _PyEval_SliceIndex, &stop))
    return NULL;
  index = container_index(self, child, start, stop);
  if (index < 0)
    return PyErr_Format(PyExc_ValueError, "child not in children");
  else
    return PyInt_FromSsize_t(index);
}

static char xml_child_inserted_doc[] = "xml_child_inserted(target)\n\n\
A node has been added as a child of another node. This event is dispatched\n\
after the insertion has taken place. The `target` node of this event is the\n\
node being inserted.";

static PyObject *xml_child_inserted(PyObject *self, PyObject *child)
{
  Py_RETURN_NONE;
}

static char xml_child_removed_doc[] = "xml_child_inserted(target)\n\n\
A node is being removed from its parent node. This event is dispatched\n\
before the node is removed from the tree. The `target` node of this event is\n\
the node being removed.";

static PyObject *xml_child_removed(PyObject *self, PyObject *child)
{
  Py_RETURN_NONE;
}

#define PyMethod_INIT(NAME, FLAGS) \
  { #NAME, (PyCFunction)NAME, FLAGS, NAME##_doc }

static PyMethodDef container_methods[] = {
  PyMethod_INIT(xml_normalize, METH_VARARGS),
  PyMethod_INIT(xml_remove,    METH_VARARGS),
  PyMethod_INIT(xml_append,    METH_VARARGS),
  PyMethod_INIT(xml_insert,    METH_VARARGS),
  PyMethod_INIT(xml_replace,   METH_VARARGS),
  PyMethod_INIT(xml_index,     METH_VARARGS),
  /* mutation events */
  PyMethod_INIT(xml_child_inserted, METH_O),
  PyMethod_INIT(xml_child_removed,  METH_O),
  { NULL }
};

/** Python Members ****************************************************/

static PyMemberDef container_members[] = {
  { NULL }
};

/** Python Computed Members *******************************************/

static PyObject *get_children(PyObject *self, void *arg)
{
  register Py_ssize_t count;
  register Py_ssize_t index;
  register PyObject *children;

  count = Container_GET_COUNT(self);
  children = PyTuple_New(count);
  if (children != NULL) {
    for (index = 0; index < count; index++) {
      PyObject *child = (PyObject *)Container_GET_CHILD(self, index);
      Py_INCREF(child);
      PyTuple_SET_ITEM(children, index, child);
    }
  }
  return children;
}

static PyObject *get_first_child(PyObject *self, void *arg)
{
  PyObject *child;
  if (Container_GET_COUNT(self) > 0)
    child = (PyObject *)Container_GET_CHILD(self, 0);
  else
    child = Py_None;
  Py_INCREF(child);
  return child;
}

static PyObject *get_last_child(PyObject *self, void *arg)
{
  PyObject *child;
  Py_ssize_t count = Container_GET_COUNT(self);
  if (count > 0)
    child = (PyObject *)Container_GET_CHILD(self, count-1);
  else
    child = Py_None;
  Py_INCREF(child);
  return child;
}

static PyGetSetDef container_getset[] = {
  { "xml_children", get_children },
  { "xml_first_child", get_first_child },
  { "xml_last_child", get_last_child },
  { NULL }
};

/** Type Object *******************************************************/

static int container_traverse(PyObject *self, visitproc visit, void *arg)
{
  register NodeObject **nodes = Container_GET_NODES(self);
  register Py_ssize_t i = Container_GET_COUNT(self);
  while (--i >= 0)
    Py_VISIT(nodes[i]);
  return DomletteNode_Type.tp_traverse(self, visit, arg);
}

static int container_clear(PyObject *self)
{
  register NodeObject **nodes = Container_GET_NODES(self);
  register Py_ssize_t i = Container_GET_COUNT(self);
  if (nodes != NULL) {
    Container_SET_NODES(self, NULL);
    Container_SET_COUNT(self, 0);
    Container_SET_ALLOCATED(self, 0);
    while (--i >= 0) {
      Py_DECREF(nodes[i]);
    }
    PyMem_Free(nodes);
  }
  return DomletteNode_Type.tp_clear(self);
}

static PyObject *container_iter(NodeObject *node);

PyTypeObject DomletteContainer_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "container",
  /* tp_basicsize      */ sizeof(ContainerObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) _Container_Del,
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
                           Py_TPFLAGS_BASETYPE |
                           Py_TPFLAGS_HAVE_GC),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) container_traverse,
  /* tp_clear          */ (inquiry) container_clear,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) container_iter,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) container_methods,
  /* tp_members        */ (PyMemberDef *) container_members,
  /* tp_getset         */ (PyGetSetDef *) container_getset,
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

/** Node ChildNodes Iterator ******************************************/

typedef struct {
  PyObject_HEAD
  Py_ssize_t index;
  NodeObject *node; /* NULL when iterator is done */
} NodeIterObject;

static PyTypeObject NodeIter_Type;

static PyObject *container_iter(NodeObject *node)
{
  NodeIterObject *iter;

  iter = PyObject_GC_New(NodeIterObject, &NodeIter_Type);
  if (iter != NULL) {
    iter->index = 0;
    Py_INCREF(node);
    iter->node = node;
    PyObject_GC_Track(iter);
  }
  return (PyObject *)iter;
}

static void nodeiter_dealloc(NodeIterObject *iter)
{
  PyObject_GC_UnTrack(iter);
  Py_XDECREF(iter->node);
  PyObject_GC_Del(iter);
}

static int nodeiter_traverse(NodeIterObject *iter, visitproc visit, void *arg)
{
  if (iter->node == NULL)
    return 0;
  return visit((PyObject *)iter->node, arg);
}

static PyObject *nodeiter_next(NodeIterObject *iter)
{
  NodeObject *node = iter->node;
  if (node == NULL)
    return NULL;

  if (iter->index < Container_GET_COUNT(node)) {
    PyObject *item = (PyObject *)Container_GET_CHILD(node, iter->index++);
    Py_INCREF(item);
    return item;
  }

  Py_DECREF(node);
  iter->node = NULL;
  return NULL;
}

static PyTypeObject NodeIter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "nodeiterator",
  /* tp_basicsize      */ sizeof(NodeIterObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) nodeiter_dealloc,
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
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) nodeiter_traverse,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) nodeiter_next,
};

/** Module Interface **************************************************/

int DomletteContainer_Init(PyObject *module)
{
  /* Initialize type object */
  DomletteContainer_Type.tp_base = &DomletteNode_Type;
  if (PyType_Ready(&DomletteContainer_Type) < 0)
    return -1;

  /* Grrrr...MingW32 gcc doesn't support assigning imported functions in a
   * static structure.  This sucks because both gcc/Unix and MSVC both support
   * that.
   */
  NodeIter_Type.tp_getattro = PyObject_GenericGetAttr;
  NodeIter_Type.tp_iter = PyObject_SelfIter;
  if (PyType_Ready(&NodeIter_Type) < 0)
    return -1;

  inserted_event = PyString_FromString("xml_child_inserted");
  if (inserted_event == NULL)
    return -1;
  removed_event = PyString_FromString("xml_child_removed");
  if (removed_event == NULL)
    return -1;

  return 0;
}

void DomletteContainer_Fini(void)
{
  Py_DECREF(inserted_event);
  Py_DECREF(removed_event);
  PyType_CLEAR(&DomletteContainer_Type);
  PyType_CLEAR(&NodeIter_Type);
}
