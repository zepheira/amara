#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

static PyObject *creation_counter, *counter_inc;

Py_LOCAL_INLINE(EntityObject *)
entity_init(EntityObject *self, PyObject *documentURI)
{
  PyObject *creationIndex, *unparsed_entities;

  if (documentURI == NULL || !XmlString_NullCheck(documentURI)) {
    PyErr_BadInternalCall();
    Py_DECREF(self);
    return NULL;
  }

  creationIndex = PyNumber_Add(creation_counter, counter_inc);
  if (creationIndex == NULL) {
    Py_DECREF(self);
    return NULL;
  }

  unparsed_entities = PyDict_New();
  if (unparsed_entities == NULL) {
    Py_DECREF(creationIndex);
    Py_DECREF(self);
    return NULL;
  }

  if (documentURI == Py_None) {
    documentURI = PyUnicode_FromUnicode(NULL, 0);
    if (documentURI == NULL) {
      Py_DECREF(creationIndex);
      Py_DECREF(unparsed_entities);
      Py_DECREF(self);
      return NULL;
    }
  } else {
    Py_INCREF(documentURI);
  }

  self->creationIndex = creationIndex;
  self->unparsed_entities = unparsed_entities;
  Entity_SET_DOCUMENT_URI(self, documentURI);
  Entity_SET_PUBLIC_ID(self, Py_None);
  Py_INCREF(Py_None);
  Entity_SET_SYSTEM_ID(self, Py_None);
  Py_INCREF(Py_None);

  /* update creation counter */
  Py_INCREF(creationIndex);
  Py_DECREF(creation_counter);
  creation_counter = creationIndex;

  return self;
}

