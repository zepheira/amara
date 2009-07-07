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
  ExpatReader *reader;

  Context *context;
  Context *free_context;

  PyObject *new_namespaces;

  PyObject *entity_factory;
  PyObject *element_factory;
  PyObject *text_factory;
  PyObject *processing_instruction_factory;
  PyObject *comment_factory;

  EntityObject *owner_document;
} ParserState;

typedef enum {
  PARSE_FLAGS_STANDALONE = 0,
  PARSE_FLAGS_EXTERNAL_ENTITIES,
  PARSE_FLAGS_VALIDATE,
} ParseFlags;

ParseFlags default_parse_flags = PARSE_FLAGS_EXTERNAL_ENTITIES;

static PyObject *empty_args_tuple;
static PyObject *empty_string;
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

/** ParserState ********************************************************/

Py_LOCAL_INLINE(ParserState *)
ParserState_New(PyObject *entity_factory)
{
  ParserState *self = PyMem_New(ParserState, 1);
  if (self == NULL) {
    PyErr_NoMemory();
  } else {
    memset(self, 0, sizeof(ParserState));
    self->new_namespaces = PyDict_New();
    if (self->new_namespaces == NULL) {
      PyMem_Free(self);
      return NULL;
    }
    if (entity_factory) {
      self->entity_factory = entity_factory;
      Py_INCREF(entity_factory);
    }
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
  Py_CLEAR(self->entity_factory);
  Py_CLEAR(self->element_factory);
  Py_CLEAR(self->text_factory);
  Py_CLEAR(self->processing_instruction_factory);
  Py_CLEAR(self->comment_factory);
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

Py_LOCAL_INLINE(int)
load_factory(PyObject *obj, char *name, PyTypeObject *type, PyObject **pslot)
{
  PyObject *factory = PyObject_GetAttrString(obj, name);
  if (factory == NULL)
    return 0;
  if (factory == (PyObject *)type)
    Py_DECREF(factory);
  else
    *pslot = factory;
  return 1;
}

static ExpatStatus
builder_StartDocument(void *userState)
{
  ParserState *state = (ParserState *)userState;
  PyObject *uri;
  EntityObject *document;

#ifdef DEBUG_PARSER
  fprintf(stderr, "--- builder_StartDocument(%p)\n", state);
#endif
  uri = ExpatReader_GetBase(state->reader);
  if (state->entity_factory) {
    PyObject *obj = PyObject_CallFunction(state->entity_factory, "N", uri);
    if (obj) {
      if (Entity_Check(obj)) {
        /* populate the remaining factory callables */
        if (!load_factory(obj, "xml_element_factory", &DomletteElement_Type,
                          &state->element_factory))
          goto factory_error;
        if (!load_factory(obj, "xml_text_factory", &DomletteText_Type,
                          &state->text_factory))
          goto factory_error;
        if (!load_factory(obj, "xml_processing_instruction_factory",
                          &DomletteProcessingInstruction_Type,
                          &state->processing_instruction_factory))
          goto factory_error;
        if (!load_factory(obj, "xml_comment_factory", &DomletteComment_Type,
                          &state->comment_factory))
          goto factory_error;
      } else {
        PyErr_Format(PyExc_TypeError,
                     "entity_factory should return entity, not %s",
                     obj->ob_type->tp_name);
       factory_error:
        Py_DECREF(obj);
        return EXPAT_STATUS_ERROR;
      }
    }
    document = Entity(obj);
  } else {
    document = Entity_New(uri);
    Py_DECREF(uri);
  }
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
  switch (_Container_SetChildren(context->node, context->children,
                                 context->children_size)) {
    case 0:
      break;
    case -1:
      ParserState_FreeContext(state);
    default:
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

  if (uri == Py_None)
    uri = empty_string;
  if (PyDict_SetItem(state->new_namespaces, prefix, uri) < 0)
    return EXPAT_STATUS_ERROR;

  return EXPAT_STATUS_OK;
}

static ExpatStatus
builder_StartElement(void *userState, ExpatName *name,
                     ExpatAttribute atts[], size_t natts)
{
  ParserState *state = (ParserState *)userState;
  PyObject *attribute_factory=NULL;
  ElementObject *elem=NULL;
  Py_ssize_t i;
  PyObject *key, *value;

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

  if (state->element_factory) {
    elem = (ElementObject *)
      PyObject_CallFunctionObjArgs(state->element_factory, name->namespaceURI,
                                   name->qualifiedName, NULL);
    if (elem == NULL)
      return EXPAT_STATUS_ERROR;
    if (!Element_Check(elem)) {
      PyErr_Format(PyExc_TypeError,
                   "xml_element_factory should return element, not %s",
                   elem->ob_type->tp_name);
      Py_DECREF(elem);
      return EXPAT_STATUS_ERROR;
    }
  } else {
    elem = Element_New(name->namespaceURI, name->qualifiedName,
                       name->localName);
    if (elem == NULL)
      return EXPAT_STATUS_ERROR;
  }

  /** namespaces *******************************************************/

  /* new_namespaces is a dictionary where key is the prefix and value
   * is the uri.
   */
  if (((PyDictObject *)state->new_namespaces)->ma_used) {
    i = 0;
    while (PyDict_Next(state->new_namespaces, &i, &key, &value)) {
      NamespaceObject *nsnode = Element_AddNamespace(elem, key, value);
      if (nsnode == NULL) {
        Py_DECREF(elem);
        Py_XDECREF(attribute_factory);
        return EXPAT_STATUS_ERROR;
      }
      Py_DECREF(nsnode);
    }
    /* make sure children don't set these namespaces */
    PyDict_Clear(state->new_namespaces);
  }

  /** attributes *******************************************************/

  for (i = 0; i < (Py_ssize_t)natts; i++) {
    AttrObject *attr = Element_AddAttribute(elem, atts[i].namespaceURI,
                                            atts[i].qualifiedName,
                                            atts[i].localName, atts[i].value);
    if (attr == NULL) {
      Py_DECREF(elem);
      return EXPAT_STATUS_ERROR;
    }
    /* save the attribute type as well (for getElementById) */
    Attr_SET_TYPE(attr, atts[i].type);
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
  switch (_Container_SetChildren(node, context->children,
                                 context->children_size)) {
    case 0:
      break;
    case -1:
      ParserState_FreeContext(state);
    default:
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

  attr = Element_AddAttribute((ElementObject *)state->context->node,
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
  NodeObject *node;

#ifdef DEBUG_PARSER
  fprintf(stderr, "--- builder_Characters(data=");
  PyObject_Print(data, stderr, 0);
  fprintf(stderr, ")\n");
#endif

  if (state->text_factory) {
    node = (NodeObject *)PyObject_CallFunctionObjArgs(state->text_factory,
                                                      data, NULL);
    if (node == NULL)
      return EXPAT_STATUS_ERROR;
    if (!Text_Check(node)) {
      PyErr_Format(PyExc_TypeError,
                   "xml_text_factory should return text, not %s",
                   node->ob_type->tp_name);
      Py_DECREF(node);
      return EXPAT_STATUS_ERROR;
    }
  } else {
    node = (NodeObject *)Text_New(data);
    if (node == NULL)
      return EXPAT_STATUS_ERROR;
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
  NodeObject *node;

#ifdef DEBUG_PARSER
  fprintf(stderr, "--- builder_ProcessingInstruction(target=");
  PyObject_Print(target, stderr, 0);
  fprintf(stderr, ", data=");
  PyObject_Print(data, stderr, 0);
  fprintf(stderr, ")\n");
#endif

  if (state->processing_instruction_factory) {
    node = (NodeObject *)
      PyObject_CallFunctionObjArgs(state->processing_instruction_factory,
                                   target, data, NULL);
    if (node == NULL)
      return EXPAT_STATUS_ERROR;
    if (!Text_Check(node)) {
      PyErr_Format(PyExc_TypeError,
                   "xml_processing_instruction_factory should return "
                   "processing_instruction, not %s",
                   node->ob_type->tp_name);
      Py_DECREF(node);
      return EXPAT_STATUS_ERROR;
    }
  } else {
    node = (NodeObject *)ProcessingInstruction_New(target, data);
    if (node == NULL)
      return EXPAT_STATUS_ERROR;
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
  NodeObject *node;

#ifdef DEBUG_PARSER
  fprintf(stderr, "--- builder_Comment(data=");
  PyObject_Print(data, stderr, 0);
  fprintf(stderr, ")\n");
#endif

  if (state->comment_factory) {
    node = (NodeObject *)PyObject_CallFunctionObjArgs(state->comment_factory,
                                                      data, NULL);
    if (node == NULL)
      return EXPAT_STATUS_ERROR;
    if (!Text_Check(node)) {
      PyErr_Format(PyExc_TypeError,
                   "xml_comment_factory should return comment, not %s",
                   node->ob_type->tp_name);
      Py_DECREF(node);
      return EXPAT_STATUS_ERROR;
    }
  } else {
    node = (NodeObject *)Comment_New(data);
    if (node == NULL)
      return EXPAT_STATUS_ERROR;
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

  if (PyDict_SetItem(Entity_GET_UNPARSED_ENTITIES(state->owner_document),
                     name, systemId))
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
                               PyObject *entity_factory, int asEntity,
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
  PySys_WriteStderr(", flags=%d, entity_factory=", flags);
  PyObject_Print(entity_factory, stream, 0);
  PySys_WriteStderr(", asEntity=%d, namespaces=", asEntity);
  PyObject_Print(namespaces, stream, 0);
  PySys_WriteStderr("\n");
#endif
  state = ParserState_New(entity_factory);
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
  static char *kwlist[] = {"source", "flags", "entity_factory", NULL};
  PyObject *source, *entity_factory=NULL;
  int flags=default_parse_flags;

  if (!PyArg_ParseTupleAndKeywords(args, kw, "O|iO:parse", kwlist,
                                   &source, &flags, &entity_factory))
    return NULL;
  if (entity_factory == Py_None)
    entity_factory = NULL;

  return builder_parse(source, flags, entity_factory, 0, NULL);
}

PyObject *Domlette_ParseFragment(PyObject *self, PyObject *args, PyObject *kw)
{
  static char *kwlist[] = {"source", "namespaces", "entity_factory", NULL};
  PyObject *source, *namespaces=NULL, *entity_factory=NULL;

  if (!PyArg_ParseTupleAndKeywords(args, kw, "O|OO:parse_fragment", kwlist,
                                   &source, &namespaces, &entity_factory))
    return NULL;
  if (namespaces == Py_None)
    namespaces = NULL;
  if (entity_factory == Py_None)
    entity_factory = NULL;

  return builder_parse(source, PARSE_FLAGS_STANDALONE, entity_factory, 1,
                       namespaces);
}

/** Module Interface **************************************************/

int DomletteBuilder_Init(PyObject *module)
{
  PyObject *import;

  if (Expat_IMPORT == NULL) return -1;

  empty_args_tuple = PyTuple_New(0);
  if (empty_args_tuple == NULL) return -1;

  empty_string = XmlString_FromASCII("");
  if (empty_string == NULL) return -1;

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
  Py_DECREF(empty_args_tuple);
  Py_DECREF(empty_string);
  Py_DECREF(gc_enable_function);
  Py_DECREF(gc_disable_function);
  Py_DECREF(gc_isenabled_function);
}
