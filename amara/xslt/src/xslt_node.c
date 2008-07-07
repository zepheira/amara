#include "xslt_node.h"
#include "xslt_root.h"
#include "xslt_element.h"

static PyObject *is_pseudo_node_string;
static PyObject *newobj_function;

/** Private Routines **************************************************/

static int node_pretty_print(XsltNodeObject *self, int level)
{
  PyObject *str;
  int i, size;
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

  self = (XsltNodeObject *) type->tp_alloc(type, 0);
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
    int i, count = XsltElement_GET_COUNT(parent);
    result = Py_False;
    for (i = 0; i < count; i++) {
      PyObject *sibling, *temp;
      sibling = (PyObject *) XsltElement_GET_CHILD(parent, i);
      if (self == sibling)
        result = Py_True;
      else if (result == Py_True) {
        int is_pseudo_node;
        temp = PyObject_GetAttr(sibling, is_pseudo_node_string);
        if (temp == NULL)
          return NULL;
        is_pseudo_node = PyObject_IsTrue(temp);
        Py_DECREF(temp);
        if (is_pseudo_node == 0) {
          result = Py_False;
          break;
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
prime(processor, context)\n\
\n\
Subclasses can override this method to perform any specific initialization\n\
that requires a context node.";

static PyObject *node_prime(PyObject *self, PyObject *args)
{
  PyObject *processor, *context;

  if (!PyArg_ParseTuple(args, "OO:prime", &processor, &context))
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char idle_doc[] = "\
idle(processor)\n\
\n\
Subclasses can override this method to perform any teardown after a\n\
transform has been completed.";

static PyObject *node_idle(PyObject *self, PyObject *args)
{
  PyObject *processor;

  if (!PyArg_ParseTuple(args, "O:idle", &processor))
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char instantiate_doc[] = "\
instantiate(context, processor)\n\
\n\
Subclasses can override this method to do the actual transformation\n\
processing.";

static PyObject *node_instantiate(PyObject *self, PyObject *args)
{
  PyObject *context, *processor;

  if (!PyArg_ParseTuple(args, "OO:instantiate", &context, &processor))
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
  XsltNode_METHOD(idle),
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
  { NULL }
};

/** Type Object ********************************************************/

static PyObject *node_repr(XsltNodeObject *self)
{
  PyObject *name, *repr;

  name = PyObject_GetAttrString((PyObject *)self->ob_type, "__name__");
  if (name == NULL) {
    return NULL;
  }

  repr = PyString_FromFormat("<%s at %p>", PyString_AsString(name), self);
  Py_DECREF(name);

  return repr;
}


static int node_traverse(XsltNodeObject *self, visitproc visit, void *arg)
{
  int rt;

  if (self->parent != NULL) {
    rt = visit(self->parent, arg);
    if (rt) return rt;
  }

  if (self->root != NULL) {
    rt = visit(self->root, arg);
    if (rt) return rt;
  }
  return 0;
}


static int node_clear(XsltNodeObject *self)
{
  PyObject *tmp;

  if (self->parent != NULL) {
    tmp = self->parent;
    self->parent = NULL;
    Py_DECREF(tmp);
  }

  if (self->root != NULL) {
    tmp = self->root;
    self->root = NULL;
    Py_DECREF(tmp);
  }

  return 0;
}


static void node_dealloc(XsltNodeObject *self)
{
  node_clear(self);
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
The Node type is the primary datatype for the entire Stylesheet Model.";

PyTypeObject XsltNode_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "Ft.Xml.Xslt.cStylesheetTree.XsltNode",
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
  /* tp_alloc          */ (allocfunc) PyType_GenericAlloc,
  /* tp_new            */ (newfunc) node_new,
  /* tp_free           */ PyObject_GC_Del,
};


/** Module Setup & Teardown *******************************************/


int XsltNode_Init(PyObject *module)
{
  PyObject *dict, *constant;

  /* Initialize type object */
  if (PyType_Ready(&XsltNode_Type) < 0)
    return -1;

  if (PyModule_AddObject(module, "XsltNode", (PyObject *) &XsltNode_Type))
    return -1;

  /* Assign "class" constants */
  dict = XsltNode_Type.tp_dict;
  if (PyDict_SetItemString(dict, "nodeName", Py_None)) return -1;
  if (PyDict_SetItemString(dict, "children", Py_None)) return -1;
  if (PyDict_SetItemString(dict, "attributes", Py_None)) return -1;
  if (PyDict_SetItemString(dict, "namespaces", Py_None)) return -1;

  constant = Py_BuildValue("(OO)", Py_None, Py_None);
  if (constant == NULL) return -1;
  if (PyDict_SetItemString(dict, "expandedName", constant)) return -1;
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

  if (PyDict_SetItemString(dict, "isPseudoNode", Py_False)) return -1;

  is_pseudo_node_string = PyString_FromString("isPseudoNode");
  if (is_pseudo_node_string == NULL) return -1;

  newobj_function = PyObject_GetAttrString(module, "__newobj__");
  if (newobj_function == NULL) return -1;

  return 0;
}


void XsltNode_Fini(void)
{
  Py_DECREF(is_pseudo_node_string);
  Py_DECREF(newobj_function);
  PyDict_Clear(XsltNode_Type.tp_dict);
}
