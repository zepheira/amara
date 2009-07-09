 #define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

static PyTypeObject NamespaceMap_Type;
static PyTypeObject KeyIter_Type;
static PyTypeObject ValueIter_Type;
static PyTypeObject ItemIter_Type;
static PyTypeObject NodeIter_Type;

#define NamespaceMap_Check(op) PyObject_TypeCheck(op, &NamespaceMap_Type)
#define NamespaceMap_CheckExact(op) ((op)->ob_type == &NamespaceMap_Type)

#define INIT_MINSIZE(op) do {                                       \
  (op)->nm_used = 0;                                                \
  (op)->nm_mask = NamespaceMap_MINSIZE - 1;                         \
  (op)->nm_table = (op)->nm_smalltable;                             \
  memset((op)->nm_smalltable, 0, sizeof(op->nm_smalltable));        \
} while(0)

#define NAME_EQ(a, b) \
  ((((a) == Py_None || (b) == Py_None) && (a) == (b)) || \
   (PyUnicode_GET_SIZE(a) == PyUnicode_GET_SIZE(b) && \
    *PyUnicode_AS_UNICODE(a) == *PyUnicode_AS_UNICODE(b) && \
    !memcmp(PyUnicode_AS_UNICODE(a), PyUnicode_AS_UNICODE(b), \
           PyUnicode_GET_DATA_SIZE(a))))

Py_LOCAL_INLINE(long)
get_hash(PyObject *name)
{
  register long hash;

  if (name == Py_None)
    hash = 0;
  else if (!PyUnicode_CheckExact(name) ||
           (hash = ((PyUnicodeObject *)name)->hash) == -1)
    hash = PyObject_Hash(name);
  return hash;
}

Py_LOCAL_INLINE(int)
key_eq(NamespaceObject *node, Py_ssize_t hash, register PyObject *name)
{
  register PyObject *node_name = node->name;
  return node_name == name || (node->hash == hash && NAME_EQ(node_name, name));
}

Py_LOCAL_INLINE(size_t)
get_entry(NamespaceMapObject *nm, Py_ssize_t hash, PyObject *name)
{
  register size_t perturb = hash;
  register size_t mask = (size_t)nm->nm_mask;
  register size_t i = perturb & mask;
  register size_t entry = i;
  NamespaceObject **table = nm->nm_table;

  while (table[entry] && !key_eq(table[entry], hash, name)) {
    i = (i << 2) + i + perturb + 1;
    perturb >>= 5;
    entry = i & mask;
  }
  return entry;
}

Py_LOCAL_INLINE(void)
set_entry(NamespaceMapObject *nm, NamespaceObject *node)
{
  register size_t perturb = node->hash;
  register size_t mask = (size_t)nm->nm_mask;
  register size_t i = perturb & mask;
  register size_t entry = i;
  NamespaceObject **table = nm->nm_table;

  while (table[entry] != NULL) {
    i = (i << 2) + i + perturb + 1;
    perturb >>= 5;
    entry = i & mask;
  }
  table[entry] = node;
}

Py_LOCAL_INLINE(NamespaceObject *)
next_entry(NamespaceMapObject *nm, Py_ssize_t *ppos)
{
  register Py_ssize_t i = *ppos;
  register Py_ssize_t mask = nm->nm_mask;
  register NamespaceObject **table = nm->nm_table;

  if (i < 0)
    return NULL;
  while (i <= mask && table[i] == NULL) i++;
  *ppos = i+1;
  if (i > mask)
    return NULL;
  return table[i];
}

