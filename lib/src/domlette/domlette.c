/***********************************************************************
 * $Header: /var/local/cvsroot/4Suite/Ft/Xml/src/domlette/domlette.c,v 1.60 2008-02-29 20:54:19 uogbuji Exp $
 ***********************************************************************/

static char module_doc[] = "\
cDomlette implementation: a very fast DOM-like library tailored for use in XPath/XSLT\n\
\n\
Copyright 2006 Fourthought, Inc. (USA).\n\
Detailed license and copyright information: http://4suite.org/COPYRIGHT\n\
Project home, documentation, distributions: http://4suite.org/\n\
";

#define PY_SSIZE_T_CLEAN
#define XmlString_SHARED
#include "xmlstring.h"
#include "domlette_interface.h"
#include "builder.h"
#include "refcounts.h"

/*
  These are the external interfaces
*/

#define CHECK_REFS(op, refs) do {                         \
  Py_ssize_t expected = (Py_ssize_t)(refs);               \
  Py_ssize_t compared = (op)->ob_refcnt;                  \
  if (expected != compared) {                             \
    PyErr_Format(PyExc_MemoryError,                       \
                 "%s:%d: refcount mismatch: expected %zd, compared %zd", \
                 __FILE__, __LINE__, expected, compared); \
    return NULL;                                          \
  }                                                       \
} while (0)

/* The test tree XML:
test_xml = """<?xml version = "1.0"?>
<?xml-stylesheet href="addr_book1.xsl" type="text/xml"?>
<docelem xmlns:ft="http://fourthought.com">
  <child foo='bar'>Some Text</child>
  <!--A comment-->
  <ft:nschild ft:foo="nsbar">Some More Text</ft:nschild>
  <appendChild/>
</docelem>"""
*/

