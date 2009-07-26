#include "xslt_element.h"
#include "xslt_root.h"
#include "xmlstring.h"

static PyObject *namespaces_string;
static PyObject *instruction_string;
static PyObject *instantiate_string;

static PyObject *empty_dict;

/** Private Routines **************************************************/

#define XsltElement_SET_COUNT(op, v) (XsltElement_GET_COUNT(op) = (v))
#define XsltElement_SET_NODES(op, v) (XsltElement_GET_NODES(op) = (v))
#define XsltElement_SET_CHILD(op, i, v) (XsltElement_GET_NODES(op)[i] = (v))

static int element_resize(XsltElementObject *self, Py_ssize_t newsize) {
  XsltNodeObject **nodes;
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
  if (new_allocated <= ((~(size_t)0) / sizeof(XsltNodeObject *)))
    PyMem_Resize(nodes, XsltNodeObject *, new_allocated);
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

static PyObject *process_children(XsltElementObject *self, PyObject *args,
                                  PyObject *context)
{
  Py_ssize_t i, size;

  if (PyObject_SetAttr(context, instruction_string, (PyObject *)self) == -1)
    return NULL;
  if (PyObject_SetAttr(context, namespaces_string, self->namespaces) == -1)
    return NULL;

  size = XsltElement_GET_COUNT(self);
  for (i = 0; i < size; i++) {
    PyObject *child, *method, *result;
    child = (PyObject *) XsltElement_GET_CHILD(self, i);
    method = PyObject_GetAttr(child, instantiate_string);
    if (method == NULL) {
      return NULL;
    }
    result = PyObject_CallObject(method, args);
    Py_DECREF(method);
    if (result == NULL) {
      return NULL;
    }
    Py_DECREF(result);
  }

  Py_INCREF(Py_None);
  return Py_None;
}

/** Public C API ******************************************************/

int XsltElement_AppendChild(XsltElementObject *self, XsltNodeObject *child)
{
  Py_ssize_t count;

  if (!XsltElement_Check(self) || !XsltNode_Check(child)) {
    PyErr_BadInternalCall();
    return -1;
  }

  /* Add the new child to the end of our array */
  count = XsltElement_GET_COUNT(self);
  if (element_resize(self, count + 1) == -1)
    return -1;
  Py_INCREF(child);
  XsltElement_SET_CHILD(self, count, child);

  return XsltNode_Link(XsltNode(self), child);
}


int XsltElement_InsertChild(XsltElementObject *self, XsltNodeObject *child,
                            Py_ssize_t where)
{
  XsltNodeObject **nodes;
  Py_ssize_t count, i;

  if (!XsltElement_Check(self) || !XsltNode_Check(child)) {
    PyErr_BadInternalCall();
    return -1;
  }

  count = XsltElement_GET_COUNT(self);
  if (element_resize(self, count + 1) == -1)
    return -1;

  if (where < 0) {
    where += count;
    if (where < 0)
      where = 0;
  }
  if (where > count)
    where = count;

  /* Shift the effected nodes up one */
  nodes = XsltElement_GET_NODES(self);
  for (i = count; --i >= where;)
    nodes[i+1] = nodes[i];

  /* Set the new child in the array */
  Py_INCREF(child);
  XsltElement_SET_CHILD(self, where, child);

  return XsltNode_Link(XsltNode(self), child);
}


int XsltElement_Merge(XsltElementObject *self, XsltElementObject *other)
{
  Py_ssize_t count, newcount, i;

  if (!XsltElement_Check(self) || !XsltElement_Check(other)) {
    PyErr_BadInternalCall();
    return -1;
  }

  /* Add the nodes to our children */
  count = XsltElement_GET_COUNT(self);
  newcount = count + XsltElement_GET_COUNT(other);
  if (element_resize(self, newcount) < 0)
    return -1;

  for (i = 0; count < newcount; i++, count++) {
    XsltNodeObject *child = XsltElement_GET_CHILD(other, i);
    Py_INCREF(child);
    XsltElement_SET_CHILD(self, count, child);
    Py_DECREF(child->parent);
    Py_INCREF((PyObject *) self);
    child->parent = (PyObject *) self;
  }

  /* remove them from the other element */
  if (element_resize(other, 0) < 0) {
    return -1;
  }

  return 0;
}

int XsltElement_SetAttribute(XsltElementObject *self, PyObject *namespaceURI,
                             PyObject *localName, PyObject *value)
{
  PyObject *key;
  int rc;

  if (self->attributes == empty_dict) {
    PyObject *temp = PyDict_New();
    if (temp == NULL) return -1;
    Py_DECREF(self->attributes);
    self->attributes = temp;
  }

  key = PyTuple_New(2);
  if (key == NULL) {
    return -1;
  }
  Py_INCREF(namespaceURI);
  PyTuple_SET_ITEM(key, 0, namespaceURI);
  Py_INCREF(localName);
  PyTuple_SET_ITEM(key, 1, localName);

  rc = PyDict_SetItem(self->attributes, key, value);
  Py_DECREF(key);
  return rc;
}

/** Python Methods *****************************************************/

static char appendChild_doc[] = "\
appendChild(newChild)\n\
\n\
Adds the node `newChild` to the end of the list of children of this node.";

static PyObject *element_appendChild(XsltElementObject *self, PyObject *args)
{
  PyObject *child;

  if (!PyArg_ParseTuple(args, "O!:appendChild", &XsltNode_Type, &child))
    return NULL;

  if (XsltElement_AppendChild(self, (XsltNodeObject *) child) == -1) {
    return NULL;
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static char insertChild_doc[] = "\
insertChild(index, child)\n\
\n\
Inserts the child at the given position in the children list.";

static PyObject *element_insertChild(XsltElementObject *self, PyObject *args)
{
  Py_ssize_t index;
  XsltNodeObject *child;

  if (!PyArg_ParseTuple(args, "iO!:insertChild", &index, &XsltNode_Type,
                        &child))
    return NULL;

  if (XsltElement_InsertChild(self, (XsltNodeObject *) child, index) == -1)
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char setAttribute_doc[] = "\
setAttribute(namespaceURI, localName, value)\n\
\n\
Sets the attribute in the attributes mapping.";

static PyObject *element_setAttribute(XsltElementObject *self, PyObject *args)
{
  PyObject *namespaceURI, *localName, *value;

  if (!PyArg_ParseTuple(args, "OOO:setAttribute",
                        &namespaceURI, &localName, &value))
    return NULL;

  if (XsltElement_SetAttribute(self, namespaceURI, localName, value) < 0) {
    return NULL;
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static char instantiate_doc[] = "\
instantiate(context)\n\
\n\
Implements default behavior for extension elements.";

static PyObject *element_instantiate(XsltElementObject *self, PyObject *args)
{
  PyObject *context;

  if (!PyArg_ParseTuple(args, "O:instantiate", &context))
    return NULL;

  return process_children(self, args, context);
}

static char process_children_doc[] = "\
process_children(context)\n\
\n\
Utility method to instantiate each child in order.";

static PyObject *element_process_children(XsltElementObject *self,
                                          PyObject *args)
{
  PyObject *context;

  if (!PyArg_ParseTuple(args, "O:process_children", &context))
    return NULL;

  return process_children(self, args, context);
}

static char _merge_doc[] = "";
static PyObject *element__merge(XsltElementObject *self, PyObject *args)
{
  XsltElementObject *stylesheet;

  if (!PyArg_ParseTuple(args, "O!:_merge", &XsltElement_Type, &stylesheet))
    return NULL;

  if (XsltElement_Merge(self, stylesheet) < 0)
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char getstate_doc[] = "helper for pickle";

static PyObject *element_getstate(XsltElementObject *self, PyObject *args)
{
  PyObject *state, *temp;
  Py_ssize_t i;

  if (!PyArg_ParseTuple(args, ":__getstate__"))
    return NULL;

  state = PyTuple_New(12);
  if (state == NULL)
    return NULL;

  /* XsltElement.root */
  Py_INCREF(XsltNode_ROOT(self));
  PyTuple_SET_ITEM(state, 0, XsltNode_ROOT(self));

  /* XsltElement.parent */
  Py_INCREF(XsltNode_GET_PARENT(self));
  PyTuple_SET_ITEM(state, 1, XsltNode_GET_PARENT(self));

  /* XsltElement.children */
  i = self->count;
  temp = PyTuple_New(i);
  if (temp == NULL) {
    Py_DECREF(state);
    return NULL;
  }
  while (i-- > 0) {
    PyObject *v = (PyObject *) XsltElement_GET_CHILD(self, i);
    Py_INCREF(v);
    PyTuple_SET_ITEM(temp, i, v);
  }
  PyTuple_SET_ITEM(state, 2, temp);

  /* XsltElement.nodeName */
  Py_INCREF(self->nodeName);
  PyTuple_SET_ITEM(state, 3, self->nodeName);

  /* XsltElement.expanded_name */
  Py_INCREF(self->expanded_name);
  PyTuple_SET_ITEM(state, 4, self->expanded_name);

  /* XsltElement.attributes */
  Py_INCREF(self->attributes);
  PyTuple_SET_ITEM(state, 5, self->attributes);

  /* XsltElement.namespaces */
  Py_INCREF(self->namespaces);
  PyTuple_SET_ITEM(state, 6, self->namespaces);

  /* XsltElement.baseUri */
  Py_INCREF(self->baseUri);
  PyTuple_SET_ITEM(state, 7, self->baseUri);

  /* XsltElement.lineNumber */
  temp = PyInt_FromLong(self->lineNumber);
  if (temp == NULL) {
    Py_DECREF(state);
    return NULL;
  }
  PyTuple_SET_ITEM(state, 8, temp);

  /* XsltElement.columnNumber */
  temp = PyInt_FromLong(self->columnNumber);
  if (temp == NULL) {
    Py_DECREF(state);
    return NULL;
  }
  PyTuple_SET_ITEM(state, 9, temp);

  /* XsltElement.import_precedence */
  temp = PyInt_FromLong(self->import_precedence);
  if (temp == NULL) {
    Py_DECREF(state);
    return NULL;
  }
  PyTuple_SET_ITEM(state, 10, temp);

  /* instance dict */
  temp = PyObject_GetAttrString((PyObject *) self, "__dict__");
  if (temp == NULL) {
    PyErr_Clear();
    temp = Py_None;
    Py_INCREF(Py_None);
  }
  PyTuple_SET_ITEM(state, 11, temp);
  return state;
}

static char setstate_doc[] = "helper for pickle";

static PyObject *element_setstate(XsltElementObject *self, PyObject *args)
{
  PyObject *root, *parent, *children, *name, *expanded, *attributes;
  PyObject *namespaces, *base, *dict, *temp;
  int line, column, precedence;
  Py_ssize_t i, n;
  XsltNodeObject *child;

  if (!PyArg_ParseTuple(args, "(OOO!OO!OOOOOOO):__setstate__", &root, &parent,
                        &PyTuple_Type, &children, &name,
                        &PyTuple_Type, &expanded, &attributes, &namespaces,
                        &base, &line, &column, &precedence, &dict))
    return NULL;

  temp = XsltNode_ROOT(self);
  Py_INCREF(root);
  XsltNode_ROOT(self) = root;
  Py_DECREF(temp);

  temp = XsltNode_GET_PARENT(self);
  Py_INCREF(parent);
  XsltNode_SET_PARENT(self, parent);
  Py_DECREF(temp);

  n = XsltElement_GET_COUNT(self);
  for (i = 0; i < n; i++) {
    child = XsltElement_GET_CHILD(self, i);
    Py_DECREF(child);
  }
  n = PyTuple_GET_SIZE(children);
  if (element_resize(self, n) < 0)
    return NULL;
  for (i = 0; i < n; i++) {
    child = (XsltNodeObject *) PyTuple_GET_ITEM(children, i);
    assert(PyObject_IsInstance((PyObject *)child, (PyObject *)&XsltNode_Type));
    Py_INCREF(child);
    XsltElement_SET_CHILD(self, i, child);
  }

  temp = self->nodeName;
  Py_INCREF(name);
  self->nodeName = name;
  Py_DECREF(temp);

  temp = self->expanded_name;
  Py_INCREF(expanded);
  self->expanded_name = expanded;
  Py_DECREF(temp);

  /* only update attributes if there are any to add to preserve
     "empty_dict" optimization.
  */
  if (PyObject_IsTrue(attributes)) {
    temp = self->attributes;
    Py_INCREF(attributes);
    self->attributes = attributes;
    Py_DECREF(temp);
  }

  temp = self->namespaces;
  Py_INCREF(namespaces);
  self->namespaces = namespaces;
  Py_DECREF(temp);

  temp = self->baseUri;
  Py_INCREF(base);
  self->baseUri = base;
  Py_DECREF(temp);

  self->lineNumber = line;
  self->columnNumber = column;
  self->import_precedence = precedence;

  if (dict != Py_None) {
    PyObject *key, *value;
    if (!PyDict_Check(dict)) {
      PyErr_SetString(PyExc_TypeError, "argument 12 is not a dictionary");
      return NULL;
    }
    i = 0;
    while (PyDict_Next(dict, &i, &key, &value)) {
      if (PyObject_SetAttr((PyObject *)self, key, value) < 0)
        return NULL;
    }
  }

  Py_INCREF(Py_None);
  return Py_None;
}

#define XsltElement_METHOD(NAME)                                        \
  { #NAME, (PyCFunction) element_##NAME, METH_VARARGS, NAME##_doc }

static struct PyMethodDef element_methods[] = {
  XsltElement_METHOD(appendChild),
  XsltElement_METHOD(insertChild),
  XsltElement_METHOD(setAttribute),

  XsltElement_METHOD(instantiate),

  XsltElement_METHOD(process_children),

  XsltElement_METHOD(_merge),

  { "__getstate__", (PyCFunction) element_getstate, METH_VARARGS,
    getstate_doc },
  { "__setstate__", (PyCFunction) element_setstate, METH_VARARGS,
    setstate_doc },
  { NULL }
};


/** Python Members ****************************************************/

#define XsltElement_MEMBER(name, type, flags) \
  { #name, type, offsetof(XsltElementObject, name), flags }

static struct PyMemberDef element_members[] = {
  XsltElement_MEMBER(expanded_name, T_OBJECT, READONLY),
  XsltElement_MEMBER(nodeName, T_OBJECT, READONLY),
  XsltElement_MEMBER(attributes, T_OBJECT, READONLY),
  XsltElement_MEMBER(namespaces, T_OBJECT, READONLY),
  XsltElement_MEMBER(baseUri, T_OBJECT, 0),
  XsltElement_MEMBER(lineNumber, T_INT, 0),
  XsltElement_MEMBER(columnNumber, T_INT, 0),
  XsltElement_MEMBER(import_precedence, T_INT, 0),
  { NULL }
};

/** Python Computed Members ********************************************/

static PyObject *get_prefix(XsltElementObject *self, char *arg)
{
  Py_UNICODE *p;
  Py_ssize_t size, i;

  p = PyUnicode_AS_UNICODE(self->nodeName);
  size = PyUnicode_GET_SIZE(self->nodeName);
  for (i = 0; i < size; i++) {
    if (p[i] == ':') {
      return PyUnicode_FromUnicode(p, i);
    }
  }
  Py_INCREF(Py_None);
  return Py_None;
}

static int set_prefix(XsltElementObject *self, PyObject *v, char *arg)
{
  PyObject *nodeName, *prefix, *localName;
  Py_UNICODE *p;
  Py_ssize_t size;

  prefix = XmlString_ConvertArgument(v, arg, 1);
  if (prefix == NULL) {
    return -1;
  }

  assert(self->expanded_name != NULL);
  localName = PyTuple_GET_ITEM(self->expanded_name, 1);

  if (prefix == Py_None) {
    Py_DECREF(self->nodeName);
    Py_INCREF(localName);
    self->nodeName = localName;
    return 0;
  }

  /* rebuild the qualifiedName */
  size = PyUnicode_GET_SIZE(prefix) + 1 + PyUnicode_GET_SIZE(localName);
  nodeName = PyUnicode_FromUnicode(NULL, size);
  if (nodeName == NULL) {
    Py_DECREF(prefix);
    return -1;
  }

  /* copy the prefix to the qualifiedName string */
  p = PyUnicode_AS_UNICODE(nodeName);
  size = PyUnicode_GET_SIZE(prefix);
  Py_UNICODE_COPY(p, PyUnicode_AS_UNICODE(prefix), size);
  Py_DECREF(prefix);
  p += size;

  /* add the ':' separator */
  *p++ = (Py_UNICODE) ':';

  /* add the localName after the ':' to finish the qualifiedName */
  Py_UNICODE_COPY(p,
                  PyUnicode_AS_UNICODE(localName),
                  PyUnicode_GET_SIZE(localName));

  Py_DECREF(self->nodeName);
  self->nodeName = nodeName;
  return 0;
}

static PyObject *element_iter(XsltElementObject *element);

static PyObject *get_children(XsltElementObject *self, void *arg)
{
  PyObject *nodes;
  Py_ssize_t i, size = self->count;

  nodes = PyTuple_New(size);
  if (nodes) {
    for (i = 0; i < size; i++) {
      PyObject *node = (PyObject *)self->nodes[i];
      Py_INCREF(node);
      PyTuple_SET_ITEM(nodes, i, node);
    }
  }
  return nodes;
}

static PyObject *get_attributes(XsltElementObject *self, void *arg)
{
  if (self->attributes == empty_dict) {
    Py_INCREF(empty_dict);
    return empty_dict;
  }
  return PyDictProxy_New(self->attributes);
}

static PyObject *get_last_instruction(XsltElementObject *self, void *arg)
{
  Py_ssize_t size = self->count;
  if (size > 0) {
    XsltNodeObject *node = self->nodes[size-1];
    if (XsltElement_Check(node)) {
      Py_INCREF(node);
      return (PyObject *)node;
    }
  }
  Py_INCREF(Py_None);
  return Py_None;
}

static struct PyGetSetDef element_getset[] = {
  { "prefix",     (getter) get_prefix, (setter) set_prefix, NULL, "prefix" },
  { "children",   (getter) get_children },
  { "attributes", (getter) get_attributes },
  { "last_instruction", (getter) get_last_instruction },
  { NULL }
};


/** Type Object ********************************************************/


static PyObject *element_repr(XsltElementObject *self)
{
  PyObject *name, *repr;

  name = PyObject_Repr(self->nodeName);
  if (name == NULL) return NULL;

  repr = PyString_FromFormat("<XsltElement at %p: "
                             "name %s, "
                             "%" PY_FORMAT_SIZE_T "d attributes, "
                             "%" PY_FORMAT_SIZE_T "d children, "
                             "precedence %d>",
                             self,
                             PyString_AS_STRING(name),
                             PyMapping_Length(self->attributes),
                             XsltElement_GET_COUNT(self),
                             XsltElement_IMPORT_PRECEDENCE(self));
  Py_DECREF(name);

  return repr;
}

static int element_traverse(XsltElementObject *self, visitproc visit,
                            void *arg)
{
  Py_ssize_t i;

  for (i = XsltElement_GET_COUNT(self); --i >= 0;) {
    Py_VISIT(XsltElement_GET_CHILD(self, i));
  }
  Py_VISIT(self->attributes);
  Py_VISIT(self->namespaces);
  assert(XsltNode_Type.tp_traverse);
  return XsltNode_Type.tp_traverse((PyObject *)self, visit, arg);
}

static int element_clear(XsltElementObject *self)
{
  XsltNodeObject **nodes = self->nodes;
  Py_ssize_t i;

  if (nodes != NULL) {
    i = self->count;
    self->nodes = NULL;
    self->count = 0;
    self->allocated = 0;
    while (--i >= 0) {
      Py_DECREF(nodes[i]);
    }
    PyMem_Free(nodes);
  }
  Py_CLEAR(self->attributes);
  Py_CLEAR(self->namespaces);
  assert(XsltNode_Type.tp_clear);
  return XsltNode_Type.tp_clear((PyObject *)self);
}

static void element_dealloc(XsltElementObject *self)
{
  element_clear(self);
  assert(XsltNode_Type.tp_dealloc);
  XsltNode_Type.tp_dealloc((PyObject *)self);
}

/* initialize everything a subclass cannot change */
static int element_init(XsltElementObject *self, PyObject *args,
                        PyObject *kwds)
{
  PyObject *root, *expanded_name, *qname, *namespaces=NULL, *attributes=NULL;
  PyObject *temp;
  static char *kwlist[] = { "root", "expanded_name", "qname",
                            "namespaces", "attributes", NULL };

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O!OO|O!O!:XsltElement", kwlist,
                                   &XsltRoot_Type, &root,
                                   &expanded_name, &qname,
                                   &PyDict_Type, &namespaces,
                                   &PyDict_Type, &attributes))
    return -1;

  temp = XsltNode_ROOT(self);
  Py_INCREF(root);
  XsltNode_ROOT(self) = root;
  Py_DECREF(temp);

  temp = self->expanded_name;
  Py_INCREF(expanded_name);
  self->expanded_name = expanded_name;
  Py_DECREF(temp);

  temp = self->nodeName;
  Py_INCREF(qname);
  self->nodeName = qname;
  Py_DECREF(temp);

  if (namespaces != NULL) {
    namespaces = PyDictProxy_New(namespaces);
    if (namespaces == NULL)
      return -1;
    temp = self->namespaces;
    self->namespaces = namespaces;
    Py_DECREF(temp);
  }

  if (attributes != NULL) {
    temp = self->attributes;
    Py_INCREF(attributes);
    self->attributes = attributes;
    Py_DECREF(temp);
  }

  return 0;
}

static PyObject *element_new(PyTypeObject *type, PyObject *args,
                             PyObject *kwds)
{
  XsltElementObject *self;

  self = (XsltElementObject *) XsltNode_New(type);
  if (self != NULL) {
    self->count = 0;
    self->nodes = NULL;
    self->allocated = 0;

    Py_INCREF(Py_None);
    self->expanded_name = Py_None;

    Py_INCREF(Py_None);
    self->nodeName = Py_None;

    Py_INCREF(empty_dict);
    self->attributes = empty_dict;

    Py_INCREF(empty_dict);
    self->namespaces = empty_dict;

    Py_INCREF(Py_None);
    self->baseUri = Py_None;
    self->lineNumber = -1;
    self->columnNumber = -1;
  }

  return (PyObject *) self;
}

static char element_doc[] = "\
The Element interface represents an XML element in the Stylesheet Tree.";

PyTypeObject XsltElement_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "amara.xslt.tree.xslt_element",
  /* tp_basicsize      */ sizeof(XsltElementObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) element_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) element_repr,
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
  /* tp_doc            */ (char *) element_doc,
  /* tp_traverse       */ (traverseproc) element_traverse,
  /* tp_clear          */ (inquiry) element_clear,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) element_iter,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) element_methods,
  /* tp_members        */ (PyMemberDef *) element_members,
  /* tp_getset         */ (PyGetSetDef *) element_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) element_init,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) element_new,
  /* tp_free           */ 0,
};

/** Node ChildNodes Iterator ******************************************/

typedef struct {
  PyObject_HEAD
  Py_ssize_t index;
  PyObject *node; /* NULL when iterator is done */
} NodeIterObject;

static PyTypeObject NodeIter_Type;

static PyObject *element_iter(XsltElementObject *node)
{
  NodeIterObject *iter;

  iter = PyObject_GC_New(NodeIterObject, &NodeIter_Type);
  if (iter == NULL)
    return NULL;

  iter->index = 0;

  Py_INCREF((PyObject *) node);
  iter->node = (PyObject *) node;

  PyObject_GC_Track(iter);

  return (PyObject *) iter;
}

static void nodeiter_dealloc(NodeIterObject *iter)
{
  PyObject_GC_UnTrack(iter);

  Py_XDECREF((PyObject *) iter->node);

  PyObject_GC_Del(iter);
}

static int nodeiter_traverse(NodeIterObject *iter, visitproc visit, void *arg)
{
  if (iter->node == NULL)
    return 0;
  return visit((PyObject *)iter->node, arg);
}

static PyObject *nodeiter_iter(NodeIterObject *iter)
{
  Py_INCREF(iter);
  return (PyObject *)iter;
}

static PyObject *nodeiter_next(NodeIterObject *iter)
{
  PyObject *node, *item;

  node = (PyObject *) iter->node;
  if (node == NULL)
    return NULL;

  if (iter->index < XsltElement_GET_COUNT(node)) {
    item = (PyObject *) XsltElement_GET_CHILD(node, iter->index);
    iter->index++;
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
  /* tp_name           */ "nodeiter",
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
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT |
                           Py_TPFLAGS_HAVE_GC),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) nodeiter_traverse,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) nodeiter_iter,
  /* tp_iternext       */ (iternextfunc) nodeiter_next,
};

