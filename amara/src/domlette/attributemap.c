#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

static PyTypeObject AttributeMap_Type;
static PyTypeObject KeyIter_Type;
static PyTypeObject ValueIter_Type;
static PyTypeObject ItemIter_Type;
static PyTypeObject NodeIter_Type;

#define AttributeMap_Check(op) PyObject_TypeCheck(op, &AttributeMap_Type)
#define AttributeMap_CheckExact(op) ((op)->ob_type == &AttributeMap_Type)

#define INIT_MINSIZE(op) do {                                       \
  (op)->nm_used = 0;                                                \
  (op)->nm_mask = AttributeMap_MINSIZE - 1;                         \
  (op)->nm_table = (op)->nm_smalltable;                             \
  memset((op)->nm_smalltable, 0, sizeof(op->nm_smalltable));        \
} while(0)

#define NAME_EQ(a, b) \
  (PyUnicode_GET_SIZE(a) == PyUnicode_GET_SIZE(b) && \
   *PyUnicode_AS_UNICODE(a) == *PyUnicode_AS_UNICODE(b) && \
   memcmp(PyUnicode_AS_UNICODE(a), PyUnicode_AS_UNICODE(b), \
          PyUnicode_GET_DATA_SIZE(a)))

#define NAMESPACE_EQ(a, b) \
  (((a) == Py_None || (b) == Py_None) ? (a) == (b) : NAME_EQ((a), (b)))

#define KEY_EQ(entry, hash, name, namespace) \
  ((Attr_GET_LOCAL_NAME(AttributeEntry_NODE(entry)) == (name) && \
    Attr_GET_NAMESPACE_URI(AttributeEntry_NODE(entry)) == (namespace)) || \
   (AttributeEntry_HASH(entry) == (hash) && \
    NAME_EQ(Attr_GET_LOCAL_NAME(AttributeEntry_NODE(entry)), (name)) && \
    NAMESPACE_EQ(Attr_GET_NAMESPACE_URI(AttributeEntry_NODE(entry)), (namespace))))

Py_LOCAL_INLINE(long)
get_hash(PyObject *namespace, PyObject *name)
{
  register long hash = 0x345678L;
  register long x;

  if (namespace == Py_None)
    x = 0;
  else if (!PyUnicode_CheckExact(namespace) ||
           (x = ((PyUnicodeObject *)namespace)->hash) == -1) {
    x = PyObject_Hash(namespace);
    if (x == -1) return -1;
  }
  hash = (hash ^ x) * 1000003L;
  if (!PyUnicode_CheckExact(name) ||
      (x = ((PyUnicodeObject *)name)->hash) == -1) {
    x = PyObject_Hash(name);
    if (x == -1) return -1;
  }
  hash = (hash ^ x) * 1082523L;
  hash += 97531L;
  if (hash == -1)
    hash = -2;
  return hash;
}

Py_LOCAL_INLINE(AttributeEntry *)
get_entry(AttributeMapObject *nm, Py_ssize_t hash, PyObject *name,
          PyObject *namespace)
{
  register size_t perturb = hash;
  register size_t mask = (size_t)nm->nm_mask;
  register size_t i = perturb & mask;
  register AttributeEntry *entry;
  AttributeEntry *table = nm->nm_table;

  entry = &table[i];
  if (entry->ne_node == NULL || KEY_EQ(entry, hash, name, namespace))
    return entry;

  do {
    i = (i << 2) + i + perturb + 1;
    entry = &table[i & mask];
    if (entry->ne_node == NULL || KEY_EQ(entry, hash, name, namespace))
      return entry;
    perturb >>= 5;
  } while(1);

  assert(0);      /* NOT REACHED */
  return NULL;
}

