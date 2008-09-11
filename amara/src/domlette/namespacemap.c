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
    memcmp(PyUnicode_AS_UNICODE(a), PyUnicode_AS_UNICODE(b), \
           PyUnicode_GET_DATA_SIZE(a))))

#define KEY_EQ(entry, hash, name) \
  (Namespace_GET_NAME(NamespaceEntry_NODE(entry)) == (name) || \
   (NamespaceEntry_HASH(entry) == (hash) && \
    NAME_EQ(Namespace_GET_NAME(NamespaceEntry_NODE(entry)), (name))))

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

Py_LOCAL_INLINE(NamespaceEntry *)
get_entry(NamespaceMapObject *nm, Py_ssize_t hash, PyObject *name)
{
  register size_t perturb = hash;
  register size_t mask = (size_t)nm->nm_mask;
  register size_t i = perturb & mask;
  register NamespaceEntry *entry;
  NamespaceEntry *table = nm->nm_table;

  entry = &table[i];
  if (entry->ne_node == NULL || KEY_EQ(entry, hash, name))
    return entry;

  do {
    i = (i << 2) + i + perturb + 1;
    entry = &table[i & mask];
    if (entry->ne_node == NULL || KEY_EQ(entry, hash, name))
      return entry;
    perturb >>= 5;
  } while(1);

  assert(0);      /* NOT REACHED */
  return NULL;
}

Py_LOCAL_INLINE(void)
set_entry(NamespaceMapObject *nm, Py_ssize_t hash, NamespaceObject *node)
{
  register size_t perturb = hash;
  register size_t mask = (size_t)nm->nm_mask;
  register size_t i = perturb & mask;
  register NamespaceEntry *entry;
  NamespaceEntry *table = nm->nm_table;

  entry = &table[i];
  while (entry->ne_node != NULL) {
    i = (i << 2) + i + perturb + 1;
    perturb >>= 5;
    entry = &table[i & mask];
  }
  entry->ne_hash = hash;
  entry->ne_node = node;
}

/*
Restructure the table by allocating a new table and reinserting all
items again.  When entries have been deleted, the new table may
actually be smaller than the old one.
*/
Py_LOCAL(int)
resize_table(NamespaceMapObject *self)
{
  NamespaceEntry *oldtable, *newtable, *entry;
  Py_ssize_t newsize, i;

  /* Get space for a new table. */
  oldtable = self->nm_table;
  newsize = (self->nm_mask + 1) << 1;
  if (newsize <= NamespaceMap_MINSIZE) {
    newsize = NamespaceMap_MINSIZE;
    newtable = self->nm_smalltable;
    if (oldtable == newtable)
      return 0;
  } else {
    newtable = PyMem_New(NamespaceEntry, newsize);
    if (newtable == NULL) {
      PyErr_NoMemory();
      return -1;
    }
  }

  /* Make the dict empty, using the new table. */
  self->nm_table = newtable;
  self->nm_mask = newsize - 1;
  memset(newtable, 0, sizeof(NamespaceEntry) * newsize);

  /* Copy the data over */
  for (entry = oldtable, i = self->nm_used; i > 0; entry++) {
    if (entry->ne_node != NULL) {
      i--;
      set_entry(self, entry->ne_hash, entry->ne_node);
    }
  }

  if (oldtable != self->nm_smalltable)
    PyMem_Free(oldtable);
  return 0;
}

Py_LOCAL_INLINE(NamespaceObject *)
next_entry(NamespaceMapObject *self, Py_ssize_t *ppos)
{
  register Py_ssize_t i = *ppos;
  register Py_ssize_t mask = self->nm_mask;
  register NamespaceEntry *table = self->nm_table;

  if (i < 0)
    return NULL;
  while (i <= mask && table[i].ne_node == NULL) i++;
  *ppos = i+1;
  if (i > mask)
    return NULL;
  return table[i].ne_node;
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
    } else if (PyObject_CheckReadBuffer(key)) {
      if (PyObject_AsCharBuffer(key, &str, &len) < 0)
        return NULL;
    } else {
      return PyErr_Format(PyExc_KeyError,
                          "subscript must be %sunicode string, "
                          "UTF-8 byte-string or None, not '%s'",
                          node_allowed ? "Namespace instance, " : "",
                          key->ob_type->tp_name);
    }
    name = PyUnicode_Decode(str, len, "utf-8", NULL);
  }
  return name;
}

