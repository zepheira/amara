#include "xslt_node.h"
#include "xslt_root.h"
#include "xslt_element.h"

static PyObject *setup_string;
static PyObject *does_setup_string;
static PyObject *validate_string;
static PyObject *does_validate_string;
static PyObject *prime_string;
static PyObject *does_prime_string;
static PyObject *teardown_string;
static PyObject *does_teardown_string;
static PyObject *empty_tuple;
static PyObject *newobj_function;

/** Private Routines **************************************************/

static int node_pretty_print(XsltNodeObject *self, int level)
{
  PyObject *str;
  Py_ssize_t i, size;
  XsltNodeObject *child;

  str = PyObject_Str((PyObject *) self);
  if (str == NULL) return -1;
  PySys_WriteStdout("%*s%s\n", level, "", PyString_AsString(str));
  Py_DECREF(str);

  /* Process the children */
  level += 2;
  if (XsltRoot_Check(self)) {
    child = (XsltNodeObject *) XsltRoot_STYLESHEET(self);
    return node_pretty_print(child, level);
  }
  else if (XsltElement_Check(self)){
    size = XsltElement_GET_COUNT(self);
    for (i = 0; i < size; i++) {
      XsltNodeObject *child = XsltElement_GET_CHILD(self, i);
      if (node_pretty_print(child, level) == -1) {
        return -1;
      }
    }
  }

  return 0;
}

/** Public C API ******************************************************/

XsltNodeObject *XsltNode_New(PyTypeObject *type)
{
  XsltNodeObject *self;

  self = (XsltNodeObject *)type->tp_alloc(type, 0);
  if (self != NULL) {
    Py_INCREF(Py_None);
    self->parent = Py_None;
    Py_INCREF(Py_None);
    self->root = Py_None;
  }
  return self;
}

int XsltNode_PrettyPrint(XsltNodeObject *self)
{
  if (!XsltNode_Check(self)) {
    PyErr_BadInternalCall();
    return -1;
  }
  return node_pretty_print(self, 0);
}

int XsltNode_Link(XsltNodeObject *self, XsltNodeObject *child)
{
  PyObject *temp, *callable;
  PyObject *root = XsltNode_ROOT(self);
  struct { PyObject *attribute; PyObject *instructions; }
    *table, update_table[] = {
      { does_validate_string, XsltRoot_VALIDATE_INSTRUCTIONS(root) },
      { does_prime_string, XsltRoot_PRIME_INSTRUCTIONS(root) },
      { does_teardown_string, XsltRoot_TEARDOWN_INSTRUCTIONS(root) },
      { NULL }
    };

  /* Set its parent link */
  temp = child->parent;
  Py_INCREF((PyObject *)self);
  child->parent = (PyObject *)self;
  Py_DECREF(temp);

  /* if the child does setup, call that function now */
  temp = PyObject_GetAttr((PyObject *)child, does_setup_string);
  if (temp == NULL)
    return -1;
  switch (PyObject_IsTrue(temp)) {
  case 1:
    Py_DECREF(temp);
    callable = PyObject_GetAttr((PyObject *)child, setup_string);
    if (callable == NULL)
      return -1;
    temp = PyObject_Call(callable, empty_tuple, NULL);
    Py_DECREF(callable);
    if (temp == NULL)
      return -1;
  case 0:
    Py_DECREF(temp);
    break;
  default:
    Py_DECREF(temp);
    return -1;
  }

  /* update the root-node instruction lists */
  for (table = update_table; table->attribute; table++) {
    /* if the child does setup, call that function now */
    temp = PyObject_GetAttr((PyObject *)child, table->attribute);
    if (temp == NULL)
      return -1;
    switch (PyObject_IsTrue(temp)) {
    case 1:
      /* FIXME: use weakrefs */
      if (PyList_Append(table->instructions, (PyObject *)child) < 0) {
        Py_DECREF(temp);
        return -1;
      }
    case 0:
      Py_DECREF(temp);
      break;
    default:
      Py_DECREF(temp);
      return -1;
    }
  }

  return 0;
}

/** Python Methods *****************************************************/

static char isLastChild_doc[] = "\
isLastChild() -> boolean\n\
\n\
Returns whether this node is the last child of its parent.";