/*
Restructure the table by allocating a new table and reinserting all
items again.  When entries have been deleted, the new table may
actually be smaller than the old one.
*/
Py_LOCAL(int)
resize_table(NamespaceMapObject *self)
{
  NamespaceObject **oldtable, **newtable;
  Py_ssize_t size, i;

  /* Get space for a new table. */
  oldtable = self->nm_table;
  size = (self->nm_mask + 1) << 1;
  if (size <= NamespaceMap_MINSIZE) {
    size = NamespaceMap_MINSIZE;
    newtable = self->nm_smalltable;
    if (oldtable == newtable)
      return 0;
  } else {
    newtable = PyMem_New(NamespaceObject *, size);
    if (newtable == NULL) {
      PyErr_NoMemory();
      return -1;
    }
  }

  /* Make the dict empty, using the new table. */
  self->nm_table = newtable;
  self->nm_mask = size - 1;
  memset(newtable, 0, sizeof(NamespaceObject *) * size);

  /* Copy the data over */
  for (i = 0, size = self->nm_used; size > 0; i++) {
    NamespaceObject *entry = oldtable[i];
    if (entry != NULL) {
      size--;
      set_entry(self, entry);
    }
  }

  if (oldtable != self->nm_smalltable)
    PyMem_Free(oldtable);
  return 0;
}

Py_LOCAL_INLINE(PyObject *)
parse_key(PyObject *key, int node_allowed)
{
  PyObject *name;

  if (key == Py_None || PyUnicode_Check(key)) {
    name = key;
    Py_INCREF(name);
  } else if (node_allowed && Namespace_Check(key)) {
    name = Namespace_GET_NAME(key);
    Py_INCREF(name);
  } else {
    const char *str;
    Py_ssize_t len;
    if (PyString_Check(key)) {
      if (PyString_AsStringAndSize(key, (char **)&str, &len) < 0)
        return NULL;
    } else if (PyObject_AsCharBuffer(key, &str, &len) < 0) {
      if (!PyErr_ExceptionMatches(PyExc_TypeError))
        return NULL;
    } else {
      PyErr_Format(PyExc_KeyError,
                   "subscript must be unicode string, UTF-8 byte-string"
                   "%s or None, not '%s'",
                   node_allowed ? ", namespace instance" : "",
                   key->ob_type->tp_name);
      return NULL;
    }
    name = PyUnicode_Decode(str, len, "utf-8", NULL);
  }
  return name;
}

/** Public C API ******************************************************/

void _NamespaceMap_Dump(NamespaceMapObject *nm)
{
  Py_ssize_t i;
  if (nm == NULL)
    fprintf(stderr, "NULL\n");
  else {
    fprintf(stderr, "object  : ");
    (void)PyObject_Print((PyObject *)nm, stderr, 0);
    /* XXX(twouters) cast refcount to long until %zd is
        universally available */
    fprintf(stderr, "\n"
            "nm_used : %ld\n"
            "nm_mask : %ld\n",
            (long)nm->nm_used, (long)nm->nm_mask);
    for (i = 0; i <= nm->nm_mask; i++) {
      fprintf(stderr, "nm_table[%ld]: ", (long)i);
      if (nm->nm_table[i] == NULL)
        fputs("NULL", stderr);
      else
        (void)PyObject_Print((PyObject *)nm->nm_table[i], stderr, 0);
      fputs("\n", stderr);
    }
  }
}

PyObject *
NamespaceMap_New(ElementObject *owner)
{
  register NamespaceMapObject *self;

  self = PyObject_GC_New(NamespaceMapObject, &NamespaceMap_Type);
  if (self != NULL) {
    INIT_MINSIZE(self);
    self->nm_owner = owner;
    Py_INCREF(owner);
    PyObject_GC_Track(self);
  }
  return (PyObject *)self;
}

Py_ssize_t
NamespaceMap_GetHash(PyObject *name)
{
  return get_hash(name);
}

NamespaceObject *
NamespaceMap_GetNode(PyObject *self, PyObject *name)
{
  NamespaceMapObject *nm = (NamespaceMapObject *)self;
  size_t entry;
  long hash;

  if (!NamespaceMap_Check(nm)) {
    PyErr_BadInternalCall();
    return NULL;
  }
  if (name == Py_None || PyUnicode_Check(name)) {
    Py_INCREF(name);
  } else {
    name = XmlString_FromObject(name);
    if (name == NULL)
      return NULL;
  }
  hash = get_hash(name);
  if (hash == -1) {
    Py_DECREF(name);
    return NULL;
  }
  entry = get_entry(nm, hash, name);
  Py_DECREF(name);
  return nm->nm_table[entry];
}

