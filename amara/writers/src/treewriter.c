/***********************************************************************
 * amara/writers/src/treewriter.c
 ***********************************************************************/

static char module_doc[] = "\
Result Tree Fragment writer for XSLT output\n\
";

#include "Python.h"
#include "structmember.h"

/* Backward compat code recommended in PEP 353 */
#if PY_VERSION_HEX < 0x02050000
    typedef int Py_ssize_t;
#endif

#include "domlette_interface.h"
#include "xmlstring.h"

#define MODULE_NAME "amara.writers.treewriter"
#define MODULE_INITFUNC inittreewriter

/* Round up n to be a multiple of sz, where sz is a power of 2. */
#define ROUND_UP(n, sz) (((n) + ((sz) - 1)) & ~((sz) - 1))

/* 8K buffer should be plenty for most documents (it does resize if needed) */
#define CDATA_BUFSIZ 8192

/* The number of items in the amara.writers.write.__slots__ member. */
#define TreeWriter_SLOTS 1

typedef struct {
  PyObject_HEAD
  PyObject *slots[TreeWriter_SLOTS];
  EntityObject *document;
  NodeObject *current_node;
  Py_UNICODE *buffer;
  Py_ssize_t buffer_size;
  Py_ssize_t buffer_allocated;
  int escape_output;
} TreeWriterObject;

/** Private Routines **************************************************/

static PyObject *writer_init;
static PyObject *xmlns_string;
static PyObject *xmlns_namespace;

static PyTypeObject UnescapedText_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".UnescapedText",
  /* tp_basicsize      */ sizeof(TextObject),
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
};

static TextObject *UnescapedText_New(PyObject *data)
{
  PyObject *self, *args;

  args = PyTuple_New(1);
  if (args == NULL) return NULL;
  Py_INCREF(data);
  PyTuple_SET_ITEM(args, 0, data);

  self = UnescapedText_Type.tp_new(&UnescapedText_Type, args, NULL);
  if (self != NULL) {
    if (UnescapedText_Type.tp_init(self, args, NULL) < 0) {
      Py_DECREF(self);
      self = NULL;
    }
  }
  Py_DECREF(args);
  return (TextObject *)self;
}

static int complete_text(TreeWriterObject *self)
{
  Py_ssize_t size = self->buffer_size;
  PyObject *data;
  TextObject *node;

  /* Mark buffer as empty. */
  assert(self->buffer_size > 0);
  self->buffer_size = 0;

  data = PyUnicode_FromUnicode(self->buffer, size);
  if (data == NULL) return -1;

  if (self->escape_output) {
    node = Text_New(data);
  } else {
    node = UnescapedText_New(data);
  }
  Py_DECREF(data);
  if (node == NULL) return -1;
  if (Container_Append(self->current_node, (NodeObject *)node) < 0) {
    Py_DECREF(node);
    return -1;
  }
  Py_DECREF(node);
  return 0;
}

/** Public C API ******************************************************/


/** Python Methods *****************************************************/

static PyObject *treewriter_get_result(TreeWriterObject *self,
                                       PyObject *noarg)
{
  if (self->current_node != NULL) {
    PyErr_SetString(PyExc_RuntimeError, "end_document not called");
    return NULL;
  }

  Py_INCREF(self->document);
  return (PyObject *)self->document;
}