static PyObject *node_isLastChild(PyObject *self, PyObject *args)
{
  PyObject *parent, *result;

  if (!PyArg_ParseTuple(args, ":isLastChild"))
    return NULL;

  /* Get the children list of the parent */
  parent = XsltNode_GET_PARENT(self);
  if (XsltRoot_Check(parent)) {
    result = (self == XsltRoot_STYLESHEET(parent)) ? Py_True : Py_False;
  }
  else if (XsltElement_Check(parent)) {
    Py_ssize_t i, count = XsltElement_GET_COUNT(parent);
    result = Py_False;
    for (i = 0; i < count; i++) {
      PyObject *sibling;
      sibling = (PyObject *) XsltElement_GET_CHILD(parent, i);
      if (self == sibling)
        result = Py_True;
      else if (result == Py_True) {
        PyObject *pseudo_node = PyObject_GetAttrString(sibling, "pseudo_node");
        if (pseudo_node == NULL)
          return NULL;
        switch (PyObject_IsTrue(pseudo_node)) {
        case 0:
          Py_DECREF(pseudo_node);
          Py_RETURN_FALSE;
        case 1:
          Py_DECREF(pseudo_node);
          break;
        default:
          Py_DECREF(pseudo_node);
          return NULL;
        }
      }
    }
  }
  else {
    /* no parent */
    result = Py_True;
  }

  Py_INCREF(result);
  return result;
}

static char setup_doc[] = "\
setup()\n\
\n\
Subclasses can override this method to perform any specific initialization\n\
that does not require a context node.";