int
NamespaceMap_SetNode(PyObject *self, NamespaceObject *node)
{
  NamespaceMapObject *nm = (NamespaceMapObject *)self;
  size_t entry;
  PyObject *name;
  long hash;
  NamespaceObject *old_node;
  NodeObject *temp;

  if (!NamespaceMap_Check(nm)) {
    PyErr_BadInternalCall();
    return -1;
  }
  hash = (long)Namespace_GET_HASH(node);
  name = Namespace_GET_NAME(node);
  entry = get_entry(nm, hash, name);
  old_node = nm->nm_table[entry];
  if (old_node == NULL) {
    /* adding the namespace to the table */
    nm->nm_used++;
  } else {
    /* replacing the old namespace in the table */
    Py_DECREF(old_node);
  }
  /* store the namespace in the table */
  nm->nm_table[entry] = node;
  Py_INCREF(node);
  /* update the naespace's owner */
  temp = Node_GET_PARENT(node);
  Node_SET_PARENT(node, (NodeObject *)nm->nm_owner);
  Py_INCREF(nm->nm_owner);
  Py_XDECREF(temp);
  /* If fill >= 2/3 size, adjust size.  Normally, this doubles the size, but
   * it's also possible for the dict to shrink. */
  if (nm->nm_used*3 >= (nm->nm_mask+1)*2) {
    if (resize_table(nm) < 0)
      return -1;
  }
  /* success */
  return 0;
}

int
NamespaceMap_DelNode(PyObject *self, PyObject *name)
{
  PyErr_SetString(PyExc_NotImplementedError, "NamespaceMap_DelNode");
  return -1;
}

NamespaceObject *
NamespaceMap_Next(PyObject *self, Py_ssize_t *ppos)
{
  return next_entry((NamespaceMapObject *)self, ppos);
}

/** Python Methods ****************************************************/

static PyObject *iter_new(NamespaceMapObject *self, PyTypeObject *type);

static char namespacemap_getnode_doc[] = "\
getnode(name) -> namespace node or None\n\
\n\
Retrieves a node specified by name or None \
if the name does not identify a node in this map.";

static PyObject *namespacemap_getnode(PyObject *self, PyObject *args)
{
  PyObject *name, *result;

  if (!PyArg_ParseTuple(args, "O:getnode", &name))
    return NULL;

  result = (PyObject *)NamespaceMap_GetNode(self, name);
  if (result == NULL) {
    if (PyErr_Occurred())
      return NULL;
    result = Py_None;
  }
  Py_INCREF(result);
  return result;
}

static char namespacemap_setnode_doc[] = "\
setnode(node) -> M[node.xml_name] = node.xml_value";