/* returns borrowed reference */
Py_LOCAL(PyObject *) /* not inlined as its recursive */
get_element_by_id(NodeObject *node, PyObject *elementId)
{
  PyObject *result;
  Py_ssize_t i;

  for (i = 0; i < Container_GET_COUNT(node); i++) {
    NodeObject *child = Container_GET_CHILD(node, i);
    if (Element_Check(child)) {
      /* Searth the attributes for an ID attr */
      PyObject *attributes = Element_ATTRIBUTES(child);
      if (attributes != NULL) {
        AttrObject *attr;
        Py_ssize_t pos = 0;
        while ((attr = AttributeMap_Next(attributes, &pos)) != NULL) {
          if (Attr_GET_TYPE(attr) == ATTRIBUTE_TYPE_ID) {
            switch (PyObject_RichCompareBool(Attr_GET_VALUE(attr),
                                             elementId, Py_EQ)) {
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
      }
      /* Continue on with the children */
      result = get_element_by_id(child, elementId);
      if (result != Py_None) 
        /* either NULL (an error) or a node (element found) */
        return result;
    }
  }
  return Py_None;
}

/** Public C API ******************************************************/

EntityObject *Entity_New(PyObject *documentURI)
{
  EntityObject *self;

  self = Container_New(EntityObject, &DomletteEntity_Type);
  if (self != NULL) {
    self = entity_init(self, documentURI);
  }
  return self;
}

/** Python Methods ****************************************************/

static char entity_lookup_doc[] =
"xml_lookup(idref) -> Element\n\
\n\
Returns the element whose ID is given by `idref`. If no such element\n\
exists, returns None. If more than one element has this ID, the first in\n\
the entity is returned.";

static PyObject *entity_lookup(PyObject *self, PyObject *args)
{
  PyObject *idref, *element;
  Py_ssize_t i;

  if (!PyArg_ParseTuple(args, "O:xml_lookup", &idref))
    return NULL;

  /* our "document" can have multiple element children */
  for (i = 0; i < Container_GET_COUNT(self); i++) {
    NodeObject *node = Container_GET_CHILD(self, i);
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
  return PyTuple_Pack(1, Entity_GET_DOCUMENT_URI(self));
}

static PyObject *entity_getstate(PyObject *self, PyObject *args)
{
  PyObject *deep=Py_True, *dict, *unparsed_entities, *children;
  Py_ssize_t i;

  if (!PyArg_ParseTuple(args, "|O:__getstate__", &deep))
    return NULL;

  if (PyType_HasFeature(self->ob_type, Py_TPFLAGS_HEAPTYPE)) {
    dict = PyObject_GetAttrString(self, "__dict__");
    if (dict == NULL)
      return NULL;
  } else {
    dict = Py_None;
    Py_INCREF(Py_None);
  }
  /* save the child nodes in a tuple */
  switch (PyObject_IsTrue(deep)) {
    case 0:
      unparsed_entities = Py_None;
      children = Py_None;
      Py_INCREF(children);
      break;
    case 1:
      unparsed_entities = Entity_GET_UNPARSED_ENTITIES(self);
      children = PyTuple_New(Container_GET_COUNT(self));
      if (children != NULL) {
        for (i = 0; i < Container_GET_COUNT(self); i++) {
          PyObject *item = (PyObject *)Container_GET_CHILD(self, i);
          PyTuple_SET_ITEM(children, i, item);
          Py_INCREF(item);
        }
        break;
      }
      /* error; fall through */
    default:
      Py_DECREF(dict);
      return NULL;
  }
  return Py_BuildValue("NOOON", dict, Entity_GET_PUBLIC_ID(self),
                       Entity_GET_SYSTEM_ID(self), unparsed_entities,
                       children);
}

Py_LOCAL_INLINE(int)
convert_arg(int item, PyTypeObject *type, PyObject **arg)
{
  PyObject *obj = *arg;
  if (obj->ob_type == type)
    return 1;
  if (obj == Py_None) {
    *arg = NULL;
    return 1;
  }
  PyErr_Format(PyExc_TypeError,
               "__setstate__() argument 1, item %d must be %s, not %s",
               item, type->tp_name, obj->ob_type->tp_name);
  return 0;
}

static PyObject *entity_setstate(PyObject *self, PyObject *state)
{
  PyObject *dict, *public_id, *system_id, *unparsed_entities, *children, *temp;
  Py_ssize_t i, n;

  if (!PyArg_UnpackTuple(state, NULL, 5, 5,
                         &dict, &public_id, &system_id, &unparsed_entities,
                         &children))
    return NULL;

  if (!convert_arg(0, &PyDict_Type, &dict))
    return NULL;
  if (!convert_arg(3, &PyDict_Type, &unparsed_entities))
    return NULL;
  if (!convert_arg(4, &PyTuple_Type, &children))
    return NULL;

  if (dict) {
    if (PyType_HasFeature(self->ob_type, Py_TPFLAGS_HEAPTYPE)) {
      temp = PyObject_GetAttrString(self, "__dict__");
      if (temp == NULL)
        return NULL;
      if (PyDict_Update(temp, dict) < 0) {
        Py_DECREF(temp);
        return NULL;
      }
      Py_DECREF(temp);
    }
  }
  temp = Entity_GET_PUBLIC_ID(self);
  Entity_SET_PUBLIC_ID(self, public_id);
  Py_INCREF(public_id);
  Py_DECREF(temp);

  temp = Entity_GET_SYSTEM_ID(self);
  Entity_SET_SYSTEM_ID(self, system_id);
  Py_INCREF(system_id);
  Py_DECREF(temp);

  if (unparsed_entities) {
    temp = Entity_GET_UNPARSED_ENTITIES(self);
    PyDict_Clear(temp);
    if (PyDict_Update(temp, unparsed_entities) < 0)
      return NULL;
  }
  if (children) {
    for (i = 0, n = PyTuple_GET_SIZE(children); i < n; i++) {
      NodeObject *node = (NodeObject *)PyTuple_GET_ITEM(children, i);
      if (Container_Append((NodeObject *)self, node) < 0)
        return NULL;
    }
  }
  Py_RETURN_NONE;
}

#define Entity_METHOD(name) \
  { "xml_" #name, entity_##name, METH_VARARGS, entity_##name##_doc }

static PyMethodDef entity_methods[] = {
  Entity_METHOD(lookup),
  { "__getnewargs__", entity_getnewargs, METH_NOARGS,  "helper for pickle" },
  { "__getstate__",   entity_getstate,   METH_VARARGS, "helper for pickle" },
  { "__setstate__",   entity_setstate,   METH_O,       "helper for pickle" },
  { NULL }
};

/** Python Members ****************************************************/

#define Entity_MEMBER(name, member) \
  { name, T_OBJECT, offsetof(EntityObject, member), RO }

static PyMemberDef entity_members[] = {
  Entity_MEMBER("xml_unparsed_entities", unparsed_entities),
  { NULL }
};

/** Python Computed Members *******************************************/

static PyObject *get_root(EntityObject *self, void *arg)
{
  Py_INCREF(self);
  return (PyObject *)self;
}

static PyObject *get_public_id(EntityObject *self, void *arg)
{
  Py_INCREF(self->publicId);
  return self->publicId;
}

static int set_public_id(EntityObject *self, PyObject *v, void *arg)
{
  if ((v = XmlString_ConvertArgument(v, "xml_public_id", 1)) == NULL)
    return -1;
  Py_DECREF(self->publicId);
  self->publicId = v;
  return 0;
}

static PyObject *get_system_id(EntityObject *self, void *arg)
{
  Py_INCREF(self->systemId);
  return self->systemId;
}

static int set_system_id(EntityObject *self, PyObject *v, void *arg)
{
  if ((v = XmlString_ConvertArgument(v, "xml_system_id", 1)) == NULL)
    return -1;
  Py_DECREF(self->systemId);
  self->systemId = v;
  return 0;
}

static PyGetSetDef entity_getset[] = {
  { "xml_root",      (getter)get_root },
  { "xml_public_id", (getter)get_public_id, (setter)set_public_id },
  { "xml_system_id", (getter)get_system_id, (setter)set_system_id },
  { NULL }
};

/** Type Object ********************************************************/

static void entity_dealloc(EntityObject *self)
{
  PyObject_GC_UnTrack((PyObject *) self);
  Py_CLEAR(self->documentURI);
  Py_CLEAR(self->publicId);
  Py_CLEAR(self->systemId);
  Py_CLEAR(self->unparsed_entities);
  Py_CLEAR(self->creationIndex);
  Node_Del(self);
}

static PyObject *entity_repr(EntityObject *self)
{
  return PyString_FromFormat("<entity at %p: %zd children>",
                             self, Container_GET_COUNT(self));
}

static int entity_traverse(EntityObject *self, visitproc visit, void *arg)
{
  Py_VISIT(self->unparsed_entities);
  return DomletteContainer_Type.tp_traverse((PyObject *)self, visit, arg);
}

static int entity_clear(EntityObject *self)
{
  Py_CLEAR(self->unparsed_entities);
  return DomletteContainer_Type.tp_clear((PyObject *)self);
}

static PyObject *entity_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  PyObject *documentURI = Py_None;
  static char *kwlist[] = { "documentURI", NULL };
  EntityObject *self;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O:entity", kwlist,
                                   &documentURI)) {
    return NULL;
  }

  documentURI = XmlString_ConvertArgument(documentURI, "documentURI", 1);
  if (documentURI == NULL) {
    return NULL;
  }

  if (type != &DomletteEntity_Type) {
    self = Entity(type->tp_alloc(type, 0));
    if (self != NULL) {
      self = entity_init(self, documentURI);
    }
  } else {
    self = Entity_New(documentURI);
  }
  Py_DECREF(documentURI);

  return (PyObject *) self;

}

static char entity_doc[] = "\
entity([documentURI]) -> entity object\n\
\n\
The `entity` interface represents an entire XML document. Conceptually,\n\
it is the root of the document tree, and provides the primary access to the\n\
document's data.";

PyTypeObject DomletteEntity_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "entity",
  /* tp_basicsize      */ sizeof(EntityObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) entity_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) entity_repr,
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
  /* tp_doc            */ (char *) entity_doc,
  /* tp_traverse       */ (traverseproc) entity_traverse,
  /* tp_clear          */ (inquiry) entity_clear,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) entity_methods,
  /* tp_members        */ (PyMemberDef *) entity_members,
  /* tp_getset         */ (PyGetSetDef *) entity_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) entity_new,
  /* tp_free           */ 0,
};

