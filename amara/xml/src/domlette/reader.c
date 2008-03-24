#include "Python.h"
#include "nodetype.h"
#include "parse_event_handler.h"

/** Private Routines **************************************************/

static int read_external_dtd;

static void factories_free(NodeFactories *factories)
{
  assert(factories != NULL);
  Py_XDECREF(factories->document_new);
  Py_XDECREF(factories->element_new);
  Py_XDECREF(factories->attr_new);
  Py_XDECREF(factories->text_new);
  Py_XDECREF(factories->processing_instruction_new);
  Py_XDECREF(factories->comment_new);
  PyMem_Free(factories);
}

static NodeFactories *factories_new(PyObject *nodeFactories)
{
  NodeFactories *factories;
  PyObject *item, *key;

  factories = PyMem_Malloc(sizeof(NodeFactories));
  if (factories == NULL)
    return NULL;

#define SET_FACTORY(NAME, TYPE) { \
  if ((key = PyInt_FromLong(TYPE)) == NULL) { \
    factories_free(factories); \
    return NULL; \
  } \
  item = PyObject_GetItem(nodeFactories, key); \
  Py_DECREF(key); \
  if (item == NULL && !PyErr_ExceptionMatches(PyExc_LookupError)) { \
    factories_free(factories); \
    return NULL; \
  } \
  factories->NAME = item; \
}

  SET_FACTORY(document_new, DOCUMENT_NODE);
  SET_FACTORY(element_new, ELEMENT_NODE);
  SET_FACTORY(attr_new, ATTRIBUTE_NODE);
  SET_FACTORY(text_new, TEXT_NODE);
  SET_FACTORY(processing_instruction_new, PROCESSING_INSTRUCTION_NODE);
  SET_FACTORY(comment_new, COMMENT_NODE);

#undef SET_FACTORY

  return factories;
}

static PyObject *parse_document(PyObject *isrc, int parse_type,
                                PyObject *factory_mapping)
{
  NodeFactories *factories=NULL;
  PyObject *result;

  if (factory_mapping != NULL) {
    factories = factories_new(factory_mapping);
    if (factories == NULL)
      return NULL;
  }

#ifdef DEBUG_PARSER
  fprintf(stderr, "Start parsing.\n");
#endif

  result = ParseDocument(isrc, parse_type, factories);

#ifdef DEBUG_PARSER
  fprintf(stderr,"Finished parsing\n");
#endif

  if (factories != NULL) {
    PyMem_Free(factories);
  }

  return result;
}

/** Public C API ******************************************************/

char Parse_doc[] = "\
Parse(isrc[, readExtDtd]) -> Document";

PyObject *Domlette_Parse(PyObject *self, PyObject *args, PyObject *kw) {
  PyObject *source;
  int parse_type=read_external_dtd;
  static char *kwlist[] = {"isrc", "readExtDtd", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, kw, "O|i:Parse", kwlist,
                                   &source, &parse_type))
    return NULL;

  return parse_document(source, parse_type, NULL);
}

char NonvalParse_doc[] = "\
NonvalParse(isrc[, readExtDtd[, nodeFactories]] ) -> Document";

PyObject *Domlette_NonvalParse(PyObject *self, PyObject *args, PyObject *kw)
{
  PyObject *isrc, *readExtDtd=NULL, *nodeFactories=NULL;
  static char *kwlist[] = {"isrc", "readExtDtd", "nodeFactories", NULL};
  int parse_type=read_external_dtd;

  if (!PyArg_ParseTupleAndKeywords(args, kw, "O|OO:NonvalParse", kwlist, 
                                   &isrc, &readExtDtd, &nodeFactories))
    return NULL;

  if (readExtDtd) {
    parse_type = PyObject_IsTrue(readExtDtd);
    if (parse_type == -1) return NULL;
  }

  return parse_document(isrc, parse_type, nodeFactories);
}


char ValParse_doc[] = "\
ValParse(isrc[, nodeFactories]) -> Document";

PyObject *Domlette_ValParse(PyObject *self, PyObject *args, PyObject *kw)
{
  PyObject *isrc, *nodeFactories=NULL;
  static char *kwlist[] = {"isrc", "nodeFactories", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, kw, "O|O:ValParse", kwlist,
                                   &isrc, &nodeFactories))
    return NULL;

  return parse_document(isrc, PARSE_TYPE_VALIDATE, nodeFactories);
}


char ParseFragment_doc[] = "\
ParseFragment(isrc[, namespaces[, nodeFactories]]) -> Document";

PyObject *Domlette_ParseFragment(PyObject *self, PyObject *args, PyObject *kw)
{
  PyObject *isrc, *namespaces=NULL, *nodeFactories=NULL;
  static char *kwlist[] = {"isrc", "namespaces", "nodeFactories", NULL};
  NodeFactories *node_factories=NULL;
  PyObject *result;

  if (!PyArg_ParseTupleAndKeywords(args, kw, "O|OO:ParseFragment", kwlist, 
                                   &isrc, &namespaces, &nodeFactories))
    return NULL;

  if (nodeFactories) {
    node_factories = factories_new(nodeFactories);
    if (node_factories == NULL)
      return NULL;
  }

#ifdef DEBUG_PARSER
  fprintf(stderr, "Start parsing.\n");
#endif

  result = ParseFragment(isrc, namespaces, node_factories);

#ifdef DEBUG_PARSER
  fprintf(stderr,"Finished parsing\n");
#endif

  if (node_factories != NULL) {
    PyMem_Free(node_factories);
  }

  return result;
}


int DomletteReader_Init(PyObject *module)
{
  PyObject *import, *constant;

  import = PyImport_ImportModule("Ft.Xml");
  if (import == NULL) return -1;

  constant = PyObject_GetAttrString(import, "READ_EXTERNAL_DTD");
  if (constant == NULL) {
    Py_DECREF(import);
    return -1;
  }
  Py_DECREF(import);

  read_external_dtd = PyObject_IsTrue(constant);
  Py_DECREF(constant);
  if (read_external_dtd == -1) return -1;

  return 0;
}

void DomletteReader_Fini(void)
{
  /* no cleanup to perform */
}