static PyObject *namespacemap_setnode(PyObject *self, PyObject *args)
{
  NamespaceObject *node;

  if (!PyArg_ParseTuple(args, "O!:setnode", &DomletteNamespace_Type, &node))
    return NULL;

  if (NamespaceMap_SetNode(self, node) < 0)
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char namespacemap_get_doc[] =
"M.get(k[,d]) -> M[k] if k in M, else d.  d defaults to None.";

static PyObject *namespacemap_get(PyObject *self, PyObject *args)
{
  PyObject *key, *result=Py_None;
  PyObject *name;
  NamespaceObject *node;

  if (!PyArg_ParseTuple(args, "O|O:get", &key, &result))
    return NULL;
  name = parse_key(key, 0);
  if (name == NULL) {
    if (!PyErr_ExceptionMatches(PyExc_KeyError))
      return NULL;
    PyErr_Clear();
    goto done;
  }
  node = NamespaceMap_GetNode(self, name);
  Py_DECREF(name);
  if (node == NULL) {
    if (PyErr_Occurred())
      return NULL;
  } else {
    result = Namespace_GET_VALUE(node);
  }
done:
  Py_INCREF(result);
  return result;
}

static char namespacemap_keys_doc[] =
"M.keys() -> list of prefixes";

static PyObject *namespacemap_keys(NamespaceMapObject *self)
{
  register PyObject *keys;
  register Py_ssize_t i, n;
  register NamespaceObject **ptr;

  n = self->nm_used;
  keys = PyList_New(n);
  if (keys == NULL)
    return NULL;
  for (i = 0, ptr = self->nm_table; i < n; ptr++) {
    NamespaceObject *node = *ptr;
    if (node != NULL) {
      PyObject *key = Namespace_GET_NAME(node);
      Py_INCREF(key);
      PyList_SET_ITEM(keys, i, key);
      i++;
    }
  }
  return keys;
}

static char namespacemap_values_doc[] =
"M.values() -> list of node values";

static PyObject *namespacemap_values(NamespaceMapObject *self)
{
  register PyObject *values;
  register Py_ssize_t i, n;
  register NamespaceObject **ptr;

  n = self->nm_used;
  values = PyList_New(n);
  if (values == NULL)
    return NULL;
  for (i = 0, ptr = self->nm_table; i < n; ptr++) {
    NamespaceObject *node = *ptr;
    if (node != NULL) {
      PyObject *value = Namespace_GET_VALUE(node);
      Py_INCREF(value);
      PyList_SET_ITEM(values, i, value);
      i++;
    }
  }
  return values;
}

static char namespacemap_items_doc[] =
"M.items() -> list of M's (prefix, uri) pairs, as 2-tuples";

static PyObject *namespacemap_items(NamespaceMapObject *self)
{
  register PyObject *items;
  register Py_ssize_t i, n;
  register NamespaceObject **ptr;

  n = self->nm_used;
  items = PyList_New(n);
  if (items == NULL)
    return NULL;
  for (i = 0, ptr = self->nm_table; i < n; ptr++) {
    NamespaceObject *node = *ptr;
    if (node != NULL) {
      PyObject *item = PyTuple_Pack(2, Namespace_GET_NAME(node),
                                    Namespace_GET_VALUE(node));
      if (item == NULL) {
        Py_DECREF(items);
        return NULL;
      }
      PyList_SET_ITEM(items, i, item);
      i++;
    }
  }
  return items;
}

static char namespacemap_copy_doc[] =
"M.copy() -> a copy of M as a dictionary";

static PyObject *namespacemap_copy(NamespaceMapObject *self)
{
  register PyObject *copy;
  register Py_ssize_t i, n;
  register NamespaceObject **ptr;

  copy = PyDict_New();
  if (copy == NULL)
    return NULL;
  for (i = 0, n = self->nm_used, ptr = self->nm_table; i < n; ptr++) {
    NamespaceObject *node = *ptr;
    if (node != NULL) {
      PyObject *key = Namespace_GET_NAME(node);
      PyObject *value = Namespace_GET_VALUE(node);
      if (PyDict_SetItem(copy, key, value) < 0) {
        Py_DECREF(copy);
        return NULL;
      }
      i++;
    }
  }
  return copy;
}

static char namespacemap_iterkeys_doc[] =
"M.iterkeys() -> an iterator over the expanded name 2-tuples of M";

static PyObject *namespacemap_iterkeys(NamespaceMapObject *self)
{
  return iter_new(self, &KeyIter_Type);
}

static char namespacemap_itervalues_doc[] =
"M.itervalues() -> an iterator over the node values of M";

static PyObject *namespacemap_itervalues(NamespaceMapObject *self)
{
  return iter_new(self, &ValueIter_Type);
}

static char namespacemap_iteritems_doc[] =
"M.iteritems() -> an iterator over the (expanded name, value) items of M";

static PyObject *namespacemap_iteritems(NamespaceMapObject *self)
{
  return iter_new(self, &ItemIter_Type);
}

static char namespacemap_nodes_doc[] =
"M.nodes() -> an iterator over the attribute nodes of M";

static PyObject *namespacemap_nodes(NamespaceMapObject *self)
{
  return iter_new(self, &NodeIter_Type);
}

#define NamespaceMap_METHOD(NAME, FLAGS)             \
  { #NAME, (PyCFunction) namespacemap_##NAME, FLAGS, \
      namespacemap_##NAME##_doc }

static PyMethodDef namespacemap_methods[] = {
  NamespaceMap_METHOD(getnode,    METH_VARARGS),
  NamespaceMap_METHOD(setnode,    METH_VARARGS),
  /* Python Mapping Interface */
  NamespaceMap_METHOD(get,        METH_VARARGS),
  NamespaceMap_METHOD(keys,       METH_NOARGS),
  NamespaceMap_METHOD(values,     METH_NOARGS),
  NamespaceMap_METHOD(items,      METH_NOARGS),
  NamespaceMap_METHOD(copy,       METH_NOARGS),
  NamespaceMap_METHOD(iterkeys,   METH_NOARGS),
  NamespaceMap_METHOD(itervalues, METH_NOARGS),
  NamespaceMap_METHOD(iteritems,  METH_NOARGS),
  NamespaceMap_METHOD(nodes,      METH_NOARGS),
  { NULL }
};

static Py_ssize_t
namespacemap_length(NamespaceMapObject *self)
{
  return self->nm_used;
}

static PyObject *
namespacemap_subscript(PyObject *op, PyObject *key)
{
  PyObject *name;
  NamespaceObject *node;

  name = parse_key(key, 0);
  if (name == NULL)
    return NULL;
  node = NamespaceMap_GetNode(op, name);
  Py_DECREF(name);
  if (node == NULL) {
    if (!PyErr_Occurred())
      PyErr_SetObject(PyExc_KeyError, key);
    return NULL;
  }
  Py_INCREF(Namespace_GET_VALUE(node));
  return Namespace_GET_VALUE(node);
}

static int
namespacemap_ass_subscript(PyObject *op, PyObject *key, PyObject *value)
{
  NamespaceMapObject *self = (NamespaceMapObject *)op;
  PyObject *name;
  int result;

  if (value == NULL) {
    /* __delitem__(key)
     * `key` can be Attr node or tuple of (namespace, name) or just name
     */
    name = parse_key(key, 1);
    if (name == NULL)
      return -1;
    result = NamespaceMap_DelNode(op, name);
  } else {
    /* __setitem__(key, value)
     * `key` can be tuple of (namespace, name) or just name
     */
    NamespaceObject *node;
    name = parse_key(key, 0);
    if (name == NULL)
      return -1;
    /* FIXME: validate value */
    value = XmlString_ConvertArgument(value, "value", 0);
    if (value == NULL) {
      Py_DECREF(name);
      return -1;
    }
    node = NamespaceMap_GetNode(op, name);
    if (node == NULL) {
      if (PyErr_Occurred()) {
        result = -1;
      } else {
        node = Element_AddNamespace(self->nm_owner, name, value);
        if (node == NULL) {
          result = -1;
        } else {
          Py_DECREF(node);
          result = 0;
        }
      }
      Py_DECREF(value);
    } else {
      /* just update the node value */
     Py_DECREF(Namespace_GET_VALUE(node));
     Namespace_SET_VALUE(node, value);
     result = 0;
    }
  }
  Py_DECREF(name);
  return result;
}

static PyMappingMethods namespacemap_as_mapping = {
  /* mp_length        */ (lenfunc) namespacemap_length,
  /* mp_subscript     */ (binaryfunc) namespacemap_subscript,
  /* mp_ass_subscript */ (objobjargproc) namespacemap_ass_subscript,
};

static int namespacemap_contains(NamespaceMapObject *self, PyObject *key)
{
  Py_ssize_t entry, hash;

  if (Namespace_Check(key)) {
    NamespaceObject *node;
    entry = 0;
    while ((node = next_entry(self, &entry))) {
      switch (PyObject_RichCompareBool(key, (PyObject *)node, Py_EQ)) {
        case 1:
          return 1;
        case 0:
          break;
        default:
          return -1;
      }
    }
    return 0;
  }
  if ((key = parse_key(key, 1)) == NULL) {
    if (PyErr_ExceptionMatches(PyExc_KeyError)) {
      PyErr_Clear();
      return 0;
    }
    return -1;
  }
  hash = get_hash(key);
  if (hash == -1) {
    Py_DECREF(key);
    return -1;
  }
  entry = get_entry(self, hash, key);
  Py_DECREF(key);
  return self->nm_table[entry] != NULL;
}

static PySequenceMethods namespacemap_as_sequence = {
  /* sq_length         */ 0,
  /* sq_concat         */ 0,
  /* sq_repeat         */ 0,
  /* sq_item           */ 0,
  /* sq_slice          */ 0,
  /* sq_ass_item       */ 0,
  /* sq_ass_slice      */ 0,
  /* sq_contains       */ (objobjproc) namespacemap_contains,
  /* sq_inplace_concat */ 0,
  /* sq_inplace_repeat */ 0,
};

/** Python Members ****************************************************/

static PyMemberDef namespacemap_members[] = {
  { NULL }
};

/** Python Computed Members *******************************************/

static PyGetSetDef namespacemap_getset[] = {
  { NULL }
};

/** Type Object ********************************************************/

static void namespacemap_dealloc(NamespaceMapObject *self)
{
  register NamespaceObject **table = self->nm_table;
  register size_t entry;
  register Py_ssize_t used;

  PyObject_GC_UnTrack(self);
  Py_XDECREF(self->nm_owner);
  Py_TRASHCAN_SAFE_BEGIN(self);
  for (entry = 0, used = self->nm_used; used > 0; entry++) {
    if (table[entry] != NULL) {
      used--;
      Py_DECREF(table[entry]);
    }
  }
  Py_TRASHCAN_SAFE_END(self);
  if (table != self->nm_smalltable)
    PyMem_Free(table);
  ((PyObject *)self)->ob_type->tp_free((PyObject *)self);
}

static PyObject *namespacemap_repr(NamespaceMapObject *self)
{
  return PyString_FromFormat("<namespacemap at %p: %zd nodes>",
                             self, self->nm_used);
}

static int namespacemap_traverse(NamespaceMapObject *self, visitproc visit,
                                 void *arg)
{
  Py_ssize_t i = 0;
  NamespaceObject *node;

  Py_VISIT(self->nm_owner);
  while ((node = next_entry(self, &i)))
    Py_VISIT(node);

  return 0;
}

static int namespacemap_clear(NamespaceMapObject *self)
{
  register NamespaceObject **table = self->nm_table;
  register Py_ssize_t used = self->nm_used;
  register size_t entry;
  NamespaceObject *smallcopy[NamespaceMap_MINSIZE];
  int malloced_table;

  Py_CLEAR(self->nm_owner);

  /* If it is a small table with something that needs to be cleared, the
   * only safe way is to copy the entries into another small table first.
   */
  malloced_table = (table != self->nm_smalltable);
  if (!malloced_table && used) {
    memcpy(smallcopy, table, sizeof(smallcopy));
    table = smallcopy;
  }

  /* Because DECREF's can cause the map to mutate, we make it empty first */
  INIT_MINSIZE(self);

  /* Now finally clear things */
  for (entry = 0; used > 0; entry++) {
    if (table[entry] != NULL) {
      used--;
      Py_DECREF(table[entry]);
    }
  }

  if (malloced_table)
    PyMem_Free(table);

  return 0;
}

static PyObject *namespacemap_iter(NamespaceMapObject *self)
{
  return iter_new(self, &KeyIter_Type);
}

static char namespacemap_doc[] = "\
Objects implementing the `namespacemap` interface are used to \
represent collections of nodes that can be accessed by name.";

static PyTypeObject NamespaceMap_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "namespacemap",
  /* tp_basicsize      */ sizeof(NamespaceMapObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) namespacemap_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) namespacemap_repr,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) &namespacemap_as_sequence,
  /* tp_as_mapping     */ (PyMappingMethods *) &namespacemap_as_mapping,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) 0,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
  /* tp_doc            */ (char *) namespacemap_doc,
  /* tp_traverse       */ (traverseproc) namespacemap_traverse,
  /* tp_clear          */ (inquiry) namespacemap_clear,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) namespacemap_iter,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) namespacemap_methods,
  /* tp_members        */ (PyMemberDef *) namespacemap_members,
  /* tp_getset         */ (PyGetSetDef *) namespacemap_getset,
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

