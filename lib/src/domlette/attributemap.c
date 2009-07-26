#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

static PyObject *added_event;
static PyObject *removed_event;
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

Py_LOCAL_INLINE(int)
remove_attribute_node(AttrObject *target)
{
  NodeObject *parent = Node_GET_PARENT(target);
  if (parent == NULL) {
    return 0;
  }
  if (!Element_CheckExact(parent)) {
    if (Node_DispatchEvent(parent, removed_event, (NodeObject *)target) < 0)
      return -1;
  }
  Node_SET_PARENT(target, NULL);
  Py_DECREF(parent);
  return 0;
}

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

#define NAME_EQ(a, b) \
  (PyUnicode_GET_SIZE(a) == PyUnicode_GET_SIZE(b) && \
   *PyUnicode_AS_UNICODE(a) == *PyUnicode_AS_UNICODE(b) && \
   !memcmp(PyUnicode_AS_UNICODE(a), PyUnicode_AS_UNICODE(b), \
           PyUnicode_GET_DATA_SIZE(a)))

#define NAMESPACE_EQ(a, b) \
  (((a) == Py_None || (b) == Py_None) ? (a) == (b) : NAME_EQ((a), (b)))

Py_LOCAL_INLINE(int)
key_eq(AttrObject *node, Py_ssize_t hash, register PyObject *name,
       register PyObject *namespace)
{
  register PyObject *node_name = Attr_GET_LOCAL_NAME(node);
  register PyObject *node_namespace = Attr_GET_NAMESPACE_URI(node);
  return ((node_name == name && node_namespace == namespace) ||
          (Attr_GET_HASH(node) == hash && NAME_EQ(node_name, name) &&
           NAMESPACE_EQ(node_namespace, namespace)));
}

Py_LOCAL_INLINE(size_t)
get_entry(AttributeMapObject *nm, Py_ssize_t hash, PyObject *name,
          PyObject *namespace)
{
  register size_t perturb = hash;
  register size_t mask = (size_t)nm->nm_mask;
  register size_t i = perturb & mask;
  register size_t entry = 0;
  AttrObject **table = nm->nm_table;

  while (table[entry] && !key_eq(table[entry], hash, name, namespace)) {
    i = (i << 2) + i + perturb + 1;
    perturb >>= 5;
    entry = i & mask;
  }
  return entry;
}

Py_LOCAL_INLINE(void)
set_entry(AttributeMapObject *nm, AttrObject *node)
{
  register size_t perturb = node->hash;
  register size_t mask = (size_t)nm->nm_mask;
  register size_t i = perturb & mask;
  register size_t entry = i;
  AttrObject **table = nm->nm_table;

  while (table[entry] != NULL) {
    i = (i << 2) + i + perturb + 1;
    perturb >>= 5;
    entry = i & mask;
  }
  table[entry] = node;
}

