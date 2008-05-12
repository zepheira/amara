#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"
#include "expat_interface.h"

/*#define DEBUG_PARSER */
#define INITIAL_CHILDREN 4

typedef struct _context {
  struct _context *next;
  NodeObject *node;

  NodeObject **children;
  Py_ssize_t children_allocated;
  Py_ssize_t children_size;
} Context;

typedef struct {
  PyObject *document_new;
  PyObject *element_new;
  PyObject *attr_new;
  PyObject *text_new;
  PyObject *processing_instruction_new;
  PyObject *comment_new;
} NodeFactories;

typedef struct {
  ExpatReader *reader;

  Context *context;
  Context *free_context;

  NodeFactories *factories;

  PyObject *new_namespaces;

  DocumentObject *owner_document;
} ParserState;

typedef enum {
  PARSE_FLAGS_STANDALONE = 0,
  PARSE_FLAGS_EXTERNAL_ENTITIES,
  PARSE_FLAGS_VALIDATE,
} ParseFlags;

ParseFlags default_parse_flags = PARSE_FLAGS_EXTERNAL_ENTITIES;

static PyObject *xmlns_string;
static PyObject *empty_args_tuple;
static PyObject *gc_enable_function;
static PyObject *gc_disable_function;
static PyObject *gc_isenabled_function;

/** Context ************************************************************/

Py_LOCAL_INLINE(Context *)
Context_New(NodeObject *node)
{
  Context *self = PyMem_New(Context, 1);
  if (self == NULL) {
    PyErr_NoMemory();
    return NULL;
  }
  memset(self, 0, sizeof(Context));

  self->node = node;

  self->children = PyMem_New(NodeObject *, INITIAL_CHILDREN);
  if (self->children == NULL) {
    PyErr_NoMemory();
    PyMem_Free(self);
    return NULL;
  }
  self->children_allocated = INITIAL_CHILDREN;
  return self;
}

Py_LOCAL_INLINE(void)
Context_Del(Context *self)
{
  Py_ssize_t i;

  /* This will only be set when an error has occurred, so it must be freed. */
  if (self->node) {
    Py_DECREF(self->node);
  }

  for (i = self->children_size; --i >= 0;) {
    Py_DECREF(self->children[i]);
  }
  PyMem_Free(self->children);

  if (self->next) {
    Context_Del(self->next);
  }

  PyMem_Free(self);
}

/** NodeFactories *****************************************************/

Py_LOCAL_INLINE(void)
NodeFactories_Del(NodeFactories *factories)
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