/** Iterator Types *********************************************/

typedef struct {
  PyObject_HEAD
  NamespaceMapObject *it_map;
  Py_ssize_t it_used;
  Py_ssize_t it_pos;
  Py_ssize_t it_length;
} IterObject;

static PyObject *iter_new(NamespaceMapObject *nodemap, PyTypeObject *itertype)
{
  IterObject *self = PyObject_New(IterObject, itertype);
  if (self != NULL) {
    Py_INCREF(nodemap);
    self->it_map = nodemap;
    self->it_used = self->it_length = nodemap->nm_used;
    self->it_pos = 0;
  }
  return (PyObject *)self;
}

static void iter_dealloc(PyObject *op)
{
  IterObject *self = (IterObject *)op;
  Py_CLEAR(self->it_map);
  PyObject_Del(self);
}

static PyObject *iter_self(PyObject *op)
{
  Py_INCREF(op);
  return op;
}

static PyObject *iter_nextkey(IterObject *self)
{
  NamespaceMapObject *nodemap = self->it_map;
  NamespaceObject *node;

  if (nodemap == NULL)
    return NULL;

  if (self->it_used != nodemap->nm_used) {
    PyErr_Format(PyExc_RuntimeError, "%s changed size during iteration",
                 nodemap->ob_type->tp_name);
    self->it_used = -1;
    return NULL;
  }

  while ((node = next_entry(nodemap, &self->it_pos))) {
    self->it_length--;
    Py_INCREF(Namespace_GET_NAME(node));
    return Namespace_GET_NAME(node);
  }
  /* iterated over all items, indicate exhausted */
  Py_DECREF(nodemap);
  self->it_map = NULL;
  return NULL;
}