/** Module Interface **************************************************/

int DomletteEntity_Init(PyObject *module)
{
  PyObject *dict, *value;

  DomletteEntity_Type.tp_base = &DomletteContainer_Type;
  if (PyType_Ready(&DomletteEntity_Type) < 0)
    return -1;

  dict = DomletteEntity_Type.tp_dict;

  value = PyString_FromString("document");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_type", value))
    return -1;
  Py_DECREF(value);
  /* add the "typecode" character for use with `xml_nodeid` */
  value = PyString_FromString("r");
  if (value == NULL)
    return -1;
  if (PyDict_SetItemString(dict, "xml_typecode", value) < 0)
    return -1;
  Py_DECREF(value);
  value = (PyObject *)&DomletteElement_Type;
  if (PyDict_SetItemString(dict, "xml_element_factory", value))
    return -1;
  value = (PyObject *)&DomletteText_Type;
  if (PyDict_SetItemString(dict, "xml_text_factory", value))
    return -1;
  value = (PyObject *)&DomletteProcessingInstruction_Type;
  if (PyDict_SetItemString(dict, "xml_processing_instruction_factory", value))
    return -1;
  value = (PyObject *)&DomletteComment_Type;
  if (PyDict_SetItemString(dict, "xml_comment_factory", value))
    return -1;

  creation_counter = PyLong_FromLong(0L);
  if (creation_counter == NULL) return -1;

  counter_inc = PyLong_FromLong(1L);
  if (counter_inc == NULL) return -1;

  Py_INCREF(&DomletteEntity_Type);
  return PyModule_AddObject(module, "entity",
                            (PyObject*) &DomletteEntity_Type);
}

void DomletteEntity_Fini(void)
{
  Py_DECREF(creation_counter);
  Py_DECREF(counter_inc);

  PyType_CLEAR(&DomletteEntity_Type);
}