/** Module Setup & Teardown *******************************************/

int XsltElement_Init(PyObject *module)
{
  PyObject *dict;

  XmlString_IMPORT;

  /* Initialize type object */
  XsltElement_Type.tp_base = &XsltNode_Type;
  if (PyType_Ready(&XsltElement_Type) < 0)
    return -1;

  /* Grrrr...MingW32 gcc doesn't support assigning imported functions in a
   * static structure.  This sucks because both gcc/Unix and MSVC both support
   * that.
   */
  NodeIter_Type.tp_getattro = PyObject_GenericGetAttr;
  if (PyType_Ready(&NodeIter_Type) < 0)
    return -1;

  if (PyModule_AddObject(module, "xslt_element", (PyObject*)&XsltElement_Type))
    return -1;

  /* Assign "class" constants */
  dict = XsltElement_Type.tp_dict;
  if (PyDict_SetItemString(dict, "attribute_types", Py_None)) return -1;
  if (PyDict_SetItemString(dict, "content_model", Py_None)) return -1;

  /* Pre-build frequently used values */
  namespaces_string = PyString_FromString("namespaces");
  if (namespaces_string == NULL) return -1;

  instruction_string = PyString_FromString("instruction");
  if (instruction_string == NULL) return -1;

  instantiate_string = PyString_FromString("instantiate");
  if (instantiate_string == NULL) return -1;

  dict = PyDict_New();
  if (dict == NULL) return -1;
  empty_dict = PyDictProxy_New(dict);
  Py_DECREF(dict);
  if (empty_dict == NULL) return -1;

  return 0;
}

void XsltElement_Fini(void)
{
  Py_DECREF(empty_dict);
  Py_DECREF(namespaces_string);
  Py_DECREF(instruction_string);
  Py_DECREF(instantiate_string);
  PyDict_Clear(XsltElement_Type.tp_dict);
}