static PyObject *iter_nextvalue(IterObject *self)
{
  NamespaceMapObject *nodemap = self->it_map;
  NamespaceObject *node;

  if (nodemap == NULL)
    return NULL;

  if (self->it_used != nodemap->nm_used) {
    PyErr_Format(PyExc_RuntimeError, "%s changed size during iteration",
                 nodemap->ob_type->tp_name);
    self->it_used = -1;
    return NULL;
  }

  while ((node = next_entry(nodemap, &self->it_pos))) {
    self->it_length--;
    Py_INCREF(Namespace_GET_VALUE(node));
    return Namespace_GET_VALUE(node);
  }
  /* iterated over all items, indicate exhausted */
  Py_DECREF(nodemap);
  self->it_map = NULL;
  return NULL;
}

static PyObject *iter_nextitem(IterObject *self)
{
  NamespaceMapObject *nodemap = self->it_map;
  NamespaceObject *node;

  if (nodemap == NULL)
    return NULL;

  if (self->it_used != nodemap->nm_used) {
    PyErr_Format(PyExc_RuntimeError, "%s changed size during iteration",
                 nodemap->ob_type->tp_name);
    self->it_used = -1;
    return NULL;
  }

  while ((node = next_entry(nodemap, &self->it_pos))) {
    PyObject *item = PyTuple_Pack(2, Namespace_GET_NAME(node),
                                  Namespace_GET_VALUE(node));
    if (item == NULL)
      return NULL;
    self->it_length--;
    return item;
  }
  /* iterated over all items, indicate exhausted */
  Py_DECREF(nodemap);
  self->it_map = NULL;
  return NULL;
}