static PyObject *treewriter_start_document(TreeWriterObject *self,
                                           PyObject *noarg)
{
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *treewriter_end_document(TreeWriterObject *self,
                                         PyObject *noarg)
{
  if (self->current_node == NULL) {
    PyErr_SetString(PyExc_RuntimeError, "end_document already called");
    return NULL;
  }
  if (self->buffer_size && complete_text(self) < 0) return NULL;
  if ((NodeObject *)self->document != self->current_node) {
    PyErr_SetString(PyExc_RuntimeError, "end_element not called");
    return NULL;
  }

  self->current_node = NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *treewriter_start_element(TreeWriterObject *self,
                                          PyObject *args, PyObject *kwds)
{
  PyObject *name, *namespace=Py_None, *namespaces=NULL, *attributes=NULL;
  PyObject *prefix, *localName;
  static char *kwlist[] = {
    "name", "namespace", "namespaces", "attributes", NULL };
  ElementObject *element;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOO:start_element", kwlist,
                                   &name, &namespace, &namespaces,
                                   &attributes)) {
    return NULL;
  }

  if (self->current_node == NULL) {
    PyErr_SetString(PyExc_RuntimeError, "end_document already called");
    return NULL;
  }

  if (self->buffer_size && complete_text(self) < 0) return NULL;

  if (namespaces && !PyDict_Check(namespaces)) {
    PyErr_SetString(PyExc_ValueError, "namespaces must be a dict or None");
    return NULL;
  }

  if (attributes && !PyDict_Check(attributes)) {
    PyErr_SetString(PyExc_ValueError, "attributes must be a dict or None");
    return NULL;
  }

  name = XmlString_ConvertArgument(name, "name", 0);
  if (name == NULL) {
    return NULL;
  }
  namespace = XmlString_ConvertArgument(namespace, "namespace", 1);
  if (namespace == NULL) {
    Py_DECREF(name);
    return NULL;
  }
  if (!XmlString_SplitQName(name, &prefix, &localName)) {
    Py_DECREF(name);
    Py_DECREF(namespace);
  }
  if (namespace == Py_None && prefix != Py_None) {
    PyErr_SetString(PyExc_ValueError, "prefix requires non-null namespace");
    Py_DECREF(name);
    Py_DECREF(namespace);
    Py_DECREF(prefix);
    return NULL;
  }
  Py_DECREF(prefix);

  /* Add the new element to the document. */
  element = Element_New(namespace, name, localName);
  Py_DECREF(name);
  Py_DECREF(namespace);
  Py_DECREF(localName);
  if (element == NULL) return NULL;
  if (Container_Append(self->current_node, (NodeObject *)element) < 0) {
    Py_DECREF(element);
    return NULL;
  }
  /* Let the parent own the reference to it. */
  Py_DECREF(element);

  /* Add the additional namespaces to the new element */
  if (namespaces) {
    Py_ssize_t i = 0;
    while (PyDict_Next(namespaces, &i, &prefix, &namespace)) {
      NamespaceObject *nsattr;
      nsattr = Element_AddNamespace(element, prefix, namespace);
      if (nsattr == NULL) 
        return NULL;
      Py_DECREF(nsattr);
    }
  }

  self->current_node = (NodeObject *) element;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *treewriter_end_element(TreeWriterObject *self,
                                        PyObject *args, PyObject *kwds)
{
  PyObject *name, *namespace=Py_None;
  static char *kwlist[] = { "name", "namespace", NULL };
  ElementObject *element = (ElementObject *)self->current_node;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O:end_element", kwlist,
                                   &name, &namespace)) {
    return NULL;
  }

  if (element == NULL) {
    PyErr_SetString(PyExc_RuntimeError, "end_document already called");
    return NULL;
  }

  if (self->buffer_size && complete_text(self) < 0) return NULL;

  name = XmlString_ConvertArgument(name, "name", 0);
  if (name == NULL) {
    return NULL;
  }
  namespace = XmlString_ConvertArgument(namespace, "namespace", 1);
  if (namespace == NULL) {
    Py_DECREF(name);
    return NULL;
  }

  switch (PyObject_RichCompareBool(Element_QNAME(element), name, Py_EQ)) {
  case 1:
    break;
  case 0:
    PyErr_SetString(PyExc_RuntimeError,
                    "qualifiedName mismatch for startElement/endElement");
    /* fall through */
  default:
    Py_DECREF(name);
    Py_DECREF(namespace);
    return NULL;
  }
  switch (PyObject_RichCompareBool(Element_NAMESPACE_URI(element),
                                   namespace, Py_EQ)) {
  case 1:
    break;
  case 0:
    PyErr_SetString(PyExc_RuntimeError,
                    "namespaceURI mismatch for startElement/endElement");
    /* fall through */
  default:
    Py_DECREF(name);
    Py_DECREF(namespace);
    return NULL;
  }
  Py_DECREF(name);
  Py_DECREF(namespace);

  self->current_node = Node_GET_PARENT(self->current_node);

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *treewriter_attribute(TreeWriterObject *self,
                                      PyObject *args, PyObject *kwds)
{
  PyObject *name, *value, *namespace=Py_None;
  static char *kwlist[] = { "name", "value", "namespace", NULL };

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|O:attribute", kwlist,
                                   &name, &value, &namespace)) {
    return NULL;
  }

  if (self->current_node == NULL) {
    PyErr_SetString(PyExc_RuntimeError, "end_document already called");
    return NULL;
  }

  /* From XSLT 1.0 Section 7.1.3 (we implement recovery here,
   * if processing gets this far):
   * - Adding an attribute to an element after children have been added
   *   to it; implementations may either signal the error or ignore the
   *   attribute.
   * - Adding an attribute to a node that is not an element;
   *   implementations may either signal the error or ignore the
   *   attribute. */
  if (Element_Check(self->current_node) &&
      Container_GET_COUNT(self->current_node) == 0) {
    PyObject *prefix, *localName;
    AttrObject *attr;

    name = XmlString_ConvertArgument(name, "name", 0);
    if (name == NULL) {
      return NULL;
    }
    value = XmlString_ConvertArgument(value, "value", 0);
    if (value == NULL) {
      Py_DECREF(name);
      return NULL;
    }
    namespace = XmlString_ConvertArgument(namespace, "namespace", 1);
    if (namespace == NULL) {
      Py_DECREF(name);
      Py_DECREF(value);
      return NULL;
    }
    if (!XmlString_SplitQName(name, &prefix, &localName)) {
      Py_DECREF(name);
      Py_DECREF(value);
      Py_DECREF(namespace);
    }
    if (namespace == Py_None && prefix != Py_None) {
      PyErr_SetString(PyExc_ValueError, "prefix requires non-null namespace");
      Py_DECREF(name);
      Py_DECREF(value);
      Py_DECREF(namespace);
      Py_DECREF(prefix);
      return NULL;
    }
    Py_DECREF(prefix);

    attr = Element_AddAttribute((ElementObject *)self->current_node,
                                namespace, name, localName, value);
    Py_DECREF(name);
    Py_DECREF(value);
    Py_DECREF(namespace);
    if (attr == NULL) return NULL;
    Py_DECREF(attr);
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *treewriter_text(TreeWriterObject *self, PyObject *args,
                                 PyObject *kwds)
{
  Py_UNICODE *buffer = self->buffer;
  Py_ssize_t size;
  int escape_output;
  PyObject *data, *disable_escaping=Py_False;
  static char *kwlist[] = { "data", "disable_escaping", NULL };

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O:text", kwlist,
                                   &data, &disable_escaping)) {
    return NULL;
  }

  if (self->current_node == NULL) {
    PyErr_SetString(PyExc_RuntimeError, "end_document already called");
    return NULL;
  }

  data = XmlString_ConvertArgument(data, "data", 0);
  if (data == NULL) return NULL;

  /* If there is nothing to write, return */
  if (PyUnicode_GET_SIZE(data) == 0) {
    Py_DECREF(data);
    Py_INCREF(Py_None);
    return Py_None;
  }

  /* If disable-output-escaping isn't the same as the previous text,
   * store the previous and start fresh. */
  escape_output = PyObject_Not(disable_escaping);
  if (escape_output != self->escape_output) {
    if (escape_output < 0 || (self->buffer_size && complete_text(self) < 0)) {
      Py_DECREF(data);
      return NULL;
    }
    self->escape_output = escape_output;
  }

  /* Grow the buffer if there isn't enough room for the new characters. */
  size = self->buffer_size + PyUnicode_GET_SIZE(data);
  if (size > self->buffer_allocated) {
    Py_ssize_t allocated = ROUND_UP(size, CDATA_BUFSIZ);
    if (PyMem_Resize(buffer, Py_UNICODE, allocated) == NULL) {
      PyErr_NoMemory();
      Py_DECREF(data);
      return NULL;
    }
    self->buffer = buffer;
    self->buffer_allocated = allocated;
  }
  buffer += self->buffer_size;

  /* store the new data */
  Py_UNICODE_COPY(buffer, PyUnicode_AS_UNICODE(data), PyUnicode_GET_SIZE(data));
  self->buffer_size = size;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *treewriter_processing_instruction(TreeWriterObject *self,
                                                   PyObject *args,
                                                   PyObject *kwds)
{
  PyObject *target, *data;
  static char *kwlist[] = { "target", "data", NULL };
  ProcessingInstructionObject *node;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "UU:processing_instruction",
                                   kwlist, &target, &data)) {
    return NULL;
  }

  if (self->current_node == NULL) {
    PyErr_SetString(PyExc_RuntimeError, "end_document already called");
    return NULL;
  }

  if (self->buffer_size && complete_text(self) < 0) {
    return NULL;
  }

  target = XmlString_ConvertArgument(target, "target", 0);
  if (target == NULL) return NULL;
  data = XmlString_ConvertArgument(data, "data", 0);
  if (data == NULL) {
    Py_DECREF(target);
    return NULL;
  }

  node = ProcessingInstruction_New(target, data);
  Py_DECREF(target);
  Py_DECREF(data);
  if (node == NULL) return NULL;
  if (Container_Append(self->current_node, (NodeObject *)node) < 0) {
    Py_DECREF(node);
    return NULL;
  }
  Py_DECREF(node);

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *treewriter_comment(TreeWriterObject *self, PyObject *args,
                                    PyObject *kwds)
{
  PyObject *data;
  static char *kwlist[] = { "data", NULL };
  CommentObject *node;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:comment", kwlist, &data)) {
    return NULL;
  }

  if (self->current_node == NULL) {
    PyErr_SetString(PyExc_RuntimeError, "end_document already called");
    return NULL;
  }

  if (self->buffer_size && complete_text(self) < 0) {
    Py_DECREF(data);
    return NULL;
  }

  data = XmlString_ConvertArgument(data, "data", 0);
  if (data == NULL) return NULL;

  node = Comment_New(data);
  Py_DECREF(data);
  if (node == NULL) return NULL;
  if (Container_Append(self->current_node, (NodeObject *)node) < 0) {
    Py_DECREF(node);
    return NULL;
  }
  Py_DECREF(node);

  Py_INCREF(Py_None);
  return Py_None;
}