Py_LOCAL_INLINE(void)
set_entry(AttributeMapObject *nm, Py_ssize_t hash, AttrObject *node)
{
  register size_t perturb = hash;
  register size_t mask = (size_t)nm->nm_mask;
  register size_t i = perturb & mask;
  register AttributeEntry *entry;
  AttributeEntry *table = nm->nm_table;

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
resize_table(AttributeMapObject *self)
{
  AttributeEntry *oldtable, *newtable, *entry;
  Py_ssize_t newsize, i;

  /* Get space for a new table. */
  oldtable = self->nm_table;
  newsize = (self->nm_mask + 1) << 1;
  if (newsize <= AttributeMap_MINSIZE) {
    newsize = AttributeMap_MINSIZE;
    newtable = self->nm_smalltable;
    if (oldtable == newtable)
      return 0;
  } else {
    newtable = PyMem_New(AttributeEntry, newsize);
    if (newtable == NULL) {
      PyErr_NoMemory();
      return -1;
    }
  }

  /* Make the dict empty, using the new table. */
  self->nm_table = newtable;
  self->nm_mask = newsize - 1;
  memset(newtable, 0, sizeof(AttributeEntry) * newsize);

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

Py_LOCAL_INLINE(int)
parse_key(PyObject *key, PyObject **pnamespace, PyObject **pname,
          int node_allowed)
{
  PyObject *namespace, *name;

  if (PyTuple_Check(key) && PyTuple_GET_SIZE(key) == 2) {
    namespace = XmlString_ConvertArgument(PyTuple_GET_ITEM(key, 0),
                                          "expanded name, item 0", 1);
    if (namespace == NULL)
      return -1;
    name = XmlString_ConvertArgument(PyTuple_GET_ITEM(key, 1),
                                     "expanded name, item 1", 0);
    if (name == NULL) {
      Py_DECREF(namespace);
      return -1;
    }
  } else if (PyUnicode_Check(key)) {
    namespace = Py_None;
    Py_INCREF(namespace);
    name = key;
    Py_INCREF(name);
  } else if (node_allowed && Attr_Check(key)) {
    namespace = Attr_GET_NAMESPACE_URI(key);
    Py_INCREF(namespace);
    name = Attr_GET_LOCAL_NAME(key);
    Py_INCREF(name);
  } else {
    const char *str;
    Py_ssize_t len;
    if (PyString_Check(key)) {
      if (PyString_AsStringAndSize(key, (char **)&str, &len) < 0)
        return -1;
    } else if (PyObject_AsCharBuffer(key, &str, &len) < 0) {
      if (PyErr_ExceptionMatches(PyExc_TypeError)) {
        PyErr_Format(PyExc_KeyError,
                     "subscript must be expanded name 2-tuple, unicode string"
                         "%s or UTF-8 byte-string, not '%s'",
                         node_allowed ? ", Attr instance" : "",
                         key->ob_type->tp_name);
      }
      return -1;
    }
    name = PyUnicode_Decode(str, len, "utf-8", NULL);
    if (name == NULL)
      return -1;
    namespace = Py_None;
    Py_INCREF(namespace);
  }
  *pnamespace = namespace;
  *pname = name;
  return 0;
}

/** Public C API ******************************************************/

PyObject *
AttributeMap_New(void)
{
  register AttributeMapObject *self;

  self = PyObject_GC_New(AttributeMapObject, &AttributeMap_Type);
  if (self != NULL) {
    INIT_MINSIZE(self);
    PyObject_GC_Track(self);
  }
  return (PyObject *)self;
}

AttrObject *
AttributeMap_GetNode(PyObject *self, PyObject *namespace, PyObject *name)
{
  AttributeMapObject *nm = (AttributeMapObject *)self;
  AttributeEntry *entry;
  long hash;

  if (!AttributeMap_Check(nm)) {
    PyErr_BadInternalCall();
    return NULL;
  }
  if (namespace == Py_None || PyUnicode_Check(namespace)) {
    Py_INCREF(namespace);
  } else {
    namespace = XmlString_FromObject(namespace);
    if (namespace == NULL)
      return NULL;
  }
  if (PyUnicode_Check(name)) {
    Py_INCREF(name);
  } else {
    name = XmlString_FromObject(name);
    if (name == NULL)
      return NULL;
  }
  hash = get_hash(namespace, name);
  if (hash == -1) {
    Py_DECREF(namespace);
    Py_DECREF(name);
    return NULL;
  }
  entry = get_entry(nm, hash, name, namespace);
  Py_DECREF(namespace);
  Py_DECREF(name);

  return AttributeEntry_NODE(entry);
}

int
AttributeMap_SetNode(PyObject *self, AttrObject *node)
{
  AttributeMapObject *nm = (AttributeMapObject *)self;
  AttributeEntry *entry;
  PyObject *namespace, *name;
  long hash;

  if (!AttributeMap_Check(nm)) {
    PyErr_BadInternalCall();
    return -1;
  }
  namespace = Attr_GET_NAMESPACE_URI(node);
  name = Attr_GET_LOCAL_NAME(node);
  hash = get_hash(namespace, name);
  if (hash == -1)
    return -1;
  entry = get_entry(nm, hash, name, namespace);
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
AttributeMap_DelNode(PyObject *self, PyObject *namespace, PyObject *name)
{
  PyErr_SetString(PyExc_NotImplementedError, "AttributeMap_DelNode");
  return -1;
}

AttrObject *
AttributeMap_Next(PyObject *self, Py_ssize_t *ppos)
{
  AttributeMapObject *nm = (AttributeMapObject *)self;
  register Py_ssize_t i = *ppos;
  register Py_ssize_t mask = nm->nm_mask;
  register AttributeEntry *table = nm->nm_table;

  if (i < 0)
    return NULL;
  while (i <= mask && table[i].ne_node == NULL) i++;
  *ppos = i+1;
  if (i > mask)
    return NULL;
  return (AttrObject *)table[i].ne_node;
}

/** Python Methods ****************************************************/

static PyObject *iter_new(AttributeMapObject *self, PyTypeObject *type);

static char namednodemap_getnode_doc[] = "\
getnode(namespace, localname) -> Node or None\n\
\n\
Retrieves a node specified by local name and namespace URI or None \
if they do not identify a node in this map.";

static PyObject *namednodemap_getnode(PyObject *self, PyObject *args)
{
  PyObject *namespace, *name;
  AttrObject *attr;

  if (!PyArg_ParseTuple(args, "OO:getnode", &namespace, &name))
    return NULL;

  attr = AttributeMap_GetNode(self, namespace, name);
  if (attr != NULL)
    return (PyObject *)attr;
  Py_INCREF(Py_None);
  return Py_None;
}

static char namednodemap_setnode_doc[] = "\
setnode(node) -> M[node.xml_namespace, node.xml_local] = node.xml_value";

static PyObject *namednodemap_setnode(PyObject *self, PyObject *args)
{
  AttrObject *attr;

  if (!PyArg_ParseTuple(args, "O!:setnode", &attr, &DomletteAttr_Type))
    return NULL;

  if (AttributeMap_SetNode(self, attr) < 0)
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char namednodemap_get_doc[] =
"M.get(k[,d]) -> M[k] if k in M, else d.  d defaults to None.";

static PyObject *namednodemap_get(PyObject *self, PyObject *args)
{
  PyObject *key, *def=Py_None;
  PyObject *namespace, *name;
  AttrObject *node;

  if (!PyArg_ParseTuple(args, "O|O:get", &key, &def))
    return NULL;
  if (parse_key(key, &namespace, &name, 0) < 0) {
    if (PyErr_ExceptionMatches(PyExc_KeyError)) {
      PyErr_Clear();
      goto notfound;
    }
    return NULL;
  }
  node = AttributeMap_GetNode(self, namespace, name);
  Py_DECREF(namespace);
  Py_DECREF(name);
  if (node) {
    Py_INCREF(Attr_GET_NODE_VALUE(node));
    return Attr_GET_NODE_VALUE(node);
  }
notfound:
  Py_INCREF(def);
  return def;
}

static char namednodemap_keys_doc[] =
"M.keys() -> list of expanded name 2-tuples";

static PyObject *namednodemap_keys(AttributeMapObject *self)
{
  register PyObject *keys;
  register Py_ssize_t i, n;
  register AttributeEntry *table;

  n = self->nm_used;
  keys = PyList_New(n);
  if (keys == NULL)
    return NULL;
  for (i = 0, table = self->nm_table; i < n; table++) {
    if (table->ne_node != NULL) {
      PyObject *key = PyTuple_Pack(2, Attr_GET_NAMESPACE_URI(table->ne_node),
                                   Attr_GET_LOCAL_NAME(table->ne_node));
      if (key == NULL) {
        Py_DECREF(keys);
        return NULL;
      }
      PyList_SET_ITEM(keys, i, key);
      i++;
    }
  }
  return keys;
}

static char namednodemap_values_doc[] =
"M.values() -> list of node values";

static PyObject *namednodemap_values(AttributeMapObject *self)
{
  register PyObject *values;
  register Py_ssize_t i, n;
  register AttributeEntry *table;

  n = self->nm_used;
  values = PyList_New(n);
  if (values == NULL)
    return NULL;
  for (i = 0, table = self->nm_table; i < n; table++) {
    if (table->ne_node != NULL) {
      PyObject *value = Attr_GET_NODE_VALUE(table->ne_node);
      Py_INCREF(value);
      PyList_SET_ITEM(values, i, value);
      i++;
    }
  }
  return values;
}

static char namednodemap_items_doc[] =
"M.items() -> list of M's (expanded name, value) pairs, as 2-tuples";

static PyObject *namednodemap_items(AttributeMapObject *self)
{
  register PyObject *items;
  register Py_ssize_t i, n;
  register AttributeEntry *table;
  PyObject *key, *value, *item;

  n = self->nm_used;
  items = PyList_New(n);
  if (items == NULL)
    return NULL;
  for (i = 0, table = self->nm_table; i < n; table++) {
    if (table->ne_node != NULL) {
      key = PyTuple_Pack(2, Attr_GET_NAMESPACE_URI(table->ne_node),
                         Attr_GET_LOCAL_NAME(table->ne_node));
      if (key == NULL) {
        Py_DECREF(items);
        return NULL;
      }
      value = Attr_GET_NODE_VALUE(table->ne_node);
      item = PyTuple_New(2);
      if (item == NULL) {
        Py_DECREF(key);
        Py_DECREF(items);
        return NULL;
      }
      PyTuple_SET_ITEM(item, 0, key);
      PyTuple_SET_ITEM(item, 1, value);
      Py_INCREF(value);
      PyList_SET_ITEM(items, i, item);
      i++;
    }
  }
  return items;
}

static char namednodemap_copy_doc[] =
"M.copy() -> a copy of M as a dictionary";

static PyObject *namednodemap_copy(AttributeMapObject *self)
{
  register PyObject *copy;
  register Py_ssize_t i, n;
  register AttributeEntry *table;
  PyObject *key, *value;

  copy = PyDict_New();
  if (copy == NULL)
    return NULL;

  for (i = 0, n = self->nm_used, table = self->nm_table; i < n; table++) {
    if (table->ne_node != NULL) {
      key = PyTuple_Pack(2, Attr_GET_NAMESPACE_URI(table->ne_node),
                         Attr_GET_LOCAL_NAME(table->ne_node));
      if (key == NULL) {
        Py_DECREF(copy);
        return NULL;
      }
      value = Attr_GET_NODE_VALUE(table->ne_node);
      if (PyDict_SetItem(copy, key, value) < 0) {
        Py_DECREF(key);
        Py_DECREF(copy);
        return NULL;
      }
      Py_DECREF(key);
      i++;
    }
  }
  return copy;
}

static char namednodemap_iterkeys_doc[] =
"M.iterkeys() -> an iterator over the expanded name 2-tuples of M";

static PyObject *namednodemap_iterkeys(AttributeMapObject *self)
{
  return iter_new(self, &KeyIter_Type);
}

static char namednodemap_itervalues_doc[] =
"M.itervalues() -> an iterator over the node values of M";

static PyObject *namednodemap_itervalues(AttributeMapObject *self)
{
  return iter_new(self, &ValueIter_Type);
}

static char namednodemap_iteritems_doc[] =
"M.iteritems() -> an iterator over the (expanded name, value) items of M";

static PyObject *namednodemap_iteritems(AttributeMapObject *self)
{
  return iter_new(self, &ItemIter_Type);
}

static char namednodemap_nodes_doc[] =
"M.nodes() -> an iterator over the attribute nodes of M";

static PyObject *namednodemap_nodes(AttributeMapObject *self)
{
  return iter_new(self, &NodeIter_Type);
}

#define AttributeMap_METHOD(NAME, FLAGS)             \
  { #NAME, (PyCFunction) namednodemap_##NAME, FLAGS, \
      namednodemap_##NAME##_doc }

static PyMethodDef namednodemap_methods[] = {
  AttributeMap_METHOD(getnode, METH_VARARGS),
  AttributeMap_METHOD(setnode, METH_VARARGS),
  /* Python Mapping Interface */
  AttributeMap_METHOD(get, METH_VARARGS),
  AttributeMap_METHOD(keys, METH_NOARGS),
  AttributeMap_METHOD(values, METH_NOARGS),
  AttributeMap_METHOD(items, METH_NOARGS),
  AttributeMap_METHOD(copy, METH_NOARGS),
  AttributeMap_METHOD(iterkeys, METH_NOARGS),
  AttributeMap_METHOD(itervalues, METH_NOARGS),
  AttributeMap_METHOD(iteritems, METH_NOARGS),
  AttributeMap_METHOD(nodes, METH_NOARGS),
  { NULL }
};

static Py_ssize_t
namednodemap_length(AttributeMapObject *self)
{
  return self->nm_used;
}

static PyObject *
namednodemap_subscript(PyObject *op, PyObject *key)
{
  PyObject *namespace, *name;
  AttrObject *node;

  if (parse_key(key, &namespace, &name, 0) < 0)
    return NULL;
  node = AttributeMap_GetNode(op, namespace, name);
  Py_DECREF(namespace);
  Py_DECREF(name);
  if (node == NULL) {
    PyErr_SetObject(PyExc_KeyError, key);
    return NULL;
  }
  Py_INCREF(node);
  return (PyObject *)node;
}

static int
namednodemap_ass_subscript(PyObject *op, PyObject *key, PyObject *value)
{
  PyObject *namespace, *name;
  int result;

  if (value == NULL) {
    /* __delitem__(key)
     * `key` can be Attr node or tuple of (namespace, name) or just name
     */
    if (parse_key(key, &namespace, &name, 1) < 0)
      return -1;
    result = AttributeMap_DelNode(op, namespace, name);
  } else {
    /* __setitem__(key, value)
     * `key` can be tuple of (namespace, name) or just name
     */
    AttrObject *attr;
    if (parse_key(key, &namespace, &name, 0) < 0)
      return -1;
    /* FIXME: validate value */
    value = XmlString_ConvertArgument(value, "", 0);
    if (value == NULL) {
      Py_DECREF(namespace);
      Py_DECREF(name);
      return -1;
    }
    attr = (AttrObject *)AttributeMap_GetNode(op, namespace, name);
    if (attr == NULL) {
      /* create new attribute node */
      result = AttributeMap_SetNode(op, attr);
    } else {
      /* just update the node value */
     Py_DECREF(Attr_GET_NODE_VALUE(attr));
     Attr_GET_NODE_VALUE(attr) = value;
     result = 0;
    }
  }
  Py_DECREF(namespace);
  Py_DECREF(name);
  return result;
}

static PyMappingMethods namednodemap_as_mapping = {
  /* mp_length        */ (lenfunc) namednodemap_length,
  /* mp_subscript     */ (binaryfunc) namednodemap_subscript,
  /* mp_ass_subscript */ (objobjargproc) namednodemap_ass_subscript,
};

static int namednodemap_contains(AttributeMapObject *self, PyObject *key)
{
  if (Attr_Check(key)) {
    Py_ssize_t pos = 0;
    AttrObject *node;
    while ((node = AttributeMap_Next((PyObject *)self, &pos))) {
      switch (PyObject_RichCompareBool(key, (PyObject *)node, Py_EQ)) {
        case 1:
          return 1;
        case 0:
          break;
        default:
          return -1;
      }
    }
  } else if (PyTuple_Check(key) && PyTuple_GET_SIZE(key) == 2) {
    AttributeEntry *entry;
    PyObject *namespace = PyTuple_GET_ITEM(key, 0);
    PyObject *name = PyTuple_GET_ITEM(key, 1);
    long hash = get_hash(namespace, name);
    if (hash == -1)
      return -1;
    entry = get_entry(self, hash, name, namespace);
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

static void namednodemap_dealloc(AttributeMapObject *self)
{
  register AttributeEntry *entry;
  register Py_ssize_t used;

  PyObject_GC_UnTrack(self);
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

static PyObject *namednodemap_repr(AttributeMapObject *self)
{
  return PyString_FromFormat("<AttributeMap at %p: "
                             "%" PY_FORMAT_SIZE_T "d nodes>",
                             self, self->nm_used);
}

static int namednodemap_traverse(AttributeMapObject *self, visitproc visit,
                                 void *arg)
{
  Py_ssize_t i = 0;
  AttrObject *node;

  while ((node = AttributeMap_Next((PyObject *)self, &i)))
    Py_VISIT(node);

  return 0;
}

static int namednodemap_clear(AttributeMapObject *self)
{
  register Py_ssize_t used = self->nm_used;
  register AttributeEntry *entry;
  AttributeEntry *table;
  AttributeEntry smallcopy[AttributeMap_MINSIZE];
  int malloced_table;

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

static PyObject *namednodemap_iter(AttributeMapObject *self)
{
  return iter_new(self, &KeyIter_Type);
}

static char namednodemap_doc[] = "\
Objects implementing the AttributeMap interface are used to \
represent collections of nodes that can be accessed by name. \
Note that AttributeMaps are not maintained in any particular order. \
Objects contained in an object implementing AttributeMap may \
also be accessed by an ordinal index, but this is simply to allow \
convenient enumeration of the contents of a AttributeMap, \
and does not imply that the DOM specifies an order to these Nodes.";

static PyTypeObject AttributeMap_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "AttributeMap",
  /* tp_basicsize      */ sizeof(AttributeMapObject),
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
  AttributeMapObject *it_map;
  Py_ssize_t it_used;
  Py_ssize_t it_pos;
  Py_ssize_t it_length;
} IterObject;

static PyObject *iter_new(AttributeMapObject *nodemap, PyTypeObject *itertype)
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
  AttributeMapObject *nodemap = self->it_map;
  Py_ssize_t pos;
  AttrObject *node;

  if (nodemap == NULL)
    return NULL;

  if (self->it_used != nodemap->nm_used) {
    PyErr_Format(PyExc_RuntimeError, "%s changed size during iteration",
                 nodemap->ob_type->tp_name);
    self->it_used = -1;
    return NULL;
  }

  pos = self->it_pos;
  while ((node = AttributeMap_Next((PyObject *)nodemap, &pos))) {
    PyObject *result = PyTuple_Pack(2, Attr_GET_NAMESPACE_URI(node),
                                    Attr_GET_LOCAL_NAME(node));
    if (result == NULL)
      return NULL;
    self->it_length--;
    return result;
  }
  /* iterated over all items, indicate exhausted */
  Py_DECREF(nodemap);
  self->it_map = NULL;
  return NULL;
}

static PyObject *iter_nextvalue(IterObject *self)
{
  AttributeMapObject *nodemap = self->it_map;
  Py_ssize_t pos;
  AttrObject *node;

  if (nodemap == NULL)
    return NULL;

  if (self->it_used != nodemap->nm_used) {
    PyErr_Format(PyExc_RuntimeError, "%s changed size during iteration",
                 nodemap->ob_type->tp_name);
    self->it_used = -1;
    return NULL;
  }

  pos = self->it_pos;
  while ((node = AttributeMap_Next((PyObject *)nodemap, &pos))) {
    PyObject *result = Attr_GET_NODE_VALUE(node);
    Py_INCREF(result);
    self->it_length--;
    return result;
  }
  /* iterated over all items, indicate exhausted */
  Py_DECREF(nodemap);
  self->it_map = NULL;
  return NULL;
}

static PyObject *iter_nextitem(IterObject *self)
{
  AttributeMapObject *nodemap = self->it_map;
  Py_ssize_t pos;
  AttrObject *node;

  if (nodemap == NULL)
    return NULL;

  if (self->it_used != nodemap->nm_used) {
    PyErr_Format(PyExc_RuntimeError, "%s changed size during iteration",
                 nodemap->ob_type->tp_name);
    self->it_used = -1;
    return NULL;
  }

  pos = self->it_pos;
  while ((node = AttributeMap_Next((PyObject *)nodemap, &pos))) {
    PyObject *key, *value, *result;
    key = PyTuple_Pack(2, Attr_GET_NAMESPACE_URI(node),
                       Attr_GET_LOCAL_NAME(node));
    if (key == NULL)
        return NULL;
    value = Attr_GET_NODE_VALUE(node);
    result = PyTuple_New(2);
    if (result == NULL) {
      Py_DECREF(key);
      return NULL;
    }
    PyTuple_SET_ITEM(result, 0, key);
    PyTuple_SET_ITEM(result, 1, value);
    Py_INCREF(value);
    self->it_length--;
    return result;
  }
  /* iterated over all items, indicate exhausted */
  Py_DECREF(nodemap);
  self->it_map = NULL;
  return NULL;
}

static PyObject *iter_nextnode(IterObject *self)
{
  AttributeMapObject *nodemap = self->it_map;
  Py_ssize_t pos;
  AttrObject *node;

  if (nodemap == NULL)
    return NULL;

  if (self->it_used != nodemap->nm_used) {
    PyErr_Format(PyExc_RuntimeError, "%s changed size during iteration",
                 nodemap->ob_type->tp_name);
    self->it_used = -1;
    return NULL;
  }

  pos = self->it_pos;
  while ((node = AttributeMap_Next((PyObject *)nodemap, &pos))) {
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
  AttributeMapObject *nodemap = it->it_map;
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
  /* tp_name           */ "namednodemap-iterator",
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
  /* tp_name           */ "namednodemap-keyiterator",
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
  /* tp_name           */ "namednodemap-valueiterator",
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
  /* tp_name           */ "namednodemap-itemiterator",
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
  /* tp_name           */ "namednodemap-nodeiterator",
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

int DomletteAttributeMap_Init(PyObject *module)
{
  if (PyType_Ready(&AttributeMap_Type) < 0)
    return -1;

  Py_INCREF(&AttributeMap_Type);
  return PyModule_AddObject(module, "AttributeMap",
                            (PyObject*) &AttributeMap_Type);
}

void DomletteAttributeMap_Fini(void)
{
  PyType_CLEAR(&AttributeMap_Type);
}