static PyObject *iter_nextnode(IterObject *self)
{
  NamespaceMapObject *nodemap = self->it_map;
  NamespaceObject *node;

  if (nodemap == NULL)
    return NULL;

  if (self->it_used != nodemap->nm_used) {
    PyErr_Format(PyExc_RuntimeError, "%s changed size during iteration",
                 nodemap->ob_type->tp_name);
    self->it_used = -1;
    return NULL;
  }

  while ((node = next_entry(nodemap, &self->it_pos))) {
    Py_INCREF(node);
    self->it_length--;
    return (PyObject *)node;
  }
  /* iterated over all items, indicate exhausted */
  Py_DECREF(nodemap);
  self->it_map = NULL;
  return NULL;
}

static PyObject *iter_length_hint(PyObject *op, PyObject *noarg)
{
  IterObject *it = (IterObject *)op;
  NamespaceMapObject *nodemap = it->it_map;
  if (nodemap != NULL && it->it_used == nodemap->nm_used)
    return PyInt_FromSize_t(it->it_length);
  else
    return PyInt_FromLong(0);
}

static PyMethodDef iter_methods[] = {
  { "__length_hint__", iter_length_hint, METH_NOARGS },
  { NULL }
};

static PyTypeObject Iter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "namespacemap-iterator",
  /* tp_basicsize      */ sizeof(IterObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) iter_dealloc,
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
  /* tp_iter           */ (getiterfunc) iter_self,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) iter_methods,
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