static PyObject *node_setup(PyObject *self, PyObject *args)
{
  if (!PyArg_ParseTuple(args, ":setup"))
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char prime_doc[] = "\
prime(context)\n\
\n\
Subclasses can override this method to perform any specific initialization\n\
that requires a context node.";

static PyObject *node_prime(PyObject *self, PyObject *args)
{
  PyObject *context;

  if (!PyArg_ParseTuple(args, "O:prime", &context))
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char teardown_doc[] = "\
teardown()\n\
\n\
Subclasses can override this method to perform any teardown after a\n\
transform has been completed.";

static PyObject *node_teardown(PyObject *self, PyObject *args)
{
  if (!PyArg_ParseTuple(args, ":teardown"))
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char instantiate_doc[] = "\
instantiate(context)\n\
\n\
Subclasses can override this method to do the actual transformation\n\
processing.";

static PyObject *node_instantiate(PyObject *self, PyObject *args)
{
  PyObject *context;

  if (!PyArg_ParseTuple(args, "O:instantiate", &context))
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char pprint_doc[] = "\
pprint()\n\
\n\
Prints an indented instance representation of the stylesheet tree.";

static PyObject *node_pprint(PyObject *self, PyObject *args)
{
  if (!PyArg_ParseTuple(args, ":pprint"))
    return NULL;

  if (node_pretty_print((XsltNodeObject *) self, 0) == -1) {
    return NULL;
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static char reduce_doc[] = "helper for pickle protocols 0 and 1";

static PyObject *node_reduce(PyObject *self, PyObject *args)
{
  PyObject *cls, *getstate, *state;

  if (!PyArg_ParseTuple(args, ":__reduce__"))
    return NULL;

  cls = PyObject_GetAttrString(self, "__class__");
  if (cls == NULL)
    return NULL;

  args = PyTuple_New(1);
  if (args == NULL) {
    Py_DECREF(cls);
    return NULL;
  }
  PyTuple_SET_ITEM(args, 0, cls);

  getstate = PyObject_GetAttrString(self, "__getstate__");
  if (getstate == NULL) {
    PyErr_Clear();
    state = PyObject_GetAttrString(self, "__dict__");
    if (state == NULL) {
      PyErr_Clear();
      state = Py_None;
      Py_INCREF(state);
    }
  } else {
    state = PyObject_CallObject(getstate, NULL);
    Py_DECREF(getstate);
    if (state == NULL) {
      Py_DECREF(args);
      return NULL;
    }
  }

  return Py_BuildValue("(ONN)", newobj_function, args, state);
}

#define XsltNode_METHOD(NAME)                                   \
  { #NAME, (PyCFunction) node_##NAME, METH_VARARGS, NAME##_doc }

static struct PyMethodDef node_methods[] = {
  XsltNode_METHOD(isLastChild),

  XsltNode_METHOD(setup),
  XsltNode_METHOD(prime),
  XsltNode_METHOD(teardown),
  XsltNode_METHOD(instantiate),

  XsltNode_METHOD(pprint),

  { "__reduce__", node_reduce, METH_VARARGS, reduce_doc },
  { NULL }
};

/** Python Members ****************************************************/

static struct PyMemberDef node_members[] = {
  { "root",         T_OBJECT, offsetof(XsltNodeObject, root),         RO },
  { "parent",       T_OBJECT, offsetof(XsltNodeObject, parent),       RO },
  { NULL }
};

/** Python Computed Members ********************************************/

static PyObject *get_base_uri(XsltNodeObject *self, void *arg)
{
  PyObject *parent, *base;

  /* baseURI is calculated according to XML Base */
  parent = self->parent;
  if (XsltElement_Check(parent))
    base = XsltElement_BASE_URI(parent);
  else if (XsltRoot_Check(parent))
    base = XsltRoot_BASE_URI(parent);
  else
    /* Node does not yet have a parent */
    base = Py_None;

  Py_INCREF(base);
  return base;
}

static struct PyGetSetDef node_getset[] = {
  { "baseUri",    (getter)get_base_uri },
  { "base_uri",    (getter)get_base_uri },
  { NULL }
};

/** Type Object ********************************************************/

static PyObject *node_repr(XsltNodeObject *self)
{
  PyObject *name, *repr;

  name = PyObject_GetAttrString((PyObject *)self->ob_type, "__name__");
  if (name == NULL)
    return NULL;
  repr = PyString_FromFormat("<%s at %p>", PyString_AsString(name), self);
  Py_DECREF(name);
  return repr;
}

static int node_traverse(XsltNodeObject *self, visitproc visit, void *arg)
{
  Py_VISIT(self->parent);
  Py_VISIT(self->root);
  return 0;
}

static int node_clear(XsltNodeObject *self)
{
  Py_CLEAR(self->parent);
  Py_CLEAR(self->root);
  return 0;
}

static void node_dealloc(XsltNodeObject *self)
{
  Py_XDECREF(self->parent);
  Py_XDECREF(self->root);
  self->ob_type->tp_free((PyObject *) self);
}

static int node_init(XsltNodeObject *self, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = { "root", NULL };
  PyObject *root, *temp;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O!:XsltNode", kwlist,
                                   &XsltRoot_Type, &root))
    return -1;

  temp = self->root;
  Py_INCREF(root);
  self->root = root;
  Py_DECREF(temp);

  return 0;
}

static PyObject *node_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  return (PyObject *) XsltNode_New(type);
}

static char node_doc[] = "\
The xslt_node type is the primary datatype for the entire stylesheet model.";

PyTypeObject XsltNode_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "amara.xslt.tree.xslt_node",
  /* tp_basicsize      */ sizeof(XsltNodeObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) node_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) node_repr,
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
  /* tp_doc            */ (char *) node_doc,
  /* tp_traverse       */ (traverseproc) node_traverse,
  /* tp_clear          */ (inquiry) node_clear,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) node_methods,
  /* tp_members        */ (PyMemberDef *) node_members,
  /* tp_getset         */ (PyGetSetDef *) node_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) node_init,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) node_new,
  /* tp_free           */ 0,
};


static PyObject *
metaclass_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = { "name", "bases", "dict", NULL };
  PyObject *name, *bases, *dict;
  struct { PyObject *function; PyObject *attribute; }
    *table, lookup_table[] = {
      { setup_string, does_setup_string },
      { validate_string, does_validate_string },
      { prime_string, does_prime_string },
      { teardown_string, does_teardown_string },
      { NULL }
    };

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "SOO:__metaclass__", kwlist,
                                   &name, &bases, &dict))
    return NULL;

  /* update the function lookup attribues */
  for (table = lookup_table; table->function; table++) {
    /* if the child does setup, call that function now */
    if (PyDict_GetItem(dict, table->function) != NULL) {
      if (PyDict_SetItem(dict, table->attribute, Py_True) < 0)
        return NULL;
    }
  }

  return type->tp_base->tp_new(type, args, kwds);
}

