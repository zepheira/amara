#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

static PyObject *creation_counter, *counter_inc;

Py_LOCAL_INLINE(int)
document_init(DocumentObject *self, PyObject *documentURI)
{
  PyObject *creationIndex, *unparsed_entities;

  if (documentURI == NULL || !XmlString_NullCheck(documentURI)) {
    PyErr_BadInternalCall();
    return -1;
  }

  creationIndex = PyNumber_Add(creation_counter, counter_inc);
  if (creationIndex == NULL) {
    return -1;
  }

  unparsed_entities = PyDict_New();
  if (unparsed_entities == NULL) {
    Py_DECREF(creationIndex);
    return -1;
  }

  if (documentURI == Py_None) {
    documentURI = PyUnicode_FromUnicode(NULL, (Py_ssize_t)0);
    if (documentURI == NULL) {
      Py_DECREF(creationIndex);
      Py_DECREF(unparsed_entities);
      return -1;
    }
  } else {
    Py_INCREF(documentURI);
  }

  self->creationIndex = creationIndex;
  self->unparsed_entities = unparsed_entities;
  Document_SET_DOCUMENT_URI(self, documentURI);
  Document_SET_PUBLIC_ID(self, Py_None);
  Py_INCREF(Py_None);
  Document_SET_SYSTEM_ID(self, Py_None);
  Py_INCREF(Py_None);

  /* update creation counter */
  Py_INCREF(creationIndex);
  Py_DECREF(creation_counter);
  creation_counter = creationIndex;

  return 0;
}

/* returns borrowed reference */
Py_LOCAL(PyObject *) /* not inlined as its recursive */
get_element_by_id(NodeObject *node, PyObject *elementId)
{
  int i;

  for (i = 0; i < ContainerNode_GET_COUNT(node); i++) {
    NodeObject *child = ContainerNode_GET_CHILD(node, i);
    if (Element_Check(child)) {
      PyObject *tmp, *attr;
      Py_ssize_t pos = 0;
      /* Searth the attributes for an ID attr */
      while (PyDict_Next(Element_GET_ATTRIBUTES(child), &pos, &tmp, &attr)) {
        if (Attr_GET_TYPE(attr) == ATTRIBUTE_TYPE_ID) {
          tmp = Attr_GET_NODE_VALUE(attr);
          switch (PyObject_RichCompareBool(tmp, elementId, Py_EQ)) {
          case 1:
            /* Found matching element, return it. */
            return (PyObject *) child;
          case 0:
            break;
          default:
            return NULL;
          }
        }
      }
      /* Continue on with the children */
      tmp = get_element_by_id(child, elementId);
      /* either NULL (an error) or a node (element found) */
      if (tmp != Py_None) return tmp;
    }
  }
  return Py_None;
}

/** Public C API ******************************************************/

DocumentObject *Document_New(PyObject *documentURI)
{
  DocumentObject *self;

  self = Node_NewContainer(DocumentObject, &DomletteDocument_Type);
  if (self != NULL) {
    if (document_init(self, documentURI) < 0) {
      Node_Del(self);
      return NULL;
    }
  }

  PyObject_GC_Track(self);

  return self;
}

/** Python Methods ****************************************************/

static char document_lookup_doc[] =
"xml_lookup(idref) -> Element\n\
\n\
Returns the Element whose ID is given by `idref`. If no such element\n\
exists, returns None. If more than one element has this ID, the first in\n\
the document is returned.";