Py_LOCAL_INLINE(NodeFactories *)
NodeFactories_New(PyObject *nodeFactories)
{
  NodeFactories *factories;
  PyObject *item, *key;

  factories = PyMem_Malloc(sizeof(NodeFactories));
  if (factories == NULL)
    return NULL;

#define SET_FACTORY(NAME, TYPE) { \
  if ((key = PyInt_FromLong(TYPE)) == NULL) { \
    NodeFactories_Del(factories); \
    return NULL; \
  } \
  item = PyObject_GetItem(nodeFactories, key); \
  Py_DECREF(key); \
  if (item == NULL && !PyErr_ExceptionMatches(PyExc_LookupError)) { \
    NodeFactories_Del(factories); \
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

/** ParserState ********************************************************/

Py_LOCAL_INLINE(ParserState *)
ParserState_New(NodeFactories *factories)
{
  ParserState *self = PyMem_New(ParserState, 1);
  if (self == NULL) {
    PyErr_NoMemory();
  } else {
    memset(self, 0, sizeof(ParserState));
    self->factories = factories;
  }
  return self;
}

static void ParserState_Del(ParserState *self)
{
  if (self->context) {
    Context_Del(self->context);
  }
  if (self->free_context) {
    Context_Del(self->free_context);
  }
  Py_CLEAR(self->new_namespaces);
  Py_CLEAR(self->owner_document);
  PyMem_Free(self);
}

Py_LOCAL_INLINE(Context *)
ParserState_AddContext(ParserState *self, NodeObject *node)
{
  Context *context = self->free_context;
  if (context != NULL) {
    /* reuse an existing context */
    context->node = node;
    self->free_context = context->next;
  } else {
    /* create a new context */
    context = Context_New(node);
    if (context == NULL) return NULL;
  }

  /* make it the active context */
  context->next = self->context;
  self->context = context;
  return context;
}

Py_LOCAL_INLINE(void)
ParserState_FreeContext(ParserState *self)
{
  Context *context = self->context;
  if (context != NULL) {
    /* switch the active context to the following one */
    self->context = context->next;

    /* move this one to the free list */
    context->next = self->free_context;
    self->free_context = context;

    /* reset its values */
    context->node = NULL;
    context->children_size = 0;
  }
}

static int ParserState_AddNode(ParserState *self, NodeObject *node)
{
  Context *context = self->context;
  NodeObject **children;
  Py_ssize_t newsize;

  if (node == NULL || context == NULL) {
#ifdef DEBUG_PARSER
    abort();
#else
    PyErr_BadInternalCall();
    return -1;
#endif
  }

  /* increase size of child array, if needed */
  children = context->children;
  newsize = context->children_size + 1;
  if (newsize >= context->children_allocated) {
    size_t new_allocated = newsize << 1;
    if (PyMem_Resize(children, NodeObject *, new_allocated) == NULL) {
      PyErr_NoMemory();
      return -1;
    }
    context->children = children;
    context->children_allocated = new_allocated;
  }

  /* add the node to the children array */
  children[context->children_size] = node;
  context->children_size = newsize;
  return 0;
}

/** handlers ***********************************************************/

static ExpatStatus
builder_StartDocument(void *userState)
{
  ParserState *state = (ParserState *)userState;
  NodeFactories *factories = state->factories;
  PyObject *uri;
  DocumentObject *document;

#ifdef DEBUG_PARSER
  fprintf(stderr, "--- builder_StartDocument(%p)\n", state);
#endif
  uri = ExpatReader_GetBase(state->reader);
  if (factories && factories->document_new) {
    PyObject *obj = PyObject_CallFunction(factories->document_new, "O", uri);
    if (obj && !Document_Check(obj)) {
      PyErr_Format(PyExc_TypeError,
                   "DOCUMENT_NODE factory returned non-Document"
                   " (type %.200s)",
                   obj->ob_type->tp_name);
      Py_CLEAR(obj);
    }
    document = Document(obj);
  } else {
    document = Document_New(uri);
  }
  Py_DECREF(uri);
  if (document == NULL)
    return EXPAT_STATUS_ERROR;

  if (ParserState_AddContext(state, (NodeObject *)document) == NULL) {
    Py_DECREF(document);
    return EXPAT_STATUS_ERROR;
  }
  Py_INCREF(document);
  state->owner_document = document;

  return EXPAT_STATUS_OK;
}

static ExpatStatus
builder_EndDocument(void *userState)
{
  ParserState *state = (ParserState *)userState;
  Context *context = state->context;

#ifdef DEBUG_PARSER
  fprintf(stderr, "--- builder_EndDocument()\n");
#endif

  /* Set the document's children */
  if (_Node_SetChildren(context->node, context->children,
                        context->children_size)) {
    return EXPAT_STATUS_ERROR;
  }

  /* Mark the current context as free */
  ParserState_FreeContext(state);
  return EXPAT_STATUS_OK;
}

static ExpatStatus
builder_NamespaceDecl(void *arg, PyObject *prefix, PyObject *uri)
{
  ParserState *state = (ParserState *)arg;

#ifdef DEBUG_PARSER
  fprintf(stderr, "--- builder_NamespaceDecl(prefix=");
  PyObject_Print(prefix, stderr, 0);
  fprintf(stderr, ", uri=");
  PyObject_Print(uri, stderr, 0);
  fprintf(stderr, ")\n");
#endif

  if (state->new_namespaces == NULL) {
    /* first namespace for this element */
    state->new_namespaces = PyDict_New();
    if (state->new_namespaces == NULL) {
      return EXPAT_STATUS_ERROR;
    }
  }

  if (uri == Py_None) {
    /* Use an empty string as this will be added as an attribute value.
       Fixes SF#834917
    */
    uri = PyUnicode_FromUnicode(NULL, 0);
    if (uri == NULL) {
      return EXPAT_STATUS_ERROR;
    }
  } else {
    Py_INCREF(uri);
  }

  if (PyDict_SetItem(state->new_namespaces, prefix, uri) < 0) {
    Py_DECREF(uri);
    return EXPAT_STATUS_ERROR;
  }

  Py_DECREF(uri);
  return EXPAT_STATUS_OK;
}

Py_LOCAL_INLINE(AttrObject *)
add_attribute(ParserState *state, ElementObject *element,
              PyObject *namespaceURI, PyObject *qualifiedName,
              PyObject *localName, PyObject *value)
{
  NodeFactories *factories = state->factories;
  AttrObject *attr;

  if (factories && factories->attr_new) {
    PyObject *ob = PyObject_CallFunction(factories->attr_new, "OO",
                                         namespaceURI, qualifiedName);
    if (ob == NULL)
      return NULL;
    else if (!Attr_Check(ob)) {
      PyErr_Format(PyExc_TypeError,
                   "ATTRIBUTE_NODE factory returned non-Attr (type %.200s)",
                   ob->ob_type->tp_name);
      Py_DECREF(ob);
      return NULL;
    }
    if (PyObject_SetAttrString(ob, "value", value) < 0) {
      Py_DECREF(ob);
      return NULL;
    }
    attr = Attr(ob);
    if (Element_CheckExact(element)) {
      ob = Element_SetAttributeNodeNS(element, attr);
    } else {
      static PyObject *funcname = NULL;
      PyObject *func, *args;
      if (funcname == NULL) {
        funcname = PyString_FromString("setAttributeNodeNS");
        if (funcname == NULL)
          return NULL;
      }
      func = PyObject_GetAttr((PyObject *)element, funcname);
      if (func == NULL)
        return NULL;
      args = PyTuple_Pack(1, attr);
      if (args == NULL)
        return NULL;
      ob = PyObject_Call(func, args, NULL);
      Py_DECREF(func);
      Py_DECREF(args);
    }
    if (ob == NULL) {
      Py_CLEAR(attr);
    }
  } else {
    if (Element_CheckExact(element)) {
      attr = Element_SetAttributeNS(element, namespaceURI, qualifiedName,
                                    localName, value);
    } else {
      static PyObject *funcname = NULL;
      PyObject *func, *args;
      if (funcname == NULL) {
        funcname = PyString_FromString("setAttributeNS");
        if (funcname == NULL)
          return NULL;
      }
      func = PyObject_GetAttr((PyObject *)element, funcname);
      if (func == NULL)
        return NULL;
      args = PyTuple_Pack(3, namespaceURI, qualifiedName, value);
      if (args == NULL)
        return NULL;
      attr = Attr(PyObject_Call(func, args, NULL));
      Py_DECREF(func);
      Py_DECREF(args);
    }
  }
  return attr;
}

static ExpatStatus
builder_StartElement(void *userState, ExpatName *name,
                     ExpatAttribute atts[], int natts)
{
  ParserState *state = (ParserState *)userState;
  NodeFactories *factories = state->factories;
  ElementObject *elem = NULL;
  Py_ssize_t i;
  PyObject *key, *value;
  PyObject *localName, *qualifiedName, *prefix;

#ifdef DEBUG_PARSER
  fprintf(stderr, "--- builder_StartElement(name=");
  PyObject_Print(name->qualifiedName, stderr, 0);
  fprintf(stderr, ", atts={");
  for (i = 0; i < natts; i++) {
    if (i > 0) {
      fprintf(stderr, ", ");
    }
    PyObject_Print(atts[i].qualifiedName, stderr, 0);
    fprintf(stderr, ", ");
    PyObject_Print(atts[i].value, stderr, 0);
  }
  fprintf(stderr, "})\n");
#endif

  if (factories && factories->element_new) {
    PyObject *obj = PyObject_CallFunction(factories->element_new, "OO",
                                          name->namespaceURI,
                                          name->qualifiedName);
    if (obj && !Element_Check(obj)) {
      PyErr_Format(PyExc_TypeError,
                   "ELEMENT_NODE factory returned non-Element"
                   " (type %.200s)",
                   obj->ob_type->tp_name);
      Py_CLEAR(obj);
    }
    elem = Element(obj);
  } else {
    elem = Element_New(name->namespaceURI, name->qualifiedName,
                       name->localName);
  }
  if (elem == NULL) {
    return EXPAT_STATUS_ERROR;
  }

  /** namespaces *******************************************************/

  /* new_namespaces is a dictionary where key is the prefix and value
   * is the uri.
   */
  if (state->new_namespaces) {
    i = 0;
    while (PyDict_Next(state->new_namespaces, &i, &key, &value)) {
      AttrObject *nsattr;
      if (key != Py_None) {
        prefix = xmlns_string;
        localName = key;
      } else {
        prefix = key;
        localName = xmlns_string;
      }

      qualifiedName = XmlString_MakeQName(prefix, localName);
      if (qualifiedName == NULL) {
        Py_DECREF(elem);
        return EXPAT_STATUS_ERROR;
      }

      nsattr = add_attribute(state, elem, g_xmlnsNamespace, qualifiedName,
                             localName, value);
      Py_DECREF(qualifiedName);
      if (nsattr == NULL) {
        Py_DECREF(elem);
        return EXPAT_STATUS_ERROR;
      }
      Py_DECREF(nsattr);
    }
    /* make sure children don't set these namespaces */
    Py_DECREF(state->new_namespaces);
    state->new_namespaces = NULL;
  }

  /** attributes *******************************************************/

  for (i = 0; i < natts; i++) {
    AttrObject *attr = add_attribute(state, elem, atts[i].namespaceURI,
                                     atts[i].qualifiedName, atts[i].localName,
                                     atts[i].value);
    if (attr == NULL) {
      Py_DECREF(elem);
      return EXPAT_STATUS_ERROR;
    }

    /* save the attribute type as well (for getElementById) */
    attr->type = atts[i].type;

    Py_DECREF(attr);
  }

  /* save states on the context */
  if (ParserState_AddContext(state, (NodeObject *) elem) == NULL) {
    Py_DECREF(elem);
    return EXPAT_STATUS_ERROR;
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus
builder_EndElement(void *userState, ExpatName *name)
{
  ParserState *state = (ParserState *)userState;
  Context *context = state->context;
  NodeObject *node;

#ifdef DEBUG_PARSER
  fprintf(stderr, "--- builder_EndElement(name=");
  PyObject_Print(name->qualifiedName, stderr, 0);
  fprintf(stderr, ")\n");
#endif

  /* Get the newly constructed element */
  node = context->node;

  /* Set the element's children */
  if (_Node_SetChildren(node, context->children, context->children_size)) {
    return EXPAT_STATUS_ERROR;
  }

  /* Mark the current context as free */
  ParserState_FreeContext(state);

  /* ParserState_AddNode steals the reference to the new node */
  if (ParserState_AddNode(state, node) < 0) {
    Py_DECREF(node);
    return EXPAT_STATUS_ERROR;
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus
builder_Attribute(void *userState, ExpatName *name, PyObject *value,
                  AttributeType type)
{
  ParserState *state = (ParserState *)userState;
  AttrObject *attr;

#ifdef DEBUG_PARSER
  fprintf(stderr, "--- builder_Attribute(name=");
  PyObject_Print(name->qualifiedName, stderr, 0);
  fprintf(stderr, ", value=");
  PyObject_Print(value, stderr, 0);
  fprintf(stderr, ")\n");
#endif

  attr = add_attribute(state, (ElementObject *)state->context->node,
                       name->namespaceURI, name->qualifiedName,
                       name->localName, value);
  if (attr == NULL)
    return EXPAT_STATUS_ERROR;

  /* save the attribute type as well (for getElementById) */
  attr->type = type;

  Py_DECREF(attr);
  return EXPAT_STATUS_OK;
}

static ExpatStatus
builder_Characters(void *userState, PyObject *data)
{
  ParserState *state = (ParserState *)userState;
  NodeFactories *factories = state->factories;
  NodeObject *node;

#ifdef DEBUG_PARSER
  fprintf(stderr, "--- builder_Characters(data=");
  PyObject_Print(data, stderr, 0);
  fprintf(stderr, ")\n");
#endif

  if (factories && factories->text_new) {
    PyObject *obj = PyObject_CallFunction(factories->text_new, "O", data);
    if (obj && !Text_Check(obj)) {
      PyErr_Format(PyExc_TypeError,
                   "TEXT_NODE factory returned non-Text"
                   " (type %.200s)",
                   obj->ob_type->tp_name);
      Py_CLEAR(obj);
    }
    node = (NodeObject *)obj;
  } else {
    node = (NodeObject *)Text_New(data);
  }

  /* ParserState_AddNode steals the reference to the new node */
  if (ParserState_AddNode(state, node) < 0) {
    Py_DECREF(node);
    return EXPAT_STATUS_ERROR;
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus
builder_ProcessingInstruction(void *userState, PyObject *target, PyObject *data)
{
  ParserState *state = (ParserState *)userState;
  NodeFactories *factories = state->factories;
  NodeObject *node;

#ifdef DEBUG_PARSER
  fprintf(stderr, "--- builder_ProcessingInstruction(target=");
  PyObject_Print(target, stderr, 0);
  fprintf(stderr, ", data=");
  PyObject_Print(data, stderr, 0);
  fprintf(stderr, ")\n");
#endif

  if (factories && factories->processing_instruction_new) {
    PyObject *obj =
      PyObject_CallFunction(factories->processing_instruction_new,
                            "OO", target, data);
    if (obj && !ProcessingInstruction_Check(obj)) {
      PyErr_Format(PyExc_TypeError,
                   "PROCESSING_INSTRUCTION_NODE factory returned"
                   " non-ProcessingInstruction (type %.200s)",
                   obj->ob_type->tp_name);
      Py_CLEAR(obj);
    }
    node = (NodeObject *)obj;
  } else {
    node = (NodeObject *)ProcessingInstruction_New(target, data);
  }

  /* ParserState_AddNode steals the reference to the new node */
  if (ParserState_AddNode(state, node) < 0) {
    Py_DECREF(node);
    return EXPAT_STATUS_ERROR;
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus
builder_Comment(void *userState, PyObject *data)
{
  ParserState *state = (ParserState *)userState;
  NodeFactories *factories = state->factories;
  NodeObject *node;

#ifdef DEBUG_PARSER
  fprintf(stderr, "--- builder_Comment(data=");
  PyObject_Print(data, stderr, 0);
  fprintf(stderr, ")\n");
#endif

  if (factories && factories->comment_new) {
    PyObject *obj = PyObject_CallFunction(factories->comment_new, "O", data);
    if (obj && !Comment_Check(obj)) {
      PyErr_Format(PyExc_TypeError,
                   "COMMENT_NODE factory returned non-Comment"
                   " (type %.200s)",
                   obj->ob_type->tp_name);
      Py_CLEAR(obj);
    }
    node = (NodeObject *)obj;
  } else {
    node = (NodeObject *)Comment_New(data);
  }

  /* ParserState_AddNode steals the reference to the new node */
  if (ParserState_AddNode(state, node) < 0) {
    Py_DECREF(node);
    return EXPAT_STATUS_ERROR;
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus
builder_DoctypeDecl(void *userState, PyObject *name, PyObject *systemId,
                    PyObject *publicId)
{
  ParserState *state = (ParserState *)userState;

#ifdef DEBUG_PARSER
  fprintf(stderr, "--- builder_DoctypeDecl(name=");
  PyObject_Print(name, stderr, 0);
  fprintf(stderr, ", systemId=");
  PyObject_Print(systemId, stderr, 0);
  fprintf(stderr, ", publicId=");
  PyObject_Print(publicId, stderr, 0);
  fprintf(stderr, ")\n");
#endif

  Py_DECREF(state->owner_document->systemId);
  Py_INCREF(systemId);
  state->owner_document->systemId = systemId;

  Py_DECREF(state->owner_document->publicId);
  Py_INCREF(publicId);
  state->owner_document->publicId = publicId;

  return EXPAT_STATUS_OK;
}

static ExpatStatus
builder_UnparsedEntityDecl(void *userState, PyObject *name, PyObject *publicId,
                           PyObject *systemId, PyObject *notationName)
{
  ParserState *state = (ParserState *)userState;

#ifdef DEBUG_PARSER
  fprintf(stderr, "--- builder_UnparsedEntityDecl(name=");
  PyObject_Print(name, stderr, 0);
  fprintf(stderr, ", publicId=");
  PyObject_Print(publicId, stderr, 0);
  fprintf(stderr, ", systemId=");
  PyObject_Print(systemId, stderr, 0);
  fprintf(stderr, ", notationName=");
  PyObject_Print(notationName, stderr, 0);
  fprintf(stderr, ")\n");
#endif

  if (PyDict_SetItem(state->owner_document->unparsedEntities, name, systemId))
    return EXPAT_STATUS_ERROR;

  return EXPAT_STATUS_OK;
}

/** Python Interface **************************************************/

static ExpatHandlers builder_handlers = {
  /* start_element          */ NULL,
  /* end_element            */ NULL,
  /* start_document         */ builder_StartDocument,
  /* end_document           */ builder_EndDocument,
  /* start_element          */ builder_StartElement,
  /* end_element            */ builder_EndElement,
  /* attribute              */ builder_Attribute,
  /* characters             */ builder_Characters,
  /* ignorable_whitespace   */ builder_Characters,
  /* processing_instruction */ builder_ProcessingInstruction,
  /* comment                */ builder_Comment,
  /* start_namespace_decl   */ builder_NamespaceDecl,
  /* end_namespace_decl     */ NULL,
  /* start_doctype_decl     */ builder_DoctypeDecl,
  /* end_doctype_decl       */ NULL,
  /* element_decl           */ NULL,
  /* attribute_decl         */ NULL,
  /* internal_entity_decl   */ NULL,
  /* external_entity_decl   */ NULL,
  /* unparsed_entity_decl   */ builder_UnparsedEntityDecl,
};

Py_LOCAL_INLINE(ExpatReader *)
create_reader(ParserState *state)
{
  ExpatFilter *filters[1];
  ExpatReader *reader;

  filters[0] = ExpatFilter_New(state, &builder_handlers,
                               ExpatFilter_HANDLER_TYPE, NULL);
  if (filters[0] == NULL)
    return NULL;
  reader = ExpatReader_New(filters, 1);
  if (reader == NULL) {
    ExpatFilter_Del(filters[0]);
    return NULL;
  }
  return reader;
}

static PyObject *builder_parse(PyObject *inputSource, ParseFlags flags,
                               NodeFactories *factories, int asEntity,
                               PyObject *namespaces)
{
  ParserState *state;
  PyObject *result;
  int gc_enabled;
  ExpatStatus status;

#ifdef DEBUG_PARSER
  FILE *stream = PySys_GetFile("stderr", stderr);
  PySys_WriteStderr("builder_parse(source=");
  PyObject_Print(inputSource, stream, 0);
  PySys_WriteStderr(", flags=%d, factories=%p, asEntity=%d, namespaces=",
                    flags, factories, asEntity);
  PyObject_Print(namespaces, stream, 0);
  PySys_WriteStderr("\n");
#endif
  /* Takes ownership of `document` */
  state = ParserState_New(factories);
  if (state == NULL)
    return NULL;

  state->reader = create_reader(state);
  if (state->reader == NULL) {
    ParserState_Del(state);
    return NULL;
  }

  /* Disable GC (if enabled) while building the DOM tree */
  result = PyObject_Call(gc_isenabled_function, empty_args_tuple, NULL);
  if (result == NULL)
    goto finally;
  gc_enabled = PyObject_IsTrue(result);
  Py_DECREF(result);
  if (gc_enabled) {
    result = PyObject_Call(gc_disable_function, empty_args_tuple, NULL);
    if (result == NULL)
      goto finally;
    Py_DECREF(result);
  }

  Expat_SetValidation(state->reader, flags == PARSE_FLAGS_VALIDATE);
  Expat_SetParamEntityParsing(state->reader, flags != PARSE_FLAGS_STANDALONE);

  if (asEntity)
    status = ExpatReader_ParseEntity(state->reader, inputSource, namespaces);
  else
    status = ExpatReader_Parse(state->reader, inputSource);

  if (gc_enabled) {
    result = PyObject_Call(gc_enable_function, empty_args_tuple, NULL);
    if (result == NULL)
      goto finally;
    Py_DECREF(result);
  }

  /* save off the created document */
  if (status == EXPAT_STATUS_OK)
    result = (PyObject *)state->owner_document;
  else
    result = NULL;

finally:
  ExpatReader_Del(state->reader);
  ParserState_Del(state);
#ifdef DEBUG_PARSER
  PySys_WriteStderr("builder_parse() => ");
  PyObject_Print(result, PySys_GetFile("stderr", stderr), 0);
  PySys_WriteStderr("\n");
#endif
  return result;
}

PyObject *Domlette_Parse(PyObject *self, PyObject *args, PyObject *kw)
{
  static char *kwlist[] = {"source", "flags", "node_factories", NULL};
  PyObject *source, *node_factories=NULL;
  int flags=default_parse_flags;
  NodeFactories *factories=NULL;
  PyObject *result;

  if (!PyArg_ParseTupleAndKeywords(args, kw, "O|iO:parse", kwlist,
                                   &source, &flags, &node_factories))
    return NULL;

  if (node_factories && node_factories != Py_None) {
    factories = NodeFactories_New(node_factories);
    if (factories == NULL)
      return NULL;
  }

  result = builder_parse(source, flags, factories, 0, NULL);

  if (factories != NULL)
    NodeFactories_Del(factories);

  return result;
}

PyObject *Domlette_ParseFragment(PyObject *self, PyObject *args, PyObject *kw)
{
  static char *kwlist[] = {"source", "namespaces", "node_factories", NULL};
  PyObject *source, *namespaces=NULL, *node_factories=NULL;
  NodeFactories *factories=NULL;
  PyObject *result;

  if (!PyArg_ParseTupleAndKeywords(args, kw, "O|OO:parse_fragment", kwlist,
                                   &source, &namespaces, &node_factories))
    return NULL;

  if (node_factories && node_factories != Py_None) {
    factories = NodeFactories_New(node_factories);
    if (factories == NULL)
      return NULL;
  }

  result = builder_parse(source, PARSE_FLAGS_STANDALONE, factories, 1,
                         namespaces);

  if (factories != NULL)
    NodeFactories_Del(factories);

  return result;
}

/** Module Interface **************************************************/

int DomletteBuilder_Init(PyObject *module)
{
  PyObject *import;

  if (Expat_IMPORT == NULL) return -1;

  xmlns_string = XmlString_FromASCII("xmlns");
  if (xmlns_string == NULL) return -1;

  empty_args_tuple = PyTuple_New((Py_ssize_t)0);
  if (empty_args_tuple == NULL) return -1;

  import = PyImport_ImportModule("gc");
  if (import == NULL) return -1;
#define GET_GC_FUNC(NAME)                                       \
  gc_##NAME##_function = PyObject_GetAttrString(import, #NAME); \
  if (gc_##NAME##_function == NULL) {                           \
    Py_DECREF(import);                                          \
    return -1;                                                  \
  }
  GET_GC_FUNC(enable);
  GET_GC_FUNC(disable);
  GET_GC_FUNC(isenabled);
  Py_DECREF(import);
#undef GET_GC_FUNC

#define ADD_CONSTANT(name) \
  if (PyModule_AddIntConstant(module, #name, name) < 0) return -1
  ADD_CONSTANT(PARSE_FLAGS_STANDALONE);
  ADD_CONSTANT(PARSE_FLAGS_EXTERNAL_ENTITIES);
  ADD_CONSTANT(PARSE_FLAGS_VALIDATE);

  return 0;
}

void DomletteBuilder_Fini(void)
{
  Py_DECREF(xmlns_string);
  Py_DECREF(empty_args_tuple);
  Py_DECREF(gc_enable_function);
  Py_DECREF(gc_disable_function);
  Py_DECREF(gc_isenabled_function);
}