#define TreeWriter_METHOD(NAME, ARGSPEC) \
  { #NAME, (PyCFunction) treewriter_##NAME, ARGSPEC, NULL }

static struct PyMethodDef treewriter_methods[] = {
  TreeWriter_METHOD(get_result, METH_NOARGS),
  TreeWriter_METHOD(start_document, METH_NOARGS),
  TreeWriter_METHOD(end_document, METH_NOARGS),
  TreeWriter_METHOD(start_element, METH_KEYWORDS),
  TreeWriter_METHOD(end_element, METH_KEYWORDS),
  TreeWriter_METHOD(attribute, METH_KEYWORDS),
  TreeWriter_METHOD(text, METH_KEYWORDS),
  TreeWriter_METHOD(processing_instruction, METH_KEYWORDS),
  TreeWriter_METHOD(comment, METH_KEYWORDS),
  { NULL }
};

/** Python Members ****************************************************/

static PyMemberDef treewriter_members[] = {
  { NULL }
};

/** Python Computed Members ********************************************/

static PyGetSetDef treewriter_getsets[] = {
  { NULL }
};

/** Type Object ********************************************************/

static void treewriter_dealloc(TreeWriterObject *self)
{
  Py_XDECREF(self->document);
  if (self->buffer) {
    PyMem_Free(self->buffer);
  }
  self->ob_type->tp_free((PyObject *)self);
}

static PyObject *
treewriter_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  return type->tp_alloc(type, 0);
}