static PyObject *document_lookup(PyObject *self, PyObject *args)
{
  PyObject *idref, *element;
  Py_ssize_t i;

  if (!PyArg_ParseTuple(args, "O:xml_lookup", &idref))
    return NULL;

  /* our "document" can have multiple element children */
  for (i = 0; i < ContainerNode_GET_COUNT(self); i++) {
    NodeObject *node = ContainerNode_GET_CHILD(self, i);
    if (Element_Check(node)) {
      element = get_element_by_id(node, idref);
      if (element == NULL) 
        return NULL;
      else if (element != Py_None) {
        Py_INCREF(element);
        return element;
      }
    }
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *entity_getnewargs(PyObject *self, PyObject *noarg)
{
  return PyTuple_Pack(1, Document_GET_DOCUMENT_URI(self));
}

static PyObject *entity_getstate(PyObject *self, PyObject *args)
{
  PyObject *deep=Py_True, *unparsed_entities, *children;

  if (!PyArg_ParseTuple(args, "|O:__getstate__", &deep))
    return NULL;

  switch (PyObject_IsTrue(deep)) {
    case 1:
      unparsed_entities = Document_GET_UNPARSED_ENTITIES(self);
      children = PyObject_GetAttrString(self, "xml_children");
      break;
    case 0:
      unparsed_entities = Py_None;
      Py_INCREF(Py_None);
      children = Py_None;
      break;
    default:
      return NULL;
  }
  return Py_BuildValue("OOON", 
                       Document_GET_PUBLIC_ID(self),
                       Document_GET_SYSTEM_ID(self),
                       unparsed_entities, children);
}

static PyObject *entity_setstate(PyObject *self, PyObject *state)
{
  PyObject *public_id, *system_id, *unparsed_entities, *children, *temp;

  if (!PyArg_ParseTuple(state, "OOOO", &public_id, &system_id,
                        &unparsed_entities, &children))
    return NULL;

  temp = Document_GET_PUBLIC_ID(self);
  Document_SET_PUBLIC_ID(self, public_id);
  Py_INCREF(public_id);
  Py_DECREF(temp);

  temp = Document_GET_SYSTEM_ID(self);
  Document_SET_SYSTEM_ID(self, system_id);
  Py_INCREF(system_id);
  Py_DECREF(temp);

  PyDict_Clear(Document_GET_UNPARSED_ENTITIES(self));
  if (unparsed_entities != Py_None)
    if (PyDict_Update(Document_GET_UNPARSED_ENTITIES(self), unparsed_entities))
      return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

#define Document_METHOD(name) \
  { "xml_" #name, document_##name, METH_VARARGS, document_##name##_doc }

static PyMethodDef document_methods[] = {
  Document_METHOD(lookup),
  { "__getnewargs__", entity_getnewargs, METH_NOARGS,  "helper for pickle" },
  { "__getstate__",   entity_getstate,   METH_VARARGS, "helper for pickle" },
  { "__setstate__",   entity_setstate,   METH_O,       "helper for pickle" },
  { NULL }
};

/** Python Members ****************************************************/

#define Document_MEMBER(name, member) \
  { name, T_OBJECT, offsetof(DocumentObject, member), RO }

static PyMemberDef document_members[] = {
  Document_MEMBER("xml_unparsed_entities", unparsed_entities),
  { NULL }
};

/** Python Computed Members *******************************************/

static PyObject *get_root(DocumentObject *self, void *arg)
{
  Py_INCREF(self);
  return (PyObject *)self;
}

static PyObject *get_public_id(DocumentObject *self, void *arg)
{
  Py_INCREF(self->publicId);
  return self->publicId;
}

static int set_public_id(DocumentObject *self, PyObject *v, void *arg)
{
  if ((v = XmlString_ConvertArgument(v, "xml_public_id", 1)) == NULL)
    return -1;
  Py_DECREF(self->publicId);
  self->publicId = v;
  return 0;
}

static PyObject *get_system_id(DocumentObject *self, void *arg)
{
  Py_INCREF(self->systemId);
  return self->systemId;
}

static int set_system_id(DocumentObject *self, PyObject *v, void *arg)
{
  if ((v = XmlString_ConvertArgument(v, "xml_system_id", 1)) == NULL)
    return -1;
  Py_DECREF(self->systemId);
  self->systemId = v;
  return 0;
}

static PyGetSetDef document_getset[] = {
  { "xml_root",      (getter)get_root },
  { "xml_public_id", (getter)get_public_id, (setter)set_public_id },
  { "xml_system_id", (getter)get_system_id, (setter)set_system_id },
  { NULL }
};

/** Type Object ********************************************************/

static void document_dealloc(DocumentObject *self)
{
  PyObject_GC_UnTrack((PyObject *) self);
  Py_CLEAR(self->documentURI);
  Py_CLEAR(self->publicId);
  Py_CLEAR(self->systemId);
  Py_CLEAR(self->unparsed_entities);
  Py_CLEAR(self->creationIndex);
  Node_Del(self);
}

static PyObject *document_repr(DocumentObject *self)
{
  return PyString_FromFormat("<Document at %p: "
                             "%" PY_FORMAT_SIZE_T "d children>",
                             self, ContainerNode_GET_COUNT(self));
}

static int document_traverse(DocumentObject *self, visitproc visit, void *arg)
{
  Py_VISIT(self->unparsed_entities);
  return DomletteNode_Type.tp_traverse((PyObject *)self, visit, arg);
}

static int document_clear(DocumentObject *self)
{
  Py_CLEAR(self->unparsed_entities);
  return DomletteNode_Type.tp_clear((PyObject *)self);
}

static PyObject *document_new(PyTypeObject *type, PyObject *args,
                              PyObject *kwds)
{
  PyObject *documentURI = Py_None;
  static char *kwlist[] = { "documentURI", NULL };
  DocumentObject *self;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O:Document", kwlist,
                                   &documentURI)) {
    return NULL;
  }

  documentURI = XmlString_ConvertArgument(documentURI, "documentURI", 1);
  if (documentURI == NULL) {
    return NULL;
  }

  if (type != &DomletteDocument_Type) {
    self = Document(type->tp_alloc(type, 0));
    if (self != NULL) {
      _Node_INIT_CONTAINER(self);
      if (document_init(self, documentURI) < 0) {
        Py_DECREF(self);
        self = NULL;
      }
    }
  } else {
    self = Document_New(documentURI);
  }
  Py_DECREF(documentURI);

  return (PyObject *) self;

}

static char document_doc[] = "\
Document([documentURI]) -> Document object\n\
\n\
The Document interface represents the entire XML document. Conceptually,\n\
it is the root of the document tree, and provides the primary access to the\n\
document's data.";

PyTypeObject DomletteDocument_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "Document",
  /* tp_basicsize      */ sizeof(DocumentObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) document_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) document_repr,
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
  /* tp_doc            */ (char *) document_doc,
  /* tp_traverse       */ (traverseproc) document_traverse,
  /* tp_clear          */ (inquiry) document_clear,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) document_methods,
  /* tp_members        */ (PyMemberDef *) document_members,
  /* tp_getset         */ (PyGetSetDef *) document_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) document_new,
  /* tp_free           */ 0,
};

/** Module Interface **************************************************/

int DomletteDocument_Init(PyObject *module)
{
  PyObject *dict, *value;

  DomletteDocument_Type.tp_base = &DomletteNode_Type;
  if (PyType_Ready(&DomletteDocument_Type) < 0)
    return -1;

  dict = DomletteDocument_Type.tp_dict;

  value = PyString_FromString("document");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_type", value))
    return -1;
  Py_DECREF(value);

  creation_counter = PyLong_FromLong(0L);
  if (creation_counter == NULL) return -1;

  counter_inc = PyLong_FromLong(1L);
  if (counter_inc == NULL) return -1;

  Py_INCREF(&DomletteDocument_Type);
  return PyModule_AddObject(module, "Document",
                            (PyObject*) &DomletteDocument_Type);
}

void DomletteDocument_Fini(void)
{
  Py_DECREF(creation_counter);
  Py_DECREF(counter_inc);

  PyType_CLEAR(&DomletteDocument_Type);
}