static int
metaclass_init(PyObject *cls, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = { "name", "bases", "dict", NULL };
  PyObject *name, *bases, *dict;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "SOO:__metaclass__", kwlist,
                                   &name, &bases, &dict))
    return -1;

  return 0;
}

PyTypeObject xslt_metaclass = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "amara.xslt.tree.xslt_node.__metaclass__",
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
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT |
                           Py_TPFLAGS_BASETYPE |
                           0),
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
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) metaclass_init,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) metaclass_new,
  /* tp_free           */ 0,
};

/** Module Setup & Teardown *******************************************/


int XsltNode_Init(PyObject *module)
{
  PyObject *dict, *constant;

  /* Initialize constants */
  setup_string = PyString_FromString("setup");
  if (setup_string == NULL) return -1;
  does_setup_string = PyString_FromString("does_setup");
  if (does_setup_string == NULL) return -1;
  validate_string = PyString_FromString("validate");
  if (validate_string == NULL) return -1;
  does_validate_string = PyString_FromString("does_validate");
  if (does_validate_string == NULL) return -1;
  prime_string = PyString_FromString("prime");
  if (prime_string == NULL) return -1;
  does_prime_string = PyString_FromString("does_prime");
  if (does_prime_string == NULL) return -1;
  teardown_string = PyString_FromString("teardown");
  if (teardown_string == NULL) return -1;
  does_teardown_string = PyString_FromString("does_teardown");
  if (does_teardown_string == NULL) return -1;

  empty_tuple = PyTuple_New(0);
  if (empty_tuple == NULL) return -1;

  newobj_function = PyObject_GetAttrString(module, "__newobj__");
  if (newobj_function == NULL) return -1;

  /* Initialize type objects */
  xslt_metaclass.tp_base = &PyType_Type;
  if (PyType_Ready(&xslt_metaclass) < 0)
    return -1;
  XsltNode_Type.ob_type = &xslt_metaclass;
  if (PyType_Ready(&XsltNode_Type) < 0)
    return -1;

  if (PyModule_AddObject(module, "xslt_node", (PyObject *) &XsltNode_Type))
    return -1;

  /* Assign "class" constants */
  dict = XsltNode_Type.tp_dict;
  if (PyDict_SetItem(dict, does_setup_string, Py_False)) return -1;
  if (PyDict_SetItem(dict, does_validate_string, Py_False)) return -1;
  if (PyDict_SetItem(dict, does_prime_string, Py_False)) return -1;
  if (PyDict_SetItem(dict, does_teardown_string, Py_False)) return -1;
  if (PyDict_SetItemString(dict, "nodeName", Py_None)) return -1;
  if (PyDict_SetItemString(dict, "children", Py_None)) return -1;
  if (PyDict_SetItemString(dict, "attributes", Py_None)) return -1;
  if (PyDict_SetItemString(dict, "namespaces", Py_None)) return -1;

  constant = Py_BuildValue("(OO)", Py_None, Py_None);
  if (constant == NULL) return -1;
  if (PyDict_SetItemString(dict, "expanded_name", constant)) return -1;
  Py_DECREF(constant);

  constant = PyString_FromString("?");
  if (constant == NULL) return -1;
  if (PyDict_SetItemString(dict, "lineNumber", constant)) return -1;
  if (PyDict_SetItemString(dict, "columnNumber", constant)) return -1;
  Py_DECREF(constant);

  constant = PyInt_FromLong(-1L);
  if (constant == NULL) return -1;
  if (PyDict_SetItemString(dict, "import_precedence", constant)) return -1;
  Py_DECREF(constant);

  if (PyDict_SetItemString(dict, "pseudo_node", Py_False)) return -1;

  if (PyDict_SetItemString(dict, "__metaclass__", (PyObject *)&xslt_metaclass))
    return -1;

  return 0;
}


void XsltNode_Fini(void)
{
  Py_DECREF(setup_string);
  Py_DECREF(does_setup_string);
  Py_DECREF(validate_string);
  Py_DECREF(does_validate_string);
  Py_DECREF(prime_string);
  Py_DECREF(does_prime_string);
  Py_DECREF(teardown_string);
  Py_DECREF(does_teardown_string);
  Py_DECREF(empty_tuple);
  Py_DECREF(newobj_function);
  PyDict_Clear(XsltNode_Type.tp_dict);
}
