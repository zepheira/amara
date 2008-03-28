#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Private Routines **************************************************/

PyObject *g_implementation;

/** Public C API ******************************************************/

/* nothing to see here */

/** Python Methods ****************************************************/

static char domimp_hasFeature_doc[] = "\
Test if the DOM implementation implements a specific feature.";

static PyObject *domimp_hasFeature(PyObject *self, PyObject *args)
{
  char *feature;
  char *version;
  PyObject *res;

  if (!PyArg_ParseTuple(args,"ss:hasFeature", &feature, &version))
    return NULL;

  if (strcasecmp(feature, "core") ) {
    res = Py_False;
  }
  else if (strcmp(version, "2.0")) {
    res = Py_False;
  } else {
    res = Py_True;
  }

  Py_INCREF(res);
  return res;
}

static char domimp_createDocument_doc[] = "\
Creates a Document object of the specified type with its document element.";

static PyObject *domimp_createDocument(PyObject *self, PyObject *args)
{
  PyObject *namespaceURI, *doctype, *qualifiedName, *documentURI=Py_None;
  DocumentObject *doc;

  if (!PyArg_ParseTuple(args,"OOO|O:createDocument",
                        &namespaceURI, &qualifiedName, &doctype, &documentURI))
    return NULL;

  /* validate the arguments */
  /*
See: http://lists.fourthought.com/pipermail/4suite-dev/2003-August/001484.html
 - if the qname arg is None, don't check namespace arg
 - else:
    - if the namespace arg is a non-empty Unicode string, OK
    - else if the namespace arg is EMPTY_NAMESPACE (None), OK
    - else complain
   */

  namespaceURI = XmlString_ConvertArgument(namespaceURI, "namespaceURI", 1);
  if (namespaceURI == NULL) {
    return NULL;
  }

  qualifiedName = XmlString_ConvertArgument(qualifiedName, "qualifiedName", 1);
  if (qualifiedName == NULL) {
    Py_DECREF(namespaceURI);
    return NULL;
  }

  if (doctype != Py_None) {
    DOMException_NotSupportedErr("doctype must be None for Domlettes");
    Py_DECREF(namespaceURI);
    Py_DECREF(qualifiedName);
    return NULL;
  }

  documentURI = XmlString_ConvertArgument(documentURI, "documentURI", 1);
  if (documentURI == NULL) {
    Py_DECREF(namespaceURI);
    Py_DECREF(qualifiedName);
    return NULL;
  }

  doc = Document_New(documentURI);
  if (doc == NULL) goto except;

  /* See if we need to add a documentElement */
  if (qualifiedName != Py_None) {
    PyObject *elem = PyObject_CallFunction((PyObject *)&DomletteElement_Type,
                                           "OO", namespaceURI, qualifiedName);
    if (elem == NULL) goto except;
    if (Node_AppendChild((NodeObject *)doc, (NodeObject *)elem) < 0) {
      Py_DECREF(elem);
      goto except;
    }
    Py_DECREF(elem);
  }

 finally:
  Py_DECREF(namespaceURI);
  Py_DECREF(qualifiedName);
  Py_DECREF(documentURI);
  return (PyObject *)doc;

 except:
  if (doc != NULL) {
    Py_DECREF(doc);
    doc = NULL;
  }
  goto finally;
}

static char domimp_createRootNode_doc[] = "\
Creates a Document object with the specified documentURI.";

static PyObject *domimp_createRootNode(PyObject *self, PyObject *args)
{
  return PyObject_CallObject((PyObject *)(&DomletteDocument_Type), args);
}

#define DOMImplementation_METHOD(name) \
  { #name, (PyCFunction) domimp_##name, METH_VARARGS, domimp_##name##_doc }

static PyMethodDef domimp_methods[] = {
  DOMImplementation_METHOD(hasFeature),
  DOMImplementation_METHOD(createDocument),
  DOMImplementation_METHOD(createRootNode),
  { NULL }
};

/** Python Members ****************************************************/

#define DOMImplementation_MEMBER(name, member) \
  { #name, T_OBJECT, offsetof(DOMImplementationObject, member), RO }

static PyMethodDef domimp_members[] = {
  { NULL }
};

/** Python Computed Members *******************************************/

static PyGetSetDef domimp_getset[] = {
  { NULL }
};

/** Type Object *******************************************************/

static void domimp_dealloc(DOMImplementationObject *self)
{
  PyObject_Del(self);
}

static PyObject *domimp_repr(DOMImplementationObject *self)
{
  return PyString_FromFormat("<DOMImplementation at %p>", self);
}

static char domimp_doc[] =
"The DOMImplementation interface provides a number of methods for performing\n\
operations that are independent of any particular instance of the document\n\
object model.";

PyTypeObject DomletteDOMImplementation_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Domlette_MODULE_NAME "." "DOMImplementation",
  /* tp_basicsize      */ sizeof(DOMImplementationObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) domimp_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) domimp_repr,
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
  /* tp_doc            */ (char *) domimp_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) domimp_methods,
  /* tp_members        */ (PyMemberDef *) domimp_members,
  /* tp_getset         */ (PyGetSetDef *) domimp_getset,
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

/** Module Interface **************************************************/

int DomletteDOMImplementation_Init(PyObject *module)
{
  DomletteDOMImplementation_Type.tp_base = &PyBaseObject_Type;
  if (PyType_Ready(&DomletteDOMImplementation_Type) < 0)
    return -1;

  g_implementation = (PyObject *)PyObject_New(DOMImplementationObject,
                                              &DomletteDOMImplementation_Type);
  if (g_implementation == NULL) return -1;

  if (PyModule_AddObject(module, "implementation", g_implementation) == -1)
    return -1;
  /* PyModule_AddObject steals a reference */
  Py_INCREF(g_implementation);

  Py_INCREF(&DomletteDOMImplementation_Type);
  return PyModule_AddObject(module, "DOMImplementation",
                            (PyObject*) &DomletteDOMImplementation_Type);
}

void DomletteDOMImplementation_Fini(void)
{
  Py_DECREF(g_implementation);
  PyType_CLEAR(&DomletteDOMImplementation_Type);
}