static int
treewriter_init(TreeWriterObject *self, PyObject *args, PyObject *kwds)
{
  PyObject *result, *output_parameters, *base_uri;
  static char *kwlist[] = { "output_parameters", "base_uri", NULL };

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO:treewriter", kwlist,
                                   &output_parameters, &base_uri)) {
    return -1;
  }

  args = PyTuple_Pack(2, self, output_parameters);
  if (args == NULL)
    return -1;
  result = PyObject_Call(writer_init, args, NULL);
  Py_DECREF(args);
  if (result == NULL)
    return -1;
  Py_DECREF(result);

  self->buffer = PyMem_New(Py_UNICODE, CDATA_BUFSIZ);
  if (self->buffer == NULL) {
    PyErr_NoMemory();
    return -1;
  }
  self->buffer_size = 0;
  self->buffer_allocated = CDATA_BUFSIZ;

  base_uri = XmlString_ConvertArgument(base_uri, "base_uri", 1);
  if (base_uri == NULL)
    return -1;

  self->document = Entity_New(base_uri);
  Py_DECREF(base_uri);
  if (self->document == NULL)
    return -1;
  self->current_node = (NodeObject *)self->document;
  self->escape_output = 1;

  return 0;
}

static char treewriter_doc[] = "\
A special, simple writer for capturing result-tree fragments.";