/** Public C API ******************************************************/

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

NamespaceObject *
NamespaceMap_GetNode(PyObject *self, PyObject *name)
{
  NamespaceMapObject *nm = (NamespaceMapObject *)self;
  if (!NamespaceMap_Check(nm)) {
    PyErr_BadInternalCall();
    return NULL;
  }
  PyErr_SetString(PyExc_NotImplementedError, "NamespaceMap_GetNode");
  return NULL;
}

int
NamespaceMap_SetNode(PyObject *self, NamespaceObject *node)
{
  NamespaceMapObject *nm = (NamespaceMapObject *)self;
  NamespaceEntry *entry;
  PyObject *name;
  long hash;

  if (!NamespaceMap_Check(nm)) {
    PyErr_BadInternalCall();
    return -1;
  }
  name = Namespace_GET_NAME(node);
  hash = get_hash(name);
  if (hash == -1)
    return -1;
  entry = get_entry(nm, hash, name);
  assert(entry != NULL);
  if (entry->ne_node == NULL) {
    entry->ne_hash = hash;
    nm->nm_used++;
    /* If fill >= 2/3 size, adjust size.  Normally, this doubles or
     * quaduples the size, but it's also possible for the dict to shrink
     * (if ma_fill is much larger than ma_used, meaning a lot of dict
     * keys have been * deleted).
     */
    if (nm->nm_used*3 >= (nm->nm_mask+1)*2) {
      if (resize_table(nm) < 0)
        return -1;
    }
  } else {
    Py_DECREF(entry->ne_node);
  }
  entry->ne_node = node;
  Py_INCREF(node);
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

static char namednodemap_getnode_doc[] = "\
getnode(namespace, localname) -> Node or None\n\
\n\
Retrieves a node specified by local name and namespace URI or None \
if they do not identify a node in this map.";

static PyObject *namednodemap_getnode(PyObject *self, PyObject *args)
{
  PyObject *name;

  if (!PyArg_ParseTuple(args, "O:getnode", &name))
    return NULL;

  return (PyObject *)NamespaceMap_GetNode(self, name);
}

static char namednodemap_setnode_doc[] = "\
setnode(node) -> M[node.xml_name] = node.xml_value";

static PyObject *namednodemap_setnode(PyObject *self, PyObject *args)
{
  NamespaceObject *node;

  if (!PyArg_ParseTuple(args, "O!:setnode", &DomletteNamespace_Type, &node))
    return NULL;

  if (NamespaceMap_SetNode(self, node) < 0)
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char namednodemap_get_doc[] =
"M.get(k[,d]) -> M[k] if k in M, else d.  d defaults to None.";

static PyObject *namednodemap_get(PyObject *self, PyObject *args)
{
  PyObject *key, *result=Py_None;
  PyObject *name;
  NamespaceObject *node;

  if (!PyArg_ParseTuple(args, "O|O:get", &key, &result))
    return NULL;
  name = parse_key(key, 0);
  if (name == NULL) {
    if (PyErr_ExceptionMatches(PyExc_KeyError)) {
      PyErr_Clear();
      goto notfound;
    }
    return NULL;
  }
  node = NamespaceMap_GetNode(self, name);
  Py_DECREF(name);
  if (node)
    result = Namespace_GET_VALUE(node);

notfound:
  Py_INCREF(result);
  return result;
}

static char namednodemap_keys_doc[] =
"M.keys() -> list of prefixes";

static PyObject *namednodemap_keys(NamespaceMapObject *self)
{
  register PyObject *keys;
  register Py_ssize_t i, n;
  register NamespaceEntry *table;

  n = self->nm_used;
  keys = PyList_New(n);
  if (keys == NULL)
    return NULL;
  for (i = 0, table = self->nm_table; i < n; table++) {
    if (table->ne_node != NULL) {
      PyObject *key = Namespace_GET_NAME(table->ne_node);
      PyList_SET_ITEM(keys, i, key);
      Py_INCREF(key);
      i++;
    }
  }
  return keys;
}

static char namednodemap_values_doc[] =
"M.values() -> list of node values";

static PyObject *namednodemap_values(NamespaceMapObject *self)
{
  register PyObject *values;
  register Py_ssize_t i, n;
  register NamespaceEntry *table;

  n = self->nm_used;
  values = PyList_New(n);
  if (values == NULL)
    return NULL;
  for (i = 0, table = self->nm_table; i < n; table++) {
    if (table->ne_node != NULL) {
      PyObject *value = Namespace_GET_VALUE(table->ne_node);
      Py_INCREF(value);
      PyList_SET_ITEM(values, i, value);
      i++;
    }
  }
  return values;
}

static char namednodemap_items_doc[] =
"M.items() -> list of M's (prefix, uri) pairs, as 2-tuples";

static PyObject *namednodemap_items(NamespaceMapObject *self)
{
  register PyObject *items;
  register Py_ssize_t i, n;
  register NamespaceEntry *table;

  n = self->nm_used;
  items = PyList_New(n);
  if (items == NULL)
    return NULL;
  for (i = 0, table = self->nm_table; i < n; table++) {
    if (table->ne_node != NULL) {
      PyObject *item = PyTuple_Pack(2, Namespace_GET_NAME(table->ne_node),
                                    Namespace_GET_VALUE(table->ne_node));
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

static char namednodemap_copy_doc[] =
"M.copy() -> a copy of M as a dictionary";

static PyObject *namednodemap_copy(NamespaceMapObject *self)
{
  register PyObject *copy;
  register Py_ssize_t i, n;
  register NamespaceEntry *table;
  PyObject *key, *value;

  copy = PyDict_New();
  if (copy == NULL)
    return NULL;

  for (i = 0, n = self->nm_used, table = self->nm_table; i < n; table++) {
    if (table->ne_node != NULL) {
      key = Namespace_GET_NAME(table->ne_node);
      value = Namespace_GET_VALUE(table->ne_node);
      if (PyDict_SetItem(copy, key, value) < 0)
        return NULL;
      i++;
    }
  }
  return copy;
}

static char namednodemap_iterkeys_doc[] =
"M.iterkeys() -> an iterator over the expanded name 2-tuples of M";

static PyObject *namednodemap_iterkeys(NamespaceMapObject *self)
{
  return iter_new(self, &KeyIter_Type);
}

static char namednodemap_itervalues_doc[] =
"M.itervalues() -> an iterator over the node values of M";

static PyObject *namednodemap_itervalues(NamespaceMapObject *self)
{
  return iter_new(self, &ValueIter_Type);
}

static char namednodemap_iteritems_doc[] =
"M.iteritems() -> an iterator over the (expanded name, value) items of M";

static PyObject *namednodemap_iteritems(NamespaceMapObject *self)
{
  return iter_new(self, &ItemIter_Type);
}

static char namednodemap_nodes_doc[] =
"M.nodes() -> an iterator over the attribute nodes of M";

static PyObject *namednodemap_nodes(NamespaceMapObject *self)
{
  return iter_new(self, &NodeIter_Type);
}

#define NamespaceMap_METHOD(NAME, FLAGS)             \
  { #NAME, (PyCFunction) namednodemap_##NAME, FLAGS, \
      namednodemap_##NAME##_doc }

static PyMethodDef namednodemap_methods[] = {
  NamespaceMap_METHOD(getnode, METH_VARARGS),
  NamespaceMap_METHOD(setnode, METH_VARARGS),
  /* Python Mapping Interface */
  NamespaceMap_METHOD(get, METH_VARARGS),
  NamespaceMap_METHOD(keys, METH_NOARGS),
  NamespaceMap_METHOD(values, METH_NOARGS),
  NamespaceMap_METHOD(items, METH_NOARGS),
  NamespaceMap_METHOD(copy, METH_NOARGS),
  NamespaceMap_METHOD(iterkeys, METH_NOARGS),
  NamespaceMap_METHOD(itervalues, METH_NOARGS),
  NamespaceMap_METHOD(iteritems, METH_NOARGS),
  NamespaceMap_METHOD(nodes, METH_NOARGS),
  { NULL }
};

static Py_ssize_t
namednodemap_length(NamespaceMapObject *self)
{
  return self->nm_used;
}

static PyObject *
namednodemap_subscript(PyObject *op, PyObject *key)
{
  PyObject *name;
  NamespaceObject *node;

  name = parse_key(key, 0);
  if (name == NULL)
    return NULL;
  node = NamespaceMap_GetNode(op, name);
  Py_DECREF(name);
  if (node == NULL) {
    PyErr_SetObject(PyExc_KeyError, key);
    return NULL;
  }
  Py_INCREF(node);
  return (PyObject *)node;
}

static int
namednodemap_ass_subscript(PyObject *self, PyObject *key, PyObject *value)
{
  PyObject *name;
  int result;

  if (value == NULL) {
    /* __delitem__(key)
     * `key` can be Attr node or tuple of (namespace, name) or just name
     */
    name = parse_key(key, 1);
    if (name == NULL)
      return -1;
    result = NamespaceMap_DelNode(self, name);
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
    node = NamespaceMap_GetNode(self, name);
    if (node == NULL) {
      /* create new attribute node */

      result = NamespaceMap_SetNode(self, node);
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

static PyMappingMethods namednodemap_as_mapping = {
  /* mp_length        */ (lenfunc) namednodemap_length,
  /* mp_subscript     */ (binaryfunc) namednodemap_subscript,
  /* mp_ass_subscript */ (objobjargproc) namednodemap_ass_subscript,
};

static int namednodemap_contains(NamespaceMapObject *self, PyObject *key)
{
  if (Namespace_Check(key)) {
    Py_ssize_t pos = 0;
    NamespaceObject *node;
    while ((node = next_entry(self, &pos))) {
      switch (PyObject_RichCompareBool(key, (PyObject *)node, Py_EQ)) {
        case 1:
          return 1;
        case 0:
          break;
        default:
          return -1;
      }
    }
  } else {
    NamespaceEntry *entry;
    PyObject *name;
    long hash = get_hash(key);
    if (hash == -1)
      return -1;
    if (key == Py_None || PyUnicode_Check(key)) {
      entry = get_entry(self, hash, key);
    } else {
      name = PyUnicode_FromEncodedObject(key, "utf-8", NULL);
      if (name == NULL)
        return -1;
      entry = get_entry(self, hash, name);
      Py_DECREF(name);
    }
    if (entry == NULL)
      return -1;
    if (entry->ne_node)
      return 1;
  }
  return 0;
}

static PySequenceMethods namednodemap_as_sequence = {
  /* sq_length         */ 0,
  /* sq_concat         */ 0,
  /* sq_repeat         */ 0,
  /* sq_item           */ 0,
  /* sq_slice          */ 0,
  /* sq_ass_item       */ 0,
  /* sq_ass_slice      */ 0,
  /* sq_contains       */ (objobjproc) namednodemap_contains,
  /* sq_inplace_concat */ 0,
  /* sq_inplace_repeat */ 0,
};

/** Python Members ****************************************************/

static PyMemberDef namednodemap_members[] = {
  { NULL }
};

/** Python Computed Members *******************************************/

static PyGetSetDef namednodemap_getset[] = {
  { NULL }
};

/** Type Object ********************************************************/

static void namednodemap_dealloc(NamespaceMapObject *self)
{
  register NamespaceEntry *entry;
  register Py_ssize_t used;

  PyObject_GC_UnTrack(self);
  Py_XDECREF(self->nm_owner);
  Py_TRASHCAN_SAFE_BEGIN(self);
  for (entry = self->nm_table, used = self->nm_used; used > 0; entry++) {
    if (entry->ne_node != NULL) {
      used--;
      Py_DECREF(entry->ne_node);
    }
  }
  Py_TRASHCAN_SAFE_END(self);
  if (self->nm_table != self->nm_smalltable)
    PyMem_Free(self->nm_table);
  ((PyObject *)self)->ob_type->tp_free((PyObject *)self);
}

static PyObject *namednodemap_repr(NamespaceMapObject *self)
{
  return PyString_FromFormat("<NamespaceMap at %p: %zd nodes>",
                             self, self->nm_used);
}

static int namednodemap_traverse(NamespaceMapObject *self, visitproc visit,
                                 void *arg)
{
  Py_ssize_t i = 0;
  NamespaceObject *node;

  Py_VISIT(self->nm_owner);
  while ((node = next_entry(self, &i)))
    Py_VISIT(node);

  return 0;
}

static int namednodemap_clear(NamespaceMapObject *self)
{
  register Py_ssize_t used = self->nm_used;
  register NamespaceEntry *entry;
  NamespaceEntry *table;
  NamespaceEntry smallcopy[NamespaceMap_MINSIZE];
  int malloced_table;

  Py_CLEAR(self->nm_owner);
  table = self->nm_table;
  malloced_table = (table != self->nm_smalltable);

  /* If it is a small table with something that needs to be cleared, the
   * only safe way is to copy the entries into another small table first.
   */
  if (!malloced_table && used) {
    memcpy(smallcopy, table, sizeof(smallcopy));
    table = smallcopy;
  }

  /* Because DECREF's can cause the map to mutate, we make it empty first */
  INIT_MINSIZE(self);

  /* Now finally clear things */
  for (entry = table; used > 0; entry++) {
    if (entry->ne_node != NULL) {
      used--;
      Py_DECREF(entry->ne_node);
    }
  }

  if (malloced_table)
    PyMem_Free(table);

  return 0;
}

static PyObject *namednodemap_iter(NamespaceMapObject *self)
{
  return iter_new(self, &KeyIter_Type);
}

static char namednodemap_doc[] = "\
Objects implementing the NamespaceMap interface are used to \
represent collections of nodes that can be accessed by name. \
Note that NamespaceMaps are not maintained in any particular order. \
Objects contained in an object implementing NamespaceMap may \
also be accessed by an ordinal index, but this is simply to allow \
convenient enumeration of the contents of a NamespaceMap, \
and does not imply that the DOM specifies an order to these Nodes.";

static PyTypeObject NamespaceMap_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "NamespaceMap",
  /* tp_basicsize      */ sizeof(NamespaceMapObject),
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
  /* tp_str            */ (reprfunc) 0,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
  /* tp_doc            */ (char *) namednodemap_doc,
  /* tp_traverse       */ (traverseproc) namednodemap_traverse,
  /* tp_clear          */ (inquiry) namednodemap_clear,
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

  node = next_entry(nodemap, &self->it_pos);
  if (node == NULL) {
    /* iterated over all items, indicate exhausted */
    Py_DECREF(nodemap);
    self->it_map = NULL;
    return NULL;
  }

  self->it_length--;
  Py_INCREF(Namespace_GET_NAME(node));
  return Namespace_GET_NAME(node);
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

  node = next_entry(nodemap, &self->it_pos);
  if (node == NULL) {
    /* iterated over all items, indicate exhausted */
    Py_DECREF(nodemap);
    self->it_map = NULL;
    return NULL;
  }

  self->it_length--;
  Py_INCREF(Namespace_GET_VALUE(node));
  return Namespace_GET_VALUE(node);
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

  node = next_entry(nodemap, &self->it_pos);
  if (node == NULL) {
    /* iterated over all items, indicate exhausted */
    Py_DECREF(nodemap);
    self->it_map = NULL;
    return NULL;
  }

  self->it_length--;
  return PyTuple_Pack(2, Namespace_GET_NAME(node), Namespace_GET_VALUE(node));
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

  node = next_entry(nodemap, &self->it_pos);
  if (node == NULL) {
    /* iterated over all items, indicate exhausted */
    Py_DECREF(nodemap);
    self->it_map = NULL;
    return NULL;
  }

  self->it_length--;
  Py_INCREF(node);
  return (PyObject *)node;
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

  Py_INCREF(&NamespaceMap_Type);
  return PyModule_AddObject(module, "NamespaceMap",
                            (PyObject*) &NamespaceMap_Type);
}

void DomletteNamespaceMap_Fini(void)
{
  PyType_CLEAR(&NamespaceMap_Type);
}