static PyObject *PyTestTree(PyObject *self, PyObject *args)
{
  /*Build a test tree*/
  EntityObject *doc;
  ProcessingInstructionObject *pi;
  ElementObject *documentElement, *element;
  TextObject *text;
  CommentObject *comment;
  AttrObject *attr;
  NamespaceObject *nsattr;
  PyObject *namespaceURI, *qualifiedName, *localName;
  PyObject *target, *data, *value;

  if (!PyArg_ParseTuple(args, ":TestTree")) return NULL;

  doc = Entity_New(Py_None);
  if (doc == NULL) return NULL;
  CHECK_REFS(doc, 1);

  /* Add processing instruction */
  target = XmlString_FromASCII("xml-stylesheet");
  data = XmlString_FromASCII("href=\"addr_book1.xsl\" type=\"text/xml\"");
  if (target == NULL || data == NULL) {
    Py_XDECREF(target);
    Py_XDECREF(data);
    Py_DECREF(doc);
    return NULL;
  }
  pi = ProcessingInstruction_New(target, data);
  Py_DECREF(target);
  Py_DECREF(data);
  if (pi == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  if (Container_Append((NodeObject *)doc, (NodeObject *)pi) < 0) {
    Py_DECREF(pi);
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(pi);

  CHECK_REFS(doc, 2);
  CHECK_REFS(pi, 1);

  /* Add documentElement */
  namespaceURI = Py_None;
  qualifiedName = localName = XmlString_FromASCII("docelem");
  if (qualifiedName == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  documentElement = Element_New(namespaceURI, qualifiedName, localName);
  Py_DECREF(qualifiedName);
  if (documentElement == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  if (Container_Append((NodeObject *)doc, (NodeObject *)documentElement) < 0) {
    Py_DECREF(documentElement);
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(documentElement);

  CHECK_REFS(doc, 3);
  CHECK_REFS(documentElement, 1);

  /* Add documentElement namespace declartion */
  localName = XmlString_FromASCII("ft");
  namespaceURI = XmlString_FromASCII("http://fourthought.com");
  if (localName == NULL || namespaceURI == NULL) {
    Py_XDECREF(localName);
    Py_XDECREF(namespaceURI);
    Py_DECREF(doc);
    return NULL;
  }
  nsattr = Element_AddNamespace(documentElement, localName, namespaceURI);
  Py_DECREF(localName);
  Py_DECREF(namespaceURI);
  if (nsattr == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(nsattr);

  CHECK_REFS(doc, 3);
  CHECK_REFS(documentElement, 2);
  CHECK_REFS(nsattr, 1);

  /* Add text 1 to documentElement */
  data = XmlString_FromASCII("\n  ");
  if (data == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  text = Text_New(data);
  Py_DECREF(data);
  if (text == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  if (Container_Append((NodeObject *)documentElement,
                       (NodeObject *)text) < 0) {
    Py_DECREF(text);
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(text);

  CHECK_REFS(doc, 3);
  CHECK_REFS(documentElement, 3);
  CHECK_REFS(text, 1);

  /* Add element 1 to documentElement */
  namespaceURI = Py_None;
  qualifiedName = localName = XmlString_FromASCII("child");
  if (qualifiedName == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  element = Element_New(namespaceURI, qualifiedName, localName);
  Py_DECREF(qualifiedName);
  if (element == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  if (Container_Append((NodeObject *)documentElement,
                       (NodeObject *)element) < 0) {
    Py_DECREF(element);
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(element);

  CHECK_REFS(doc, 3);
  CHECK_REFS(documentElement, 4);
  CHECK_REFS(element, 1);

  /* Add element 1 attribute */
  namespaceURI = Py_None;
  qualifiedName = localName = XmlString_FromASCII("foo");
  value = XmlString_FromASCII("bar");
  if (qualifiedName == NULL || value == NULL) {
    Py_XDECREF(qualifiedName);
    Py_XDECREF(value);
    Py_DECREF(doc);
    return NULL;
  }
  attr = Element_AddAttribute(element, namespaceURI, qualifiedName,
                              localName, value);
  Py_DECREF(qualifiedName);
  Py_DECREF(value);
  if (attr == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(attr);

  CHECK_REFS(doc, 3);
  CHECK_REFS(element, 2);
  CHECK_REFS(attr, 1);

  /* Add element 1 text */
  data = XmlString_FromASCII("Some Text");
  if (data == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  text = Text_New(data);
  Py_DECREF(data);
  if (text == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  if (Container_Append((NodeObject *)element, (NodeObject *)text) < 0) {
    Py_DECREF(text);
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(text);

  CHECK_REFS(doc, 3);
  CHECK_REFS(element, 3);
  CHECK_REFS(text, 1);

  /* Add text 2 to documentElement */
  data = XmlString_FromASCII("\n  ");
  if (data == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  text = Text_New(data);
  Py_DECREF(data);
  if (text == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  if (Container_Append((NodeObject *)documentElement,
                       (NodeObject *)text) < 0) {
    Py_DECREF(text);
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(text);

  CHECK_REFS(doc, 3);
  CHECK_REFS(documentElement, 5);
  CHECK_REFS(text, 1);

  /* Add comment to documentElement */
  data = XmlString_FromASCII("A comment");
  if (data == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  comment = Comment_New(data);
  Py_DECREF(data);
  if (comment == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  if (Container_Append((NodeObject *)documentElement,
                       (NodeObject *)comment) < 0) {
    Py_DECREF(comment);
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(comment);

  CHECK_REFS(doc, 3);
  CHECK_REFS(documentElement, 6);
  CHECK_REFS(comment, 1);

  /* Add text 3 to documentElement */
  data = XmlString_FromASCII("\n  ");
  if (data == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  text = Text_New(data);
  Py_DECREF(data);
  if (text == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  if (Container_Append((NodeObject *)documentElement,
                       (NodeObject *)text) < 0) {
    Py_DECREF(text);
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(text);

  CHECK_REFS(doc, 3);
  CHECK_REFS(documentElement, 7);
  CHECK_REFS(text, 1);

  /* Add element 2 to documentElement */
  namespaceURI = XmlString_FromASCII("http://fourthought.com");
  qualifiedName = XmlString_FromASCII("ft:nschild");
  localName = XmlString_FromASCII("nschild");
  if (namespaceURI == NULL || qualifiedName == NULL || localName == NULL) {
    Py_XDECREF(namespaceURI);
    Py_XDECREF(qualifiedName);
    Py_XDECREF(localName);
    Py_DECREF(doc);
    return NULL;
  }
  element = Element_New(namespaceURI, qualifiedName, localName);
  Py_DECREF(localName);
  Py_DECREF(qualifiedName);
  Py_DECREF(namespaceURI);
  if (element == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  if (Container_Append((NodeObject *)documentElement,
                       (NodeObject *)element) < 0) {
    Py_DECREF(element);
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(element);

  CHECK_REFS(doc, 3);
  CHECK_REFS(documentElement, 8);
  CHECK_REFS(element, 1);

  /* Add element 2 attribute */
  namespaceURI = XmlString_FromASCII("http://fourthought.com");
  qualifiedName = XmlString_FromASCII("ft:foo");
  localName = XmlString_FromASCII("foo");
  value = XmlString_FromASCII("nsbar");
  if (namespaceURI == NULL || qualifiedName == NULL || localName == NULL ||
      value == NULL) {
    Py_XDECREF(namespaceURI);
    Py_XDECREF(qualifiedName);
    Py_XDECREF(localName);
    Py_XDECREF(value);
    Py_DECREF(doc);
    return NULL;
  }
  attr = Element_AddAttribute(element, namespaceURI, qualifiedName,
                              localName, value);
  Py_DECREF(value);
  Py_DECREF(localName);
  Py_DECREF(qualifiedName);
  Py_DECREF(namespaceURI);
  if (attr == NULL) {
    Py_DECREF(element);
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(attr);

  CHECK_REFS(doc, 3);
  CHECK_REFS(element, 2);
  CHECK_REFS(attr, 1);

  /* Add element 2 text node */
  data = XmlString_FromASCII("Some More Text");
  if (data == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  text = Text_New(data);
  Py_DECREF(data);
  if (text == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  if (Container_Append((NodeObject *)element, (NodeObject *)text) < 0) {
    Py_DECREF(text);
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(text);

  CHECK_REFS(doc, 3);
  CHECK_REFS(element, 3);
  CHECK_REFS(text, 1);

  /* Add text 4 to documentElement */
  data = XmlString_FromASCII("\n  ");
  if (data == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  text = Text_New(data);
  Py_DECREF(data);
  if (text == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  if (Container_Append((NodeObject *)documentElement,
                       (NodeObject *)text) < 0) {
    Py_DECREF(text);
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(text);

  CHECK_REFS(doc, 3);
  CHECK_REFS(documentElement, 9);
  CHECK_REFS(text, 1);

  /* Add element 3 to documentElement */
  namespaceURI = Py_None;
  qualifiedName = localName = XmlString_FromASCII("appendChild");
  if (qualifiedName == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  element = Element_New(namespaceURI, qualifiedName, localName);
  Py_DECREF(qualifiedName);
  if (element == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  if (Container_Append((NodeObject *)documentElement,
                       (NodeObject *)element) < 0) {
    Py_DECREF(element);
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(element);

  CHECK_REFS(doc, 3);
  CHECK_REFS(documentElement, 10);
  CHECK_REFS(element, 1);

  /* Add text 5 to documentElement */
  data = XmlString_FromASCII("\n  ");
  if (data == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  text = Text_New(data);
  Py_DECREF(data);
  if (text == NULL) {
    Py_DECREF(doc);
    return NULL;
  }
  if (Container_Append((NodeObject *)documentElement,
                       (NodeObject *)text) < 0) {
    Py_DECREF(text);
    Py_DECREF(doc);
    return NULL;
  }
  Py_DECREF(text);

  CHECK_REFS(doc, 3);
  CHECK_REFS(documentElement, 11);
  CHECK_REFS(text, 1);

  return (PyObject *)doc;

}


/** The external interface definitions ********************************/

#define Domlette_METHOD(name, flags)                            \
  { #name, (PyCFunction) Domlette_##name, flags, name##_doc }

static PyMethodDef module_methods[] = {
  /* from builder.c */
  { "parse", (PyCFunction) Domlette_Parse, METH_KEYWORDS,
    "parse(source[, flags[, node_factories]]) -> Document" },
  { "parse_fragment", (PyCFunction) Domlette_ParseFragment, METH_KEYWORDS,
    "parse_fragment(source[, namespaces[, node_factories]]) -> Document" },

  /* from nss.c */
  //Domlette_METHOD(GetAllNs, METH_VARARGS),
  //Domlette_METHOD(SeekNss, METH_VARARGS),

  /* defined here (regression tests) */
  { "TestTree", PyTestTree, METH_VARARGS,
    "TestTree() -> Document\n\nFor regression testing." },

  { NULL }
};

static Domlette_APIObject Domlette_API = {
  &DomletteNode_Type,
  &DomletteEntity_Type,
  &DomletteElement_Type,
  &DomletteAttr_Type,
  &DomletteText_Type,
  &DomletteComment_Type,
  &DomletteProcessingInstruction_Type,
  &DomletteNamespace_Type,

  Container_Remove,
  Container_Append,
  Container_Insert,
  Container_Replace,

  Entity_New,

  Element_New,
  Element_AddNamespace,
  Element_AddAttribute,
  Element_InscopeNamespaces,

  Text_New,

  Comment_New,

  ProcessingInstruction_New,

  Namespace_New,

  NamespaceMap_Next,

  AttributeMap_Next,
};

struct submodule_t {
  int (*init)(PyObject *);
  void (*fini)(void);
};

#define SUBMODULE(name) { Domlette##name##_Init, Domlette##name##_Fini }
struct submodule_t submodules[] = {
  SUBMODULE(Exceptions),
  SUBMODULE(Builder),
  SUBMODULE(Node),
  SUBMODULE(Container),
  SUBMODULE(NamespaceMap),
  SUBMODULE(AttributeMap),
  SUBMODULE(Attr),
  SUBMODULE(Element),
  SUBMODULE(CharacterData),
  SUBMODULE(Text),
  SUBMODULE(ProcessingInstruction),
  SUBMODULE(Comment),
  SUBMODULE(Entity),
  SUBMODULE(Namespace),
  { NULL, NULL }
};


static void fini_domlette(void *capi)
{
  struct submodule_t *submodule;
  for (submodule = submodules; submodule->fini; submodule++) {
    submodule->fini();
  }
}

DL_EXPORT(void) init_domlette(void)
{
  PyObject *module;
  struct submodule_t *submodule;
  PyObject *cobj;

  module = Py_InitModule3("_domlette", module_methods, module_doc);
  if (module == NULL) return;

  if ((XmlString_IMPORT) == NULL) return;

  /* initialize the sub-components */
  for (submodule = submodules; submodule->init; submodule++) {
    if (submodule->init(module) < 0) return;
  }

  /* Export C API - done last to serve as a cleanup function as well */
  cobj = PyCObject_FromVoidPtr((void *)&Domlette_API, fini_domlette);
  if (cobj) {
    PyModule_AddObject(module, "CAPI", cobj);
  }
  return;
}