static PyTypeObject KeyIter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "namespacemap-keyiterator",
  /* tp_basicsize      */ 0,
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
  /* tp_iternext       */ (iternextfunc) iter_nextkey,
  /* tp_methods        */ (PyMethodDef *) 0,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) &Iter_Type,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) 0,
  /* tp_free           */ 0,
};

static PyTypeObject ValueIter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "namespacemap-valueiterator",
  /* tp_basicsize      */ 0,
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
  /* tp_iternext       */ (iternextfunc) iter_nextvalue,
  /* tp_methods        */ (PyMethodDef *) 0,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) &Iter_Type,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) 0,
  /* tp_free           */ 0,
};

static PyTypeObject ItemIter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "namespacemap-itemiterator",
  /* tp_basicsize      */ 0,
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
  /* tp_iternext       */ (iternextfunc) iter_nextitem,
  /* tp_methods        */ (PyMethodDef *) 0,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) &Iter_Type,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) 0,
  /* tp_free           */ 0,
};

static PyTypeObject NodeIter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "namespacemap-nodeiterator",
  /* tp_basicsize      */ 0,
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
  /* tp_iternext       */ (iternextfunc) iter_nextnode,
  /* tp_methods        */ (PyMethodDef *) 0,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) &Iter_Type,
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

int DomletteNamespaceMap_Init(PyObject *module)
{
  if (PyType_Ready(&Iter_Type) < 0)
    return -1;
  if (PyType_Ready(&KeyIter_Type) < 0)
    return -1;
  if (PyType_Ready(&ValueIter_Type) < 0)
    return -1;
  if (PyType_Ready(&ItemIter_Type) < 0)
    return -1;
  if (PyType_Ready(&NodeIter_Type) < 0)
    return -1;
  if (PyType_Ready(&NamespaceMap_Type) < 0)
    return -1;

  return 0;
}

void DomletteNamespaceMap_Fini(void)
{
  PyType_CLEAR(&NamespaceMap_Type);
}