static PyTypeObject TreeWriter_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".treewriter",
  /* tp_basicsize      */ sizeof(TreeWriterObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) treewriter_dealloc,
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
  /* tp_doc            */ (char *) treewriter_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) treewriter_methods,
  /* tp_members        */ (PyMemberDef *) treewriter_members,
  /* tp_getset         */ (PyGetSetDef *) treewriter_getsets,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) treewriter_init,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) treewriter_new,
  /* tp_free           */ 0,
};

/** Module Setup & Teardown *******************************************/

static PyMethodDef module_methods[] = {
  { NULL }
};

#define DEFINE_OBJECT(name, ob) \
  (name) = (ob);                \
  if ((name) == NULL) return
#define DEFINE_STRING(name, s) \
  DEFINE_OBJECT(name, PyString_FromString(s))
#define DEFINE_UNICODE(name, s) \
  DEFINE_OBJECT(name, PyUnicode_DecodeASCII((s), sizeof(s) - 1, NULL))

PyMODINIT_FUNC MODULE_INITFUNC(void)
{
  PyObject *module, *base, *dict;

  Domlette_IMPORT;
  XmlString_IMPORT;

  /* Get the `amara.writers.writer` class */
  module = PyImport_ImportModule("amara.writers");
  if (module == NULL)
    return;
  base = PyObject_GetAttrString(module, "writer");
  Py_DECREF(module);
  if (base == NULL)
    return;
  assert(PyObject_IsInstance(base, (PyObject *)&PyType_Type));
  TreeWriter_Type.tp_base = (PyTypeObject *)base;
  if (PyType_Ready(&TreeWriter_Type) < 0) {
    Py_DECREF(base);
    return;
  }
  /* Store the base class' __init__ method */
  writer_init = PyObject_GetAttrString(base, "__init__");
  if (writer_init == NULL)
    return;

  UnescapedText_Type.tp_base = Domlette->Text_Type;
  if (PyType_Ready(&UnescapedText_Type) < 0)
    return;
  if (PyDict_SetItemString(UnescapedText_Type.tp_dict,
                           "xsltOutputEscaping",
                           Py_False) < 0)
    return;

  module = Py_InitModule3(MODULE_NAME, module_methods, module_doc);
  if (module == NULL) return;
  dict = PyModule_GetDict(module);
  if (PyDict_SetItemString(dict, "treewriter", (PyObject *)&TreeWriter_Type))
    return;

  DEFINE_UNICODE(xmlns_string, "xmlns");
  DEFINE_UNICODE(xmlns_namespace, "http://www.w3.org/2000/xmlns/");
}