Py_LOCAL_INLINE(AttrObject *)
next_entry(AttributeMapObject *nm, Py_ssize_t *ppos)
{
  register Py_ssize_t i = *ppos;
  register Py_ssize_t mask = nm->nm_mask;
  register AttrObject **table = nm->nm_table;

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
resize_table(AttributeMapObject *self)
{
  AttrObject **oldtable, **newtable;
  Py_ssize_t size, i;

  /* Get space for a new table. */
  oldtable = self->nm_table;
  size = (self->nm_mask + 1) << 1;
  if (size <= AttributeMap_MINSIZE) {
    size = AttributeMap_MINSIZE;
    newtable = self->nm_smalltable;
    if (oldtable == newtable)
      return 0;
  } else {
    newtable = PyMem_New(AttrObject *, size);
    if (newtable == NULL) {
      PyErr_NoMemory();
      return -1;
    }
  }

  /* Make the dict empty, using the new table. */
  self->nm_table = newtable;
  self->nm_mask = size - 1;
  memset(newtable, 0, sizeof(AttrObject *) * size);

  /* Copy the data over */
  for (i = 0, size = self->nm_used; size > 0; i++) {
    AttrObject *entry = oldtable[i];
    if (entry != NULL) {
      size--;
      set_entry(self, entry);
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
      if (!PyErr_ExceptionMatches(PyExc_TypeError))
        return -1;
      PyErr_Format(PyExc_KeyError,
                    "subscript must be expanded name 2-tuple, unicode string"
                        "%s or UTF-8 byte-string, not '%s'",
                        node_allowed ? ", attribute instance" : "",
                        key->ob_type->tp_name);
      return -2;
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
AttributeMap_New(ElementObject *owner)
{
  register AttributeMapObject *self;

  self = PyObject_GC_New(AttributeMapObject, &AttributeMap_Type);
  if (self != NULL) {
    INIT_MINSIZE(self);
    self->nm_owner = owner;
    Py_INCREF(owner);
    PyObject_GC_Track(self);
  }
  return (PyObject *)self;
}

Py_ssize_t
AttributeMap_GetHash(PyObject *namespace, PyObject *name)
{
  return get_hash(namespace, name);
}

AttrObject *
AttributeMap_GetNode(PyObject *self, PyObject *namespace, PyObject *name)
{
  AttributeMapObject *nm = (AttributeMapObject *)self;
  size_t entry;
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
  return nm->nm_table[entry];
}

int
AttributeMap_SetNode(PyObject *self, AttrObject *node)
{
  AttributeMapObject *nm = (AttributeMapObject *)self;
  size_t entry;
  AttrObject *old_node;
  PyObject *namespace, *name;
  long hash;
  NodeObject *temp;

  if (!AttributeMap_Check(nm)) {
    PyErr_BadInternalCall();
    return -1;
  }
  /* locate an entry in the table for the namespace/name key */
  hash = (long)Attr_GET_HASH(node);
  name = Attr_GET_LOCAL_NAME(node);
  namespace = Attr_GET_NAMESPACE_URI(node);
  entry = get_entry(nm, hash, name, namespace);
  old_node = nm->nm_table[entry];
  if (old_node == NULL) {
    /* adding the attribute to the table */
    nm->nm_used++;
  } else {
    /* replacing the old attribute in the table */
    if (remove_attribute_node(old_node) < 0)
      return -1;
  }
  /* store the attribute in the table */
  nm->nm_table[entry] = node;
  Py_INCREF(node);
  /* update the attribute's owner */
  temp = Node_GET_PARENT(node);
  Node_SET_PARENT(node, (NodeObject *)nm->nm_owner);
  Py_INCREF(nm->nm_owner);
  Py_XDECREF(temp);
  /* success */
  if (!Element_CheckExact(nm->nm_owner)) {
    if (Node_DispatchEvent((NodeObject *)nm->nm_owner, added_event,
                           (NodeObject *)node) < 0)
      return -1;
  }
  /* If fill >= 2/3 size, adjust size.  Normally, this doubles the size,
   * but it's also possible for the dict to shrink. */
  if (nm->nm_used*3 >= (nm->nm_mask+1)*2) {
    if (resize_table(nm) < 0)
      return -1;
  }
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
  return next_entry((AttributeMapObject *)self, ppos);
}

/** Python Methods ****************************************************/

static PyObject *iter_new(AttributeMapObject *self, PyTypeObject *type);

static char attributemap_getnode_doc[] = "\
getnode(namespace, localname) -> attribute node or None\n\
\n\
Retrieves a node specified by local name and namespace URI or None \
if they do not identify a node in this map.";

static PyObject *attributemap_getnode(PyObject *self, PyObject *args)
{
  PyObject *namespace, *name, *result;

  if (!PyArg_ParseTuple(args, "OO:getnode", &namespace, &name))
    return NULL;

  result = (PyObject *)AttributeMap_GetNode(self, namespace, name);
  if (result == NULL) {
    if (PyErr_Occurred())
      return NULL;
    result = Py_None;
  }
  Py_INCREF(result);
  return result;
}

static char attributemap_setnode_doc[] = "\
setnode(node) -> M[node.xml_namespace, node.xml_local] = node.xml_value";

static PyObject *attributemap_setnode(PyObject *self, PyObject *args)
{
  AttrObject *attr;

  if (!PyArg_ParseTuple(args, "O!:setnode", &DomletteAttr_Type, &attr))
    return NULL;

  if (AttributeMap_SetNode(self, attr) < 0)
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char attributemap_get_doc[] =
"M.get(k[,d]) -> M[k] if k in M, else d.  d defaults to None.";

static PyObject *attributemap_get(PyObject *self, PyObject *args)
{
  PyObject *key, *result=Py_None;
  PyObject *namespace, *name;
  AttrObject *node;

  if (!PyArg_ParseTuple(args, "O|O:get", &key, &result))
    return NULL;
  if (parse_key(key, &namespace, &name, 0) < 0) {
    if (!PyErr_ExceptionMatches(PyExc_KeyError))
      return NULL;
    PyErr_Clear();
    goto done;
  }
  node = AttributeMap_GetNode(self, namespace, name);
  Py_DECREF(namespace);
  Py_DECREF(name);
  if (node == NULL) {
    if (PyErr_Occurred())
      return NULL;
  } else {
    result = Attr_GET_VALUE(node);
  }
done:
  Py_INCREF(result);
  return result;
}

static char attributemap_keys_doc[] =
"M.keys() -> list of expanded name 2-tuples";

static PyObject *attributemap_keys(AttributeMapObject *self)
{
  register PyObject *keys;
  register Py_ssize_t i, n;
  register AttrObject **ptr;

  n = self->nm_used;
  keys = PyList_New(n);
  if (keys == NULL)
    return NULL;
  for (i = 0, ptr = self->nm_table; i < n; ptr++) {
    AttrObject *node = *ptr;
    if (node != NULL) {
      PyObject *key = PyTuple_Pack(2, Attr_GET_NAMESPACE_URI(node),
                                   Attr_GET_LOCAL_NAME(node));
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

static char attributemap_values_doc[] =
"M.values() -> list of node values";

static PyObject *attributemap_values(AttributeMapObject *self)
{
  register PyObject *values;
  register Py_ssize_t i, n;
  register AttrObject **ptr;

  n = self->nm_used;
  values = PyList_New(n);
  if (values == NULL)
    return NULL;
  for (i = 0, ptr = self->nm_table; i < n; ptr++) {
    AttrObject *node = *ptr;
    if (node != NULL) {
      PyObject *value = Attr_GET_VALUE(node);
      Py_INCREF(value);
      PyList_SET_ITEM(values, i, value);
      i++;
    }
  }
  return values;
}

static char attributemap_items_doc[] =
"M.items() -> list of M's (expanded name, value) pairs, as 2-tuples";

static PyObject *attributemap_items(AttributeMapObject *self)
{
  register PyObject *items;
  register Py_ssize_t i, n;
  register AttrObject **ptr;
  PyObject *key, *item;

  n = self->nm_used;
  items = PyList_New(n);
  if (items == NULL)
    return NULL;
  for (i = 0, ptr = self->nm_table; i < n; ptr++) {
    AttrObject *node = *ptr;
    if (node != NULL) {
      key = PyTuple_Pack(2, Attr_GET_NAMESPACE_URI(node),
                         Attr_GET_LOCAL_NAME(node));
      if (key == NULL) {
        Py_DECREF(items);
        return NULL;
      }
      item = PyTuple_Pack(2, key, Attr_GET_VALUE(node));
      Py_DECREF(key);
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

static char attributemap_copy_doc[] =
"M.copy() -> a copy of M as a dictionary";

static PyObject *attributemap_copy(AttributeMapObject *self)
{
  register PyObject *copy;
  register Py_ssize_t i, n;
  register AttrObject **ptr;

  copy = PyDict_New();
  if (copy == NULL)
    return NULL;
  for (i = 0, n = self->nm_used, ptr = self->nm_table; i < n; ptr++) {
    AttrObject *node = *ptr;
    if (node != NULL) {
      PyObject *key = PyTuple_Pack(2, Attr_GET_NAMESPACE_URI(node),
                                   Attr_GET_LOCAL_NAME(node));
      if (key == NULL) {
        Py_DECREF(copy);
        return NULL;
      }
      if (PyDict_SetItem(copy, key, Attr_GET_VALUE(node)) < 0) {
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

static char attributemap_iterkeys_doc[] =
"M.iterkeys() -> an iterator over the expanded name 2-tuples of M";

static PyObject *attributemap_iterkeys(AttributeMapObject *self)
{
  return iter_new(self, &KeyIter_Type);
}

static char attributemap_itervalues_doc[] =
"M.itervalues() -> an iterator over the node values of M";

static PyObject *attributemap_itervalues(AttributeMapObject *self)
{
  return iter_new(self, &ValueIter_Type);
}

static char attributemap_iteritems_doc[] =
"M.iteritems() -> an iterator over the (expanded name, value) items of M";

static PyObject *attributemap_iteritems(AttributeMapObject *self)
{
  return iter_new(self, &ItemIter_Type);
}

static char attributemap_nodes_doc[] =
"M.nodes() -> an iterator over the attribute nodes of M";

static PyObject *attributemap_nodes(AttributeMapObject *self)
{
  return iter_new(self, &NodeIter_Type);
}

#define AttributeMap_METHOD(NAME, FLAGS)             \
  { #NAME, (PyCFunction) attributemap_##NAME, FLAGS, \
      attributemap_##NAME##_doc }

static PyMethodDef attributemap_methods[] = {
  AttributeMap_METHOD(getnode,    METH_VARARGS),
  AttributeMap_METHOD(setnode,    METH_VARARGS),
  /* Python Mapping Interface */
  AttributeMap_METHOD(get,        METH_VARARGS),
  AttributeMap_METHOD(keys,       METH_NOARGS),
  AttributeMap_METHOD(values,     METH_NOARGS),
  AttributeMap_METHOD(items,      METH_NOARGS),
  AttributeMap_METHOD(copy,       METH_NOARGS),
  AttributeMap_METHOD(iterkeys,   METH_NOARGS),
  AttributeMap_METHOD(itervalues, METH_NOARGS),
  AttributeMap_METHOD(iteritems,  METH_NOARGS),
  AttributeMap_METHOD(nodes,      METH_NOARGS),
  { NULL }
};

static Py_ssize_t
attributemap_length(AttributeMapObject *self)
{
  return self->nm_used;
}

static PyObject *
attributemap_subscript(PyObject *op, PyObject *key)
{
  PyObject *namespace, *name;
  AttrObject *node;

  if (parse_key(key, &namespace, &name, 0) < 0)
    return NULL;
  node = AttributeMap_GetNode(op, namespace, name);
  Py_DECREF(namespace);
  Py_DECREF(name);
  if (node == NULL) {
    if (!PyErr_Occurred())
      PyErr_SetObject(PyExc_KeyError, key);
    return NULL;
  }
  Py_INCREF(Attr_GET_VALUE(node));
  return Attr_GET_VALUE(node);
}

static int
attributemap_ass_subscript(PyObject *op, PyObject *key, PyObject *value)
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
    value = XmlString_ConvertArgument(value, "value", 0);
    if (value == NULL) {
      Py_DECREF(namespace);
      Py_DECREF(name);
      return -1;
    }
    attr = AttributeMap_GetNode(op, namespace, name);
    if (attr == NULL) {
      if (PyErr_Occurred()) {
        result = -1;
      } else {
        attr = Element_AddAttribute(((AttributeMapObject *)op)->nm_owner,
                                    namespace, NULL, name, value);
        if (attr == NULL) {
          result = -1;
        } else {
          Py_DECREF(attr);
          result = 0;
        }
      }
    } else {
      /* just update the node value */
      result = Attr_SetValue(attr, value);
    }
    Py_DECREF(value);
  }
  Py_DECREF(namespace);
  Py_DECREF(name);
  return result;
}

static PyMappingMethods attributemap_as_mapping = {
  /* mp_length        */ (lenfunc) attributemap_length,
  /* mp_subscript     */ (binaryfunc) attributemap_subscript,
  /* mp_ass_subscript */ (objobjargproc) attributemap_ass_subscript,
};

static int attributemap_contains(AttributeMapObject *self, PyObject *key)
{
  PyObject *namespace, *name;
  Py_ssize_t hash, entry;
  int status;

  if (Attr_Check(key)) {
    AttrObject *node;
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
  if ((status = parse_key(key, &namespace, &name, 1)) < 0) {
    if (status < -1) {
      PyErr_Clear();
      return 0;
    }
    return -1;
  }
  hash = get_hash(namespace, name);
  if (hash == -1) {
    Py_DECREF(namespace);
    Py_DECREF(name);
    return -1;
  }
  entry = get_entry(self, hash, name, namespace);
  Py_DECREF(namespace);
  Py_DECREF(name);
  return self->nm_table[entry] != NULL;
}

static PySequenceMethods attributemap_as_sequence = {
  /* sq_length         */ 0,
  /* sq_concat         */ 0,
  /* sq_repeat         */ 0,
  /* sq_item           */ 0,
  /* sq_slice          */ 0,
  /* sq_ass_item       */ 0,
  /* sq_ass_slice      */ 0,
  /* sq_contains       */ (objobjproc) attributemap_contains,
  /* sq_inplace_concat */ 0,
  /* sq_inplace_repeat */ 0,
};

/** Python Members ****************************************************/

static PyMemberDef attributemap_members[] = {
  { NULL }
};

/** Python Computed Members *******************************************/

static PyGetSetDef attributemap_getset[] = {
  { NULL }
};

/** Type Object ********************************************************/

static void attributemap_dealloc(AttributeMapObject *self)
{
  register AttrObject **table = self->nm_table;
  register size_t entry;
  register Py_ssize_t used;

  PyObject_GC_UnTrack(self);
  Py_XDECREF(self->nm_owner);
  /* clear attribute nodes */
  Py_TRASHCAN_SAFE_BEGIN(self);
  for (entry = 0, used = self->nm_used; used > 0; entry++) {
    if (table[entry] != NULL) {
      used--;
      Py_DECREF(table[entry]);
    }
  }
  Py_TRASHCAN_SAFE_END(self);
  /* dealloc node table */
  if (table != self->nm_smalltable)
    PyMem_Free(table);
  ((PyObject *)self)->ob_type->tp_free((PyObject *)self);
}

static PyObject *attributemap_repr(AttributeMapObject *self)
{
  return PyString_FromFormat("<attributemap at %p: %zd nodes>",
                             self, self->nm_used);
}

static int attributemap_traverse(AttributeMapObject *self, visitproc visit,
                                 void *arg)
{
  Py_ssize_t i = 0;
  AttrObject *node;

  Py_VISIT(self->nm_owner);
  while ((node = next_entry(self, &i)))
    Py_VISIT(node);

  return 0;
}

static int attributemap_clear(AttributeMapObject *self)
{
  register AttrObject **table = self->nm_table;
  register Py_ssize_t used = self->nm_used;
  register size_t entry;
  AttrObject *smallcopy[AttributeMap_MINSIZE];
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

static PyObject *attributemap_iter(AttributeMapObject *self)
{
  return iter_new(self, &KeyIter_Type);
}

static char attributemap_doc[] = "\
Objects implementing the AttributeMap interface are used to \
represent collections of nodes that can be accessed by name.";

static PyTypeObject AttributeMap_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "attributemap",
  /* tp_basicsize      */ sizeof(AttributeMapObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) attributemap_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) attributemap_repr,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) &attributemap_as_sequence,
  /* tp_as_mapping     */ (PyMappingMethods *) &attributemap_as_mapping,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) 0,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
  /* tp_doc            */ (char *) attributemap_doc,
  /* tp_traverse       */ (traverseproc) attributemap_traverse,
  /* tp_clear          */ (inquiry) attributemap_clear,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) attributemap_iter,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) attributemap_methods,
  /* tp_members        */ (PyMemberDef *) attributemap_members,
  /* tp_getset         */ (PyGetSetDef *) attributemap_getset,
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
  AttrObject *node;

  if (nodemap == NULL)
    return NULL;

  if (self->it_used != nodemap->nm_used) {
    PyErr_Format(PyExc_RuntimeError, "%s changed size during iteration",
                 nodemap->ob_type->tp_name);
    self->it_used = -1;
    return NULL;
  }

  while ((node = next_entry(nodemap, &self->it_pos))) {
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
  AttrObject *node;

  if (nodemap == NULL)
    return NULL;

  if (self->it_used != nodemap->nm_used) {
    PyErr_Format(PyExc_RuntimeError, "%s changed size during iteration",
                 nodemap->ob_type->tp_name);
    self->it_used = -1;
    return NULL;
  }

  while ((node = next_entry(nodemap, &self->it_pos))) {
    PyObject *result = Attr_GET_VALUE(node);
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
  AttrObject *node;

  if (nodemap == NULL)
    return NULL;

  if (self->it_used != nodemap->nm_used) {
    PyErr_Format(PyExc_RuntimeError, "%s changed size during iteration",
                 nodemap->ob_type->tp_name);
    self->it_used = -1;
    return NULL;
  }

  while ((node = next_entry(nodemap, &self->it_pos))) {
    PyObject *key, *value, *result;
    key = PyTuple_Pack(2, Attr_GET_NAMESPACE_URI(node),
                       Attr_GET_LOCAL_NAME(node));
    if (key == NULL)
        return NULL;
    value = Attr_GET_VALUE(node);
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
  AttrObject *node;

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
  /* tp_name           */ "attributemap-iterator",
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
  /* tp_name           */ "attributemap-keyiterator",
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
  /* tp_name           */ "attributemap-valueiterator",
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
  /* tp_name           */ "attributemap-itemiterator",
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
  /* tp_name           */ "attributemap-nodeiterator",
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
  if (PyType_Ready(&AttributeMap_Type) < 0)
    return -1;

  added_event = PyString_FromString("xml_attribute_added");
  if (added_event == NULL)
    return -1;
  removed_event = PyString_FromString("xml_attribute_removed");
  if (removed_event == NULL)
    return -1;

  return 0;
}

void DomletteAttributeMap_Fini(void)
{
  Py_DECREF(added_event);
  Py_DECREF(removed_event);
  PyType_CLEAR(&AttributeMap_Type);
}
