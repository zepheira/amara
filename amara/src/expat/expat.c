/***********************************************************************/
/* amara/src/expat/expat.c                                             */
/***********************************************************************/

static char module_doc[] = "\
Expat wrapper library";

#include "Python.h"
#include "structmember.h"
#define XmlString_SHARED
#include "xmlstring.h"
#include "cStringIO.h"
#include "lib/expat.h"          /* Expat library */
#include "xmlchar.h"            /* XML_Char to PyUnicode support */
#include "stack.h"              /* Stack_* routines */
#include "hash_table.h"         /* XML_Char-keyed HashTable */
#include "content_model.h"      /* basic content model */
#include "expat_interface.h"    /* exported ExpatReader interface */
#include "filter.h"             /* pattern-based event filtering */
#include "input_source.h"
#include "attributes.h"
#include "reader.h"             /* Python interface */
#include "sax_filter.h"         /* Python SAX interface */
#include "util.h"
#include "debug.h"              /* debugging support */

/** Private Interface *************************************************/

/*
 * Alignment of addresses returned to the user. 8-bytes alignment works
 * on most current architectures (with 32-bit or 64-bit address busses).
 *
 * You shouldn't change this unless you know what you are doing.
 */
#define ALIGNMENT       8       /* must be 2^N */
#define ALIGNMENT_MASK  (ALIGNMENT - 1)
#define ROUND_UP(x)     (((x) + (ALIGNMENT - 1)) & ~(ALIGNMENT - 1))

/* using a 64K buffer helps read performance for large documents */
#define EXPAT_BUFSIZ   65536
/* 8K buffer should be plenty for most documents (it does resize if needed) */
#define XMLCHAR_BUFSIZ 8192

static PyObject *read_string;
static PyObject *empty_string;
static PyObject *asterisk_string;
static PyObject *space_string;
static PyObject *preserve_string;
static PyObject *default_string;
static PyObject *id_string;
static PyObject *xml_namespace_string;
static PyObject *xml_space_string;
static PyObject *xml_base_string;
static PyObject *xml_lang_string;
static PyObject *base_string;
static PyObject *lang_string;
static PyObject *unicode_space_char;

static PyObject *empty_event;
static PyObject *content_model_empty;
static PyObject *content_model_any;
static PyObject *content_model_pcdata;
static PyObject *attribute_decl_implied;
static PyObject *attribute_decl_required;
static PyObject *attribute_decl_fixed;

static PyObject *absolutize_function;

static PyObject *ReaderError;
static PyObject *IriError;
static PyObject *IriError_RESOURCE_ERROR;

static PyObject *expat_library_error;

static XML_Memory_Handling_Suite expat_memsuite = {
  malloc, realloc, free
};

typedef struct XML_Handlers {
  XML_StartElementHandler start_element;
  XML_EndElementHandler end_element;
  XML_CharacterDataHandler character_data;
  XML_ProcessingInstructionHandler processing_instruction;
  XML_CommentHandler comment;
  XML_StartNamespaceDeclHandler start_namespace;
  XML_EndNamespaceDeclHandler end_namespace;
  XML_SkippedEntityHandler skipped_entity;
  XML_StartCdataSectionHandler start_cdata;
  XML_EndCdataSectionHandler end_cdata;
  XML_ElementDeclHandler element_decl;
  XML_AttlistDeclHandler attlist_decl;
  XML_EntityDeclHandler entity_decl;
  XML_NotationDeclHandler notation_decl;
  struct XML_Handlers *next;
} XML_Handlers;

typedef struct DTD {
  PyObject *validator;          /* ValidatorObject */
  PyObject *root_element;       /* PyUnicodeObject */
  PyObject *ids;                /* PyDictObject */
  PyObject *entities;           /* PyDictObject */
  PyObject *notations;          /* PyDictObject */
  PyObject *used_ids;           /* PyListObject */
  PyObject *used_elements;      /* PyDictObject */
  PyObject *used_notations;     /* PyDictObject */
} DTD;

struct ExpatFilterStruct {
  void *arg;
  ExpatHandlers handlers;
  unsigned long flags;
  FilterCriterion *criteria;
};

struct FilterState {
  struct FilterState *next;
  int active;
  int depth;
  StateTable *state_table;
  StateId accepting;
  ExpatFilter *filter;
};

typedef struct Context {
  struct Context *next;
  XML_Parser parser;            /* the Expat parser */
  XML_Handlers *handlers;       /* the Expat handlers */
  PyObject *source;             /* the Python InputSource object */
  PyObject *uri;                /* the URI of the current document */
  PyObject *stream;             /* the stream for the current document */
  PyObject *encoding;           /* the encoding of the stream */
  unsigned long flags;          /* feature flags */
  PyObject *xml_base;
  PyObject *xml_lang;
  DTD *dtd;
  FilterState *filters;         /* extra stuff for event filtering */
} Context;

/* This flag marks that certain infoset properties need to be adjusted for
 * a particular included entity. */
#define EXPAT_FLAG_INFOSET_FIXUP        (1L<<0)

/* This flag indicates that DTD validation should be performed. */
#define EXPAT_FLAG_VALIDATE             (1L<<1)

#define Expat_HasFlag(p,f) (((p)->context->flags & (f)) == (f))
#define Expat_SetFlag(p,f) ((p)->context->flags |= (f))
#define Expat_ClearFlag(p,f) ((p)->context->flags &= ~(f))
#define Expat_DumpFlags(p) do {                                 \
  if ((p)->context->flags) {                                    \
    int nflags = 0;                                             \
    PySys_WriteStderr("  Flags: ");                             \
    if (Expat_HasFlag((p), EXPAT_FLAG_VALIDATE))                \
      if (nflags++) PySys_WriteStderr(" | ");                   \
      PySys_WriteStderr("EXPAT_FLAG_VALIDATE");                 \
    }                                                           \
    if (Expat_HasFlag((p), EXPAT_FLAG_INFOSET_FIXUP))           \
      if (nflags++) PySys_WriteStderr(" | ");                   \
      PySys_WriteStderr("EXPAT_FLAG_INFOSET_FIXUP");            \
    }                                                           \
    PySys_WriteStderr("\n");                                    \
  }                                                             \
} while(0)


enum NameTestType {
  ELEMENT_TEST,
  NAMESPACE_TEST,
  EXPANDED_NAME_TEST,
};

typedef struct {
  enum NameTestType test_type;
  PyObject *test_namespace;
  PyObject *test_name;
  PyObject *preserve_flag;
} WhitespaceRule;

typedef struct {
  Py_ssize_t size;
  WhitespaceRule items[1];
} WhitespaceRules;

struct ExpatReaderStruct {
  /* event filtering */
  ExpatFilter *filters;         /* array of event filters */
  size_t filters_size;

  /* caching members */
  HashTable *name_cache;        /* element name parts */
  HashTable *unicode_cache;     /* XMLChar to unicode mapping */
  ExpatAttribute *attrs;        /* reusable attributes list */
  size_t attrs_size;            /* allocated size of attributes list */

  /* character data buffering */
  XML_Char *buffer;             /* buffer used for accumulating characters */
  size_t buffer_size;           /* size of buffer (in XML_Char units) */
  size_t buffer_used;           /* buffer units in use */

  /* parsing options */
  unsigned long flags;

  /* parsing data */
  Context *context;             /* stack of parser contexts */
  Stack *xml_base_stack;        /* current base URI w/xml:base support */
  Stack *xml_lang_stack;        /* XInclude language fixup (xml:lang) */
  Stack *xml_space_stack;       /* indicates xml:space='preserve' */

  WhitespaceRules *whitespace_rules;  /* array of stripping rules */
  Stack *preserve_whitespace_stack;   /* whitespace stripping allowed */
};

#define ExpatReader_HasFlag(p,f) ((((ExpatReader *)(p))->flags & (f)) == (f))
#define ExpatReader_SetFlag(p,f) (((ExpatReader *)(p))->flags |= (f))
#define ExpatReader_ClearFlag(p,f) (((ExpatReader *)(p))->flags &= ~(f))

#define ExpatReader_DTD_VALIDATION       (1L<<0)
#define ExpatReader_PARAM_ENTITY_PARSING (1L<<1)

#define ExpatReader_INFOSET_HANDLERS     (1L<<2)
#define ExpatReader_ENTITY_RESOLVER      (1L<<3)
#define ExpatReader_ERROR_HANDLERS       (1L<<4)
#define ExpatReader_DTD_DECLARATIONS     (1L<<5)

/** DTD ***************************************************************/

Py_LOCAL(DTD *) DTD_New(void)
{
  DTD *dtd;

  dtd = (DTD *) PyObject_MALLOC(sizeof(DTD));
  if (dtd == NULL) {
    PyErr_NoMemory();
  } else {
    dtd->validator = Validator_New();
    if (dtd->validator == NULL) {
      PyObject_FREE(dtd);
      return NULL;
    }
    dtd->ids = PyDict_New();
    if (dtd->ids == NULL) {
      Py_DECREF(dtd->validator);
      PyObject_FREE(dtd);
      return NULL;
    }
    dtd->entities = PyDict_New();
    if (dtd->entities == NULL) {
      Py_DECREF(dtd->ids);
      Py_DECREF(dtd->validator);
      PyObject_FREE(dtd);
      return NULL;
    }
    dtd->notations = PyDict_New();
    if (dtd->notations == NULL) {
      Py_DECREF(dtd->entities);
      Py_DECREF(dtd->ids);
      Py_DECREF(dtd->validator);
      PyObject_FREE(dtd);
      return NULL;
    }
    dtd->used_ids = PyList_New(0);
    if (dtd->used_ids == NULL) {
      Py_DECREF(dtd->notations);
      Py_DECREF(dtd->entities);
      Py_DECREF(dtd->ids);
      Py_DECREF(dtd->validator);
      PyObject_FREE(dtd);
      return NULL;
    }
    dtd->used_elements = PyDict_New();
    if (dtd->used_elements == NULL) {
      Py_DECREF(dtd->used_ids);
      Py_DECREF(dtd->notations);
      Py_DECREF(dtd->entities);
      Py_DECREF(dtd->ids);
      Py_DECREF(dtd->validator);
      PyObject_FREE(dtd);
      return NULL;
    }
    dtd->used_notations = PyDict_New();
    if (dtd->used_notations == NULL) {
      Py_DECREF(dtd->used_elements);
      Py_DECREF(dtd->used_ids);
      Py_DECREF(dtd->notations);
      Py_DECREF(dtd->entities);
      Py_DECREF(dtd->ids);
      Py_DECREF(dtd->validator);
      PyObject_FREE(dtd);
      return NULL;
    }
    dtd->root_element = Py_None;
  }
  return dtd;
}

Py_LOCAL(void) DTD_Del(DTD *dtd)
{
  Py_DECREF(dtd->used_notations);
  Py_DECREF(dtd->used_elements);
  Py_DECREF(dtd->used_ids);
  Py_DECREF(dtd->notations);
  Py_DECREF(dtd->entities);
  Py_DECREF(dtd->ids);
  Py_DECREF(dtd->validator);
  PyObject_FREE(dtd);
}

/** FilterState *******************************************************/

FilterState *FilterState_New(size_t size) {
  return NULL;
}

void FilterState_Del(FilterState *state) {
}

/** ExpatFilter *******************************************************/

ExpatFilter *
ExpatFilter_New(void *arg, ExpatHandlers *handlers, unsigned long flags,
                FilterCriterion *criteria)
{
  ExpatFilter *filter;
  filter = PyMem_New(ExpatFilter, 1);
  if (filter != NULL) {
    filter->arg = arg;
    if (handlers != NULL) {
      memcpy(&filter->handlers, handlers, sizeof(ExpatHandlers));
    }
    filter->flags = flags;
    filter->criteria = criteria;
  } else {
    PyErr_NoMemory();
  }
  Debug_Return(ExpatFilter_New, filter);
  return filter;
}

void
ExpatFilter_Del(ExpatFilter *filter)
{
  Debug_FunctionCall(ExpatFilter_Del, filter);
  PyMem_Del(filter);
}

Py_LOCAL(FilterState *)
ExpatFilter_NewState(ExpatFilter *filter)
{
  FilterState *state;

  Debug_FunctionCall(ExpatFilter_NewState, filter);

  state = PyMem_New(FilterState, 1);
  if (state != NULL) {
    memset(state, 0, sizeof(FilterState));
    state->active = 1;
    state->filter = filter;
  } else {
    PyErr_NoMemory();
  }
  Debug_Return(ExpatFilter_NewState, state);
  return state;
}

#define FUNCTION_TEMPLATE(NAME, HANDLER, PROTO, ARGS, DEPTH) \
Py_LOCAL_INLINE(ExpatStatus) \
ExpatFilter_##NAME PROTO \
{ \
  ExpatStatus status = EXPAT_STATUS_OK; \
  /* For each active (criteria have matched) filter, call the handler. */ \
  while (state) { \
    if (state->active) { \
      ExpatFilter *filter = state->filter; \
      ExpatHandlers handlers = filter->handlers; \
      DEPTH; \
      if (handlers.HANDLER) { \
        status = handlers.HANDLER ARGS; \
        if (status != EXPAT_STATUS_OK) break; \
      } \
      if (ExpatFilter_HasFlag(filter, ExpatFilter_HANDLER_TYPE)) break; \
    } \
    state = state->next; \
  } \
  return status; \
}

#define PROTO0 FilterState *state
#define PROTO1 PROTO0, PyObject *arg1
#define PROTO2 PROTO1, PyObject *arg2
#define PROTO3 PROTO2, PyObject *arg3
#define PROTO4 PROTO3, PyObject *arg4
#define PROTO5 PROTO4, PyObject *arg5

#define ARGS0 filter->arg
#define ARGS1 ARGS0, arg1
#define ARGS2 ARGS1, arg2
#define ARGS3 ARGS2, arg3
#define ARGS4 ARGS3, arg4
#define ARGS5 ARGS4, arg5

#define FUNCTION_OBJ_ARGS(NAME, HANDLER, NARGS) \
  FUNCTION_TEMPLATE(NAME, HANDLER, (PROTO##NARGS), (ARGS##NARGS), ;)

FUNCTION_TEMPLATE(StartDocument, start_document,
                  (PROTO0), (ARGS0), state->depth++)
FUNCTION_TEMPLATE(EndDocument, end_document,
                  (PROTO0), (ARGS0), state->depth--)
FUNCTION_TEMPLATE(StartElement, start_element,
                  (PROTO0, ExpatName *name, ExpatAttribute atts[], size_t natts),
                  (ARGS0, name, atts, natts), state->depth++)
FUNCTION_TEMPLATE(EndElement, end_element,
                  (PROTO0, ExpatName *name), (ARGS0, name), state->depth--)
FUNCTION_OBJ_ARGS(Characters, characters, 1)
FUNCTION_OBJ_ARGS(IgnorableWhitespace, ignorable_whitespace, 1)
FUNCTION_OBJ_ARGS(ProcessingInstruction, processing_instruction, 2)
FUNCTION_OBJ_ARGS(Comment, comment, 1)
FUNCTION_OBJ_ARGS(StartNamespaceDecl, start_namespace_decl, 2)
FUNCTION_OBJ_ARGS(EndNamespaceDecl, end_namespace_decl, 1)
FUNCTION_OBJ_ARGS(StartDoctypeDecl, start_doctype_decl, 3)
FUNCTION_OBJ_ARGS(EndDoctypeDecl, end_doctype_decl, 0)
FUNCTION_OBJ_ARGS(StartCdataSection, start_cdata_section, 0)
FUNCTION_OBJ_ARGS(EndCdataSection, end_cdata_section, 0)
FUNCTION_OBJ_ARGS(SkippedEntity, skipped_entity, 1)
FUNCTION_OBJ_ARGS(ElementDecl, element_decl, 2)
FUNCTION_OBJ_ARGS(AttributeDecl, attribute_decl, 5)
FUNCTION_OBJ_ARGS(InternalEntityDecl, internal_entity_decl, 2)
FUNCTION_OBJ_ARGS(ExternalEntityDecl, external_entity_decl, 3)
FUNCTION_OBJ_ARGS(UnparsedEntityDecl, unparsed_entity_decl, 4)
FUNCTION_OBJ_ARGS(NotationDecl, notation_decl, 3)

/* ErrorHandler */
FUNCTION_OBJ_ARGS(Warning, warning, 1)
FUNCTION_OBJ_ARGS(Error, error, 1)
FUNCTION_OBJ_ARGS(FatalError, fatal_error, 1)

#undef FUNCTION_TEMPLATE
#undef FUNCTION_OBJ_ARGS
#undef PROTO0
#undef PROTO1
#undef PROTO2
#undef PROTO3
#undef PROTO4
#undef PROTO5
#undef ARGS0
#undef ARGS1
#undef ARGS2
#undef ARGS3
#undef ARGS4
#undef ARGS5

/** Context ***********************************************************/

/* Context objects are used to store all the things that make up the current
 * parsing state.  They are needed to enable the suspend/resume functionality
 * of the Expat XML_Parser since finalization will not happen in a linear
 * fashion.
 */

Py_LOCAL(Context *) Context_New(XML_Parser parser, PyObject *source)
{
  Context *context;

  if (source != Py_None && !InputSource_Check(source)) {
    PyErr_Format(PyExc_TypeError, "expected InputSource or None, not %s",
                 source->ob_type->tp_name);
    return NULL;
  }

  context = (Context *) PyObject_MALLOC(sizeof(Context));
  if (context == NULL) {
    PyErr_NoMemory();
    return NULL;
  }
  memset(context, 0, sizeof(Context));

  context->parser = parser;
  if (source == Py_None) {
    context->source = source;
    context->uri = Py_None;
    context->stream = Py_None;
    context->encoding = Py_None;
  } else {
    context->source = source;
    context->uri = InputSource_GET_BASE_URI(source);
    context->stream = InputSource_GET_BYTE_STREAM(source);
    context->encoding = InputSource_GET_ENCODING(source);
  }
  Py_INCREF(source);
  Py_INCREF(context->uri);
  Py_INCREF(context->stream);
  Py_INCREF(context->encoding);

  return context;
}

/* Deallocate the Context object and its contents */
Py_LOCAL_INLINE(void)
Context_Del(Context *context)
{
  if (context->parser)
    XML_ParserFree(context->parser);
  Py_DECREF(context->source);
  Py_DECREF(context->uri);
  Py_DECREF(context->stream);
  Py_DECREF(context->encoding);
  if (context->dtd)
    DTD_Del(context->dtd);
  if (context->filters)
    FilterState_Del(context->filters);

  PyObject_FREE(context);
}

/* Create a new Context object and set it as the current parsing context */
Py_LOCAL(ExpatStatus)
begin_context(ExpatReader *reader, XML_Parser parser, PyObject *source)
{
  Context *context;
  FilterState *state;
  size_t i;

  context = Context_New(parser, source);

  Debug_Return(begin_context, context);

  if (context == NULL) return EXPAT_STATUS_ERROR;

  /* Make it the active context */
  context->next = reader->context;
  reader->context = context;

  /* propagate DTD parsing flag to the context */
  if (ExpatReader_HasFlag(reader, ExpatReader_DTD_VALIDATION)) {
    Expat_SetFlag(reader, EXPAT_FLAG_VALIDATE);
  }

  /* create the FilterState for each of the defined filters */
  for (state = NULL, i = 0; i < reader->filters_size; i++) {
    ExpatFilter *filter = &reader->filters[i];
    if (state) {
      state->next = ExpatFilter_NewState(filter);
      state = state->next;
    } else {
      state = ExpatFilter_NewState(filter);
      context->filters = state;
    }
    if (state == NULL) {
      Context_Del(context);
      return EXPAT_STATUS_ERROR;
    }
  }

  /* Only perform infoset fixup for included entities. */
  /* context->next == NULL when starting with a document, */
  /* context->next->uri == Py_None when starting with a entity. */
  if (context->next != NULL && context->next->uri != Py_None) {
#if defined(DEBUG_XINCLUDE)
    fprintf(stderr, "      Setting EXPAT_FLAG_INFOSET_FIXUP\n");
#endif
    Expat_SetFlag(reader, EXPAT_FLAG_INFOSET_FIXUP);
    context->xml_base = Stack_PEEK(reader->xml_base_stack);
    context->xml_lang = Stack_PEEK(reader->xml_lang_stack);
  }

  /* Set initial values for the xml:* attributes */
  /* xml:base="<document-URI>" */
  if (Stack_Push(reader->xml_base_stack, context->uri) == -1) {
    Context_Del(context);
    return EXPAT_STATUS_ERROR;
  }
  /* xml:lang="" */
  if (Stack_Push(reader->xml_lang_stack, Py_None) == -1) {
    Context_Del(context);
    return EXPAT_STATUS_ERROR;
  }
  /* xml:space="default" */
  if (Stack_Push(reader->xml_space_stack, Py_False) == -1) {
    Context_Del(context);
    return EXPAT_STATUS_ERROR;
  }

  return EXPAT_STATUS_OK;
}

/* Switch to previous parsing context and deallocate the current one */
Py_LOCAL_INLINE(void)
end_context(ExpatReader *reader)
{
  Context *context;
  PyObject *temp;

  Debug_ParserFunctionCall(end_context, reader);

  context = reader->context;
  if (context) {
    temp = Stack_Pop(reader->xml_space_stack);
    Py_DECREF(temp);

    temp = Stack_Pop(reader->xml_lang_stack);
    Py_DECREF(temp);

    temp = Stack_Pop(reader->xml_base_stack);
    Py_DECREF(temp);

    reader->context = context->next;
    Context_Del(context);
  }
}


/* Deallocate ALL Contexts that exist */
Py_LOCAL_INLINE(void)
destroy_contexts(ExpatReader *reader)
{
  Debug_ParserFunctionCall(destroy_contexts, reader);

  while (reader->context) {
    end_context(reader);
  }
}

/** XML_Handlers ******************************************************/

static void expat_StartElement(ExpatReader *reader,
                               const XML_Char *name,
                               const XML_Char **atts);
static void expat_EndElement(ExpatReader *reader,
                             const XML_Char *name);
static void expat_CharacterData(ExpatReader *reader,
                                const XML_Char *s,
                                int len);
static void expat_ProcessingInstruction(ExpatReader *reader,
                                        const XML_Char *target,
                                        const XML_Char *data);
static void expat_Comment(ExpatReader *reader, const XML_Char *data);
static void expat_StartNamespaceDecl(ExpatReader *reader,
                                     const XML_Char *prefix,
                                     const XML_Char *uri);
static void expat_EndNamespaceDecl(ExpatReader *reader,
                                   const XML_Char *prefix);
static void expat_SkippedEntity(ExpatReader *reader,
                                const XML_Char *entityName,
                                int is_parameter_entity);
static void expat_StartDoctypeDecl(ExpatReader *reader,
                                   const XML_Char *name,
                                   const XML_Char *sysid,
                                   const XML_Char *pubid,
                                   int has_internal_subset);
static void expat_EndDoctypeDecl(ExpatReader *reader);
static void expat_StartCdataSection(ExpatReader *reader);
static void expat_EndCdataSection(ExpatReader *reader);
static void expat_ElementDecl(ExpatReader *reader,
                              const XML_Char *name,
                              XML_Content *content);
static void expat_AttlistDecl(ExpatReader *reader,
                              const XML_Char *elname,
                              const XML_Char *attname,
                              const XML_Char *att_type,
                              const XML_Char *dflt,
                              int isrequired);
static void expat_EntityDecl(ExpatReader *reader,
                             const XML_Char *entity_name,
                             int is_parameter_entity,
                             const XML_Char *value,
                             int value_length,
                             const XML_Char *base,
                             const XML_Char *systemId,
                             const XML_Char *publicId,
                             const XML_Char *notationName);
static void expat_NotationDecl(ExpatReader *reader,
                               const XML_Char *notationName,
                               const XML_Char *base,
                               const XML_Char *systemId,
                               const XML_Char *publicId);
static int expat_ExternalEntityRef(XML_Parser parser,
                                   const XML_Char *context,
                                   const XML_Char *base,
                                   const XML_Char *systemId,
                                   const XML_Char *publicId);

static XML_Handlers expat_handlers = {
  (XML_StartElementHandler)expat_StartElement,
  (XML_EndElementHandler)expat_EndElement,
  (XML_CharacterDataHandler)expat_CharacterData,
  (XML_ProcessingInstructionHandler)expat_ProcessingInstruction,
  (XML_CommentHandler)expat_Comment,
  (XML_StartNamespaceDeclHandler)expat_StartNamespaceDecl,
  (XML_EndNamespaceDeclHandler)expat_EndNamespaceDecl,
  (XML_SkippedEntityHandler)expat_SkippedEntity,
  (XML_StartCdataSectionHandler)expat_StartCdataSection,
  (XML_EndCdataSectionHandler)expat_EndCdataSection,
  (XML_ElementDeclHandler)expat_ElementDecl,
  (XML_AttlistDeclHandler)expat_AttlistDecl,
  (XML_EntityDeclHandler)expat_EntityDecl,
  (XML_NotationDeclHandler)expat_NotationDecl,
};

Py_LOCAL_INLINE(XML_Handlers *)
XML_Handlers_New(void)
{
  XML_Handlers *handlers;

  handlers = (XML_Handlers *) PyObject_MALLOC(sizeof(XML_Handlers));
  if (handlers == NULL) {
    PyErr_NoMemory();
  } else {
    memset(handlers, 0, sizeof(XML_Handlers));
  }
  return handlers;
}

Py_LOCAL_INLINE(void)
XML_Handlers_Del(XML_Handlers *handlers)
{
  PyObject_FREE(handlers);
}

Py_LOCAL_INLINE(XML_Handlers *)
XML_Handlers_Copy(XML_Handlers *handlers)
{
  XML_Handlers *new_handlers;

  Debug_FunctionCall(XML_Handlers_Copy, handlers);

  new_handlers = (XML_Handlers *) PyObject_MALLOC(sizeof(XML_Handlers));
  if (new_handlers == NULL) {
    PyErr_NoMemory();
  } else {
    memcpy(new_handlers, handlers, sizeof(XML_Handlers));
    new_handlers->next = NULL;
  }
  return new_handlers;
}

Py_LOCAL_INLINE(void)
setup_handlers(XML_Parser parser, XML_Handlers *handlers)
{
  XML_SetElementHandler(parser,
                        handlers->start_element,
                        handlers->end_element);
  XML_SetCharacterDataHandler(parser, handlers->character_data);
  XML_SetProcessingInstructionHandler(parser,
                                      handlers->processing_instruction);
  XML_SetCommentHandler(parser, handlers->comment);
  XML_SetNamespaceDeclHandler(parser,
                              handlers->start_namespace,
                              handlers->end_namespace);
  XML_SetSkippedEntityHandler(parser, handlers->skipped_entity);
  XML_SetDoctypeDeclHandler(parser,
        (XML_StartDoctypeDeclHandler) expat_StartDoctypeDecl,
        (XML_EndDoctypeDeclHandler) expat_EndDoctypeDecl);
  XML_SetCdataSectionHandler(parser,
                             handlers->start_cdata,
                             handlers->end_cdata);
  XML_SetElementDeclHandler(parser, handlers->element_decl);
  XML_SetAttlistDeclHandler(parser, handlers->attlist_decl);
  XML_SetEntityDeclHandler(parser, handlers->entity_decl);
  XML_SetNotationDeclHandler(parser, handlers->notation_decl);
  XML_SetExternalEntityRefHandler(parser, expat_ExternalEntityRef);
}

Py_LOCAL_INLINE(void)
begin_handlers(ExpatReader *reader, XML_Handlers *handlers)
{
  Context *context = reader->context;

  Debug_ParserFunctionCall(begin_handlers, reader);

  handlers->next = context->handlers;
  context->handlers = handlers;

  setup_handlers(context->parser, handlers);
}

Py_LOCAL_INLINE(void)
end_handlers(ExpatReader *reader)
{
  Context *context = reader->context;
  XML_Handlers *handlers;

  Debug_ParserFunctionCall(end_handlers, reader);

  handlers = context->handlers;
  context->handlers = handlers->next;
  XML_Handlers_Del(handlers);

  setup_handlers(context->parser, context->handlers);
}

/** Error Handling ****************************************************/

Py_LOCAL_INLINE(PyObject *)
create_exception(ExpatReader *reader, const char *errorCode,
                const char *argspec, va_list va)
{
  PyObject *code, *args, *kwords, *exc;

  code = PyObject_GetAttrString(ReaderError, (char *)errorCode);
  if (code == NULL)
    return NULL;
  args = Py_BuildValue("NOii", code, reader->context->uri,
                       XML_GetCurrentLineNumber(reader->context->parser),
                       XML_GetCurrentColumnNumber(reader->context->parser));
  if (args == NULL)
    return NULL;

  if (argspec != NULL) {
    kwords = Py_VaBuildValue((char *)argspec, va);
    if (kwords == NULL) {
      Py_DECREF(args);
      return NULL;
    }
  } else {
    kwords = NULL;
  }
  exc = PyObject_Call(ReaderError, args, kwords);
  Py_DECREF(args);
  Py_XDECREF(kwords);
  return exc;
}

#define stop_parsing(reader) _stop_parsing((reader), __FILE__, __LINE__)
Py_LOCAL(ExpatStatus)
_stop_parsing(ExpatReader *reader, char *filename, int lineno)
{
  XML_Parser parser = reader->context->parser;

  Debug_Print("Parsing stopped at %s:%d\n", filename, lineno);
  if (!PyErr_Occurred()) {
    PyErr_Format(PyExc_SystemError,
                 "%s:%d: Parsing stopped without exception",
                 filename, lineno);
  }

  XML_StopParser(parser, 0);
  /* Clear the handlers so as to prevent inadvertant processing for some
   * callbacks, which include:
   *   - the end element handler for empty elements when stopped in the
   *     start element handler,
   *   - end namespace declaration handler when stopped in the end element
   *     handler,
   * and possibly others.
   */
  XML_SetElementHandler(parser, NULL, NULL);
  XML_SetCharacterDataHandler(parser, NULL);
  XML_SetProcessingInstructionHandler(parser, NULL);
  XML_SetCommentHandler(parser, NULL);
  XML_SetNamespaceDeclHandler(parser, NULL, NULL);
  XML_SetSkippedEntityHandler(parser, NULL);
  XML_SetDoctypeDeclHandler(parser, NULL, NULL);
  XML_SetCdataSectionHandler(parser, NULL, NULL);
  XML_SetElementDeclHandler(parser, NULL);
  XML_SetAttlistDeclHandler(parser, NULL);
  XML_SetEntityDeclHandler(parser, NULL);
  XML_SetNotationDeclHandler(parser, NULL);
  XML_SetExternalEntityRefHandler(parser, NULL);

  return EXPAT_STATUS_ERROR;
}

Py_LOCAL(ExpatStatus)
report_warning(ExpatReader *reader, const char *error, char *argspec, ...)
{
  va_list va;
  PyObject *exception;
  ExpatStatus status;

  Debug_FunctionCall(report_warning, reader);

  va_start(va, argspec);
  exception = create_exception(reader, error, argspec, va);
  va_end(va);
  if (exception == NULL)
    return stop_parsing(reader);

  if (ExpatReader_HasFlag(reader, ExpatReader_ERROR_HANDLERS)) {
    status = ExpatFilter_Warning(reader->context->filters, exception);
  } else {
    status = EXPAT_STATUS_OK;
  }
  Py_DECREF(exception);

  return status;
}

Py_LOCAL(ExpatStatus)
report_error(ExpatReader *reader, const char *error, char *argspec, ...)
{
  va_list va;
  PyObject *exception;
  ExpatStatus status;

  Debug_FunctionCall(report_error, reader);

  va_start(va, argspec);
  exception = create_exception(reader, error, argspec, va);
  va_end(va);
  if (exception == NULL)
    return stop_parsing(reader);

  if (ExpatReader_HasFlag(reader, ExpatReader_ERROR_HANDLERS)) {
    status = ExpatFilter_Error(reader->context->filters, exception);
  } else {
    PyErr_SetObject(ReaderError, exception);
    status = stop_parsing(reader);
  }
  Py_DECREF(exception);

  return status;
}

/** Unicode Interning *************************************************/

/* Routines to minimize the number of PyUnicodeObjects that need to be
 * created for each XML_Char string returned from Expat.
 * This is a memory AND speed improvement.
 */

#define LOOKUP_UNICODE(tbl,s,n) \
  HashTable_Lookup((tbl), (s), (n), NULL, NULL)
#define XMLChar_DecodeSizedInterned(s, n, tbl) \
  LOOKUP_UNICODE((tbl), (s), (n))
#define XMLChar_DecodeInterned(s, tbl) \
  XMLChar_DecodeSizedInterned((s), XMLChar_Len(s), (tbl))


/* If the name from the document had a prefix, then expat name is:
 *   namespace-uri + sep + localName + sep + prefix,
 * otherwise if there is a default namespace:
 *   namespace-uri + sep + localName
 * lastly, it could just be:
 *   localName
 */

#define NAMESPACE_SEP ((const XML_Char)('\f'))

/* An `ExpatName` is really a PyTupleObject that is pointer adjusted
 * to point to the ob_items array. */
#define ExpatName_FROM_OBJECT(ob) ( (ExpatName *) ( (PyVarObject *)(ob)+1 ) )
#define ExpatName_AS_OBJECT(ob)   ( (PyObject *) ( (PyVarObject *)(ob)-1 ) )

Py_LOCAL_INLINE(ExpatName *)
ExpatName_New(void)
{
  PyObject *obj = PyTuple_New(3);
  if (obj == NULL)
    return NULL;
  else
    return ExpatName_FROM_OBJECT(obj);
}

/* callback functions cannot be declared Py_LOCAL */
static PyObject *
split_triplet(const XML_Char *triplet, Py_ssize_t len, void *arg)
{
  HashTable *table = (HashTable *)arg;
  ExpatName *name;
  PyObject *namespaceURI, *localName, *qualifiedName;
  register Py_ssize_t i;
  register Py_ssize_t j;

  name = ExpatName_New();
  if (name == NULL)
    return NULL;

  /* scan for beginning of localName */
  for (i = 0; i < len && triplet[i] != NAMESPACE_SEP; i++);

  if (i == len) {
    /* no namespace-URI found; this is a null-namespace name */
    qualifiedName = LOOKUP_UNICODE(table, triplet, len);
    if (qualifiedName == NULL) {
      Py_DECREF(ExpatName_AS_OBJECT(name));
      return NULL;
    }
    Py_INCREF(Py_None);
    name->namespaceURI = Py_None;
    Py_INCREF(qualifiedName);
    name->localName = qualifiedName;
    Py_INCREF(qualifiedName);
    name->qualifiedName = qualifiedName;
    return ExpatName_AS_OBJECT(name);
  }

  /* found a namespace uri */
  if ((namespaceURI = LOOKUP_UNICODE(table, triplet, i)) == NULL) {
    Py_DECREF(ExpatName_AS_OBJECT(name));
    return NULL;
  }
  i++;

  for (j = i; j < len && triplet[j] != NAMESPACE_SEP; j++);

  if ((localName = LOOKUP_UNICODE(table, triplet + i, j - i)) == NULL) {
    Py_DECREF(ExpatName_AS_OBJECT(name));
    return NULL;
  }
  j++;

  if (j < len) {
    /* a prefix is given as well, build the qualifiedName */
    if ((qualifiedName = PyUnicode_FromUnicode(NULL, len - i)) == NULL) {
      Py_DECREF(ExpatName_AS_OBJECT(name));
      return NULL;
    }

    /* copy the prefix to the qualifiedName string */
    len -= j;
    Py_UNICODE_COPY(PyUnicode_AS_UNICODE(qualifiedName), triplet + j, len);

    /* add the ':' separator */
    PyUnicode_AS_UNICODE(qualifiedName)[len++] = (Py_UNICODE) ':';

    /* add the localName after the ':' to finish the qualifiedName */
    Py_UNICODE_COPY(PyUnicode_AS_UNICODE(qualifiedName) + len,
                    PyUnicode_AS_UNICODE(localName),
                    PyUnicode_GET_SIZE(localName));

  } else {
    /* default namespace, re-use the localName */
    Py_INCREF(localName);
    qualifiedName = localName;
  }

  /* Only qualifiedName is a new reference, the rest are borrowed */
  Py_INCREF(namespaceURI);
  name->namespaceURI = namespaceURI;
  Py_INCREF(localName);
  name->localName = localName;
  name->qualifiedName = qualifiedName;
  return ExpatName_AS_OBJECT(name);
}

Py_LOCAL_INLINE(ExpatName *)
create_name(ExpatReader *reader, const XML_Char *triplet)
{
  PyObject *obj;
  obj = HashTable_Lookup(reader->name_cache, triplet, XMLChar_Len(triplet),
                         split_triplet, reader->unicode_cache);
  if (obj == NULL) return NULL;
  return ExpatName_FROM_OBJECT(obj);
}

Py_LOCAL_INLINE(PyObject *)
intern_string(ExpatReader *reader, PyObject *obj)
{
  PyObject *unicode = PyUnicode_FromObject(obj);
  PyObject *result;
  if (unicode == NULL)
    return NULL;
  result = LOOKUP_UNICODE(reader->unicode_cache,
                          (XML_Char *)PyUnicode_AS_UNICODE(unicode),
                          (size_t)PyUnicode_GET_SIZE(unicode));
  Py_DECREF(unicode);
  return result;
}

/** Whitespace Stripping **********************************************/

Py_LOCAL_INLINE(WhitespaceRules *)
create_whitespace_rules(ExpatReader *reader, PyObject *sequence)
{
  Py_ssize_t i, length;
  size_t nbytes;
  WhitespaceRules *rules;

  if (sequence == NULL) {
    PyErr_BadInternalCall();
    return NULL;
  }

  sequence = PySequence_Tuple(sequence);
  if (sequence == NULL)
    return NULL;
  length = PyTuple_GET_SIZE(sequence);
  assert(length >= 0);
  nbytes = SIZEOF_INT + (sizeof(WhitespaceRule) * (size_t)length);
  rules = (WhitespaceRules *)PyObject_MALLOC(nbytes);
  if (rules == NULL) {
    Py_DECREF(sequence);
    PyErr_NoMemory();
    return NULL;
  }
  memset(rules, '\0', nbytes);
  rules->size = length;

  for (i = 0; i < length; i++) {
    PyObject *namespace_uri, *local_name, *flag;
    if (!PyArg_UnpackTuple(PyTuple_GET_ITEM(sequence, i), NULL, 3, 3,
                           &namespace_uri, &local_name, &flag))
      goto error;
    /* Each strip element specifies a NS and a local name,
       The localname can be a name or *
       If the localname is * then the NS could be None.
       ns:local is a complete match
       ns:* matches any element in the given namespace
       * matches any element.

       NOTE:  There are precedence rules to stripping as (according to XSLT)
       the matches should be treated as node tests.  The precedence is based
       on level of specificity.  This code assumes the list of white space
       rules has already been sorted by precedence.
    */
    switch (PyObject_RichCompareBool(local_name, asterisk_string, Py_EQ)) {
    case 1:
      if (namespace_uri == Py_None) {
        /* rule matches every element */
        rules->items[i].test_type = ELEMENT_TEST;
      } else {
        /* rule matches any element in the target namespace */
        namespace_uri = intern_string(reader, namespace_uri);
        if (namespace_uri == NULL)
          goto error;
        rules->items[i].test_type = NAMESPACE_TEST;
        rules->items[i].test_namespace = namespace_uri;
      }
      break;
    case 0:
      namespace_uri = intern_string(reader, namespace_uri);
      if (namespace_uri == NULL)
        goto error;
      local_name = intern_string(reader, local_name);
      if (local_name == NULL)
        goto error;
      rules->items[i].test_type = EXPANDED_NAME_TEST;
      rules->items[i].test_namespace = namespace_uri;
      rules->items[i].test_name = local_name;
      break;
    default:
      goto error;
    }
    switch (PyObject_IsTrue(flag)) {
    case 1:
      rules->items[i].preserve_flag = Py_False;
      break;
    case 0:
      rules->items[i].preserve_flag = Py_True;
      break;
    default:
      goto error;
    }
  }
  Py_DECREF(sequence);
  return rules;

error:
  PyObject_FREE(rules);
  Py_DECREF(sequence);
  return NULL;
}

Py_LOCAL_INLINE(void)
destroy_whitespace_rules(WhitespaceRules *rules)
{
  /* all test values are borrowed references from the unicode intern table */
  PyObject_FREE(rules);
}

Py_LOCAL_INLINE(PyObject *)
is_whitespace_preserving(ExpatReader *reader, PyObject *namespaceURI,
                         PyObject *localName)
{
  WhitespaceRules *rules = reader->whitespace_rules;
  register WhitespaceRule *rule;
  register size_t size;

  /* NOTE: We can use exact pointer compares as the names are interned */
  if (rules != NULL) {
    for (size = rules->size, rule = rules->items; size > 0; size--, rule++) {
      switch (rule->test_type) {
      case EXPANDED_NAME_TEST:
        if (rule->test_name != localName)
          break;
        /* else, fall through for namespace-uri test */
      case NAMESPACE_TEST:
        if (rule->test_namespace != namespaceURI)
          break;
        /* else, fall through to handle match */
      case ELEMENT_TEST:
        return rule->preserve_flag;
      }
    }
  }
  /* by default, all elements are whitespace-preserving */
  return Py_True;
}

/** Character Data Buffering ******************************************/

/* These routines are used to ensure that all character data is reported
 * as a single logic chunk to the application regardless of how many chunks
 * Expat returns.
 */

Py_LOCAL_INLINE(ExpatStatus)
charbuf_report_error(ExpatReader *reader)
{
  DTD *dtd = reader->context->dtd;
  PyObject *type = Validator_GetCurrentElementType(dtd->validator);
  return report_error(reader, "INVALID_TEXT", "{sO}",
                      "element", ElementType_GET_NAME(type));
}

Py_LOCAL_INLINE(ExpatStatus)
charbuf_callback(ExpatReader *reader, PyObject *data, int is_ws)
{
  Context *context = reader->context;
  ExpatStatus status = EXPAT_STATUS_OK;

  if (Expat_HasFlag(reader, EXPAT_FLAG_VALIDATE)) {
    DTD *dtd = context->dtd;
    switch (Validator_CheckEvent(dtd->validator, content_model_pcdata)) {
    case 1: /* mixed content ok */
      status = ExpatFilter_Characters(context->filters, data);
      if (status == EXPAT_STATUS_ERROR)
        return stop_parsing(reader);
      break;
    case 0: /* element content only */
      /* whitespace is still an error if it occurrs for an empty model */
      switch (is_ws ? Validator_CheckEvent(dtd->validator, empty_event) : 1) {
      case 0: /* element content ok */
        status = ExpatFilter_IgnorableWhitespace(context->filters, data);
        if (status == EXPAT_STATUS_ERROR)
          return stop_parsing(reader);
        break;
      case 1:
        status = charbuf_report_error(reader);
        break;
      default:
        return stop_parsing(reader);
      }
      break;
    default:
      return stop_parsing(reader);
    }
  } else {
    status = ExpatFilter_Characters(context->filters, data);
    if (status == EXPAT_STATUS_ERROR)
      return stop_parsing(reader);
  }
  return status;
}

/* Do not inline as this is called from many of the handler callbacks */
Py_LOCAL(ExpatStatus)
charbuf_flush(ExpatReader *reader)
{
  const XML_Char *str = reader->buffer;
  register size_t len = reader->buffer_used;
  register size_t i;
  PyObject *data;
  ExpatStatus status;

  Debug_ParserFunctionCall(charbuf_flush, reader);

  if (len == 0) return EXPAT_STATUS_OK;

  /* Mark buffer as empty */
  reader->buffer_used = 0;

  /* intern strings that are only whitespace */
  for (i = 0; i < len; i++) {
    XML_Char ch = str[i];
    if (!((ch == 0x09) || (ch == 0x0A) || (ch == 0x0D) || (ch == 0x20))) {
      break;
    }
  }
  if (i == len) {
    /* Only bother creating a PyUnicodeObject from the data if we are
     * going to be preserving it. */
    if (Stack_PEEK(reader->preserve_whitespace_stack) == Py_True) {
      /* Intern the all-whitespace data as it will be helpful
       * for those "pretty printed" XML documents. */
      data = XMLChar_DecodeSizedInterned(str, len, reader->unicode_cache);
      if (data == NULL) return stop_parsing(reader);
      status = charbuf_callback(reader, data, 1);
    } else if (Expat_HasFlag(reader, EXPAT_FLAG_VALIDATE)) {
      DTD *dtd = reader->context->dtd;
      /* whitespace is still an error if it occurrs for an empty model */
      switch (Validator_CheckEvent(dtd->validator, empty_event)) {
      case 0: /* element content ok */
        status = EXPAT_STATUS_OK;
        break;
      case 1:
        status = charbuf_report_error(reader);
        if (status == EXPAT_STATUS_OK) break;
        /* fall through on error */
      default:
        return stop_parsing(reader);
      }
    } else {
      status = EXPAT_STATUS_OK;
    }
  } else {
    /* Normal character data usually doesn't repeat often enough to bother
     * with interning it. */
    data = XMLChar_DecodeSized(str, len);
    if (data == NULL) return stop_parsing(reader);
    status = charbuf_callback(reader, data, 0);
    Py_DECREF(data);
  }
  return status;
}

#define charbuf_reset(reader) \
  (((reader)->buffer_used) ? charbuf_flush(reader) : EXPAT_STATUS_OK)

Py_LOCAL_INLINE(ExpatStatus)
charbuf_resize(ExpatReader *reader, size_t new_size)
{
  XML_Char *buffer = reader->buffer;
  size_t nbytes = ROUND_UP(new_size * sizeof(XML_Char));

  buffer = (XML_Char *)PyMem_Realloc(buffer, nbytes);
  if (buffer == NULL) {
    PyErr_NoMemory();
    return EXPAT_STATUS_ERROR;
  }
  reader->buffer = buffer;
  reader->buffer_size = nbytes / sizeof(XML_Char);
  return EXPAT_STATUS_OK;
}

Py_LOCAL_INLINE(ExpatStatus)
charbuf_write(ExpatReader *reader, const XML_Char *data, size_t len)
{
  XML_Char *buffer;
  register size_t new_len = reader->buffer_used + len;
  register size_t size = reader->buffer_size;

  if (len == 0) return EXPAT_STATUS_OK;

  if (new_len > size) {
    if (charbuf_resize(reader, new_len) == EXPAT_STATUS_ERROR) {
      return EXPAT_STATUS_ERROR;
    }
  }
  buffer = reader->buffer;

  /* store the new data */
  if (len == 1)
    buffer[reader->buffer_used] = data[0];
  else
    memcpy((buffer + reader->buffer_used), data, (len * sizeof(XML_Char)));
  reader->buffer_used = new_len;
  return EXPAT_STATUS_OK;
}

#define charbuf_puts(r, s) charbuf_write((r), (s), XMLChar_Len(s))

Py_LOCAL_INLINE(ExpatStatus)
charbuf_putc(ExpatReader *reader, XML_Char c)
{
  register size_t pos = reader->buffer_used++;
  if (pos >= reader->buffer_size) {
    if (charbuf_resize(reader, reader->buffer_used) == EXPAT_STATUS_ERROR) {
      return EXPAT_STATUS_ERROR;
    }
  }
  reader->buffer[pos] = c;
  return EXPAT_STATUS_OK;
}

/** Parsing Routines **************************************************/

static XML_Char expat_xml_namespace[] = {
  'h', 't', 't', 'p', ':', '/', '/', 'w', 'w', 'w', '.', 'w', '3', '.',
  'o', 'r', 'g', '/', 'X', 'M', 'L', '/', '1', '9', '9', '8', '/', 'n',
  'a', 'm', 'e', 's', 'p', 'a', 'c', 'e', NAMESPACE_SEP
};
static XML_Char expat_base_string[] = { 'b', 'a', 's', 'e' };
static XML_Char expat_lang_string[] = { 'l', 'a', 'n', 'g' };
static XML_Char expat_space_string[] = { 's', 'p', 'a', 'c', 'e' };
static XML_Char expat_id_string[] = { 'i', 'd' };
static XML_Char expat_preserve_string[] = {
  'p', 'r', 'e', 's', 'e', 'r', 'v', 'e', '\0' };
static XML_Char expat_default_string[] = {
  'd', 'e', 'f', 'a', 'u', 'l', 't', '\0' };

#if defined(XML_UNICODE_WIDE)   /* XML_Char 4 bytes wide (UTF-32) */
# define XMLChar_STATIC_LEN(s) (sizeof(s) >> 2)
#elif defined(XML_UNICODE)      /* XML_Char 2 bytes wide (UTF-16) */
# define XMLChar_STATIC_LEN(s) (sizeof(s) >> 1)
#else                           /* XML_Char 1 byte wide (UTF-8) */
# define XMLChar_STATIC_LEN(s) sizeof(s)
#endif

#define XMLChar_STATIC_CMP(s1, s2)                          \
  (XMLChar_NCmp((s1), (s2), XMLChar_STATIC_LEN(s2)) == 0 && \
   ((s1)[XMLChar_STATIC_LEN(s2)] == NAMESPACE_SEP ||        \
    (s1)[XMLChar_STATIC_LEN(s2)] == '\0'))

/* callback functions cannot be declared Py_LOCAL */
static int expat_UnknownEncoding(void *arg, const XML_Char *name,
                                 XML_Encoding *info);

Py_LOCAL_INLINE(XML_Parser)
create_parser(ExpatReader *reader)
{
  static const XML_Char sep[] = { NAMESPACE_SEP, '\0' };
  enum XML_ParamEntityParsing parsing;

  XML_Parser parser = XML_ParserCreate_MM(NULL, &expat_memsuite, sep);
  if (parser == NULL) {
    PyErr_NoMemory();
    return NULL;
  }

  /* enable parsing of parameter entities if requested */
  if (ExpatReader_HasFlag(reader, ExpatReader_DTD_VALIDATION))
    parsing = ExpatReader_PARAM_ENTITY_PARSING;
  else if (ExpatReader_HasFlag(reader, ExpatReader_PARAM_ENTITY_PARSING))
    parsing = XML_PARAM_ENTITY_PARSING_UNLESS_STANDALONE;
  else
    parsing = XML_PARAM_ENTITY_PARSING_NEVER;
  XML_SetParamEntityParsing(parser, parsing);

  /* enable prefix information in names (URI + sep + local + sep + prefix) */
  XML_SetReturnNSTriplet(parser, 1);

  /* enable use of all encodings available with Python */
  XML_SetUnknownEncodingHandler(parser, expat_UnknownEncoding, (void *)reader);

  XML_SetUserData(parser, (void *)reader);

  return parser;
}

/* optimized routine for reading from real file objects */
/* callback functions cannot be declared Py_LOCAL */
static Py_ssize_t read_file(PyObject *file, char *buffer, int length)
{
  FILE *fp = (FILE *) file;
  size_t bytes_read;

  Py_BEGIN_ALLOW_THREADS;
  errno = 0;
  bytes_read = fread(buffer, sizeof(char), length, fp);
  Py_END_ALLOW_THREADS;

  if (bytes_read == 0 && ferror(fp)) {
    PyErr_SetFromErrno(PyExc_IOError);
    clearerr(fp);
    return -1;
  }

  return bytes_read;
}

/* optimized routine for reading from cStringIO objects */
/* callback functions cannot be declared Py_LOCAL */
static Py_ssize_t read_stringio(PyObject *stream, char *buffer, int length)
{
  char *data;
  Py_ssize_t bytes_read;

  bytes_read = PycStringIO->cread(stream, &data, length);

  if (bytes_read > 0)
    memcpy(buffer, data, bytes_read);

  return bytes_read;
}

/* generic routine for reading from any Python object */
/* callback functions cannot be declared Py_LOCAL */
static Py_ssize_t read_object(PyObject *stream, char *buffer, int length)
{
  PyObject *str;
  char *data;
  Py_ssize_t bytes_read = -1;

  str = PyObject_CallMethod(stream, "read", "i", length);
  if (str != NULL) {
    /* bytes_read will be unmodified on error, so OK to ignore result */
    (void) PyString_AsStringAndSize(str, &data, &bytes_read);
    if (bytes_read > 0)
      memcpy(buffer, data, bytes_read);
    Py_DECREF(str);
  }
  return bytes_read;
}

/* Common handling of Expat error condition. */
Py_LOCAL_INLINE(void)
process_error(ExpatReader *reader)
{
  int error_code = XML_GetErrorCode(reader->context->parser);
  PyObject *args, *exception;

  switch (error_code) {
  case XML_ERROR_NONE:
    /* error handler called during non-error condition */
    PyErr_BadInternalCall();
    stop_parsing(reader);
    break;
  case XML_ERROR_NO_MEMORY:
    PyErr_NoMemory();
    break;
  case XML_ERROR_UNEXPECTED_STATE:
  case XML_ERROR_FEATURE_REQUIRES_XML_DTD:
  case XML_ERROR_CANT_CHANGE_FEATURE_ONCE_PARSING:
  case XML_ERROR_SUSPENDED:
  case XML_ERROR_FINISHED:
  case XML_ERROR_SUSPEND_PE:
    /* programming logic is not correct (developer error) */
    PyErr_SetString(PyExc_SystemError, XML_ErrorString(error_code));
    break;
  case XML_ERROR_NOT_SUSPENDED:
    /* user error */
    PyErr_SetString(PyExc_RuntimeError, XML_ErrorString(error_code));
    break;
  case XML_ERROR_ABORTED:
    /* XML_StopParser called (an exception should already be set) */
    if (!PyErr_Occurred()) {
      PyErr_SetString(PyExc_SystemError,
                      "parsing terminated without exception");
    }
    break;
  default:
    /* terminate parsing and setup ReaderError */
    Debug_Print("-- Parsing error ------------ \n"
                "Expat error: %s\n"
                "Expat error code: %d\n",
                XML_ErrorString(error_code), error_code);
    args = Py_BuildValue("iOii", error_code, reader->context->uri,
                         XML_GetErrorLineNumber(reader->context->parser),
                         XML_GetErrorColumnNumber(reader->context->parser));
    if (args) {
      exception = PyObject_Call(ReaderError, args, NULL);
      Py_DECREF(args);
      if (exception) {
        if (ExpatReader_HasFlag(reader, ExpatReader_ERROR_HANDLERS)) {
          (void) ExpatFilter_FatalError(reader->context->filters, exception);
        } else {
          PyErr_SetObject(ReaderError, exception);
        }
        Py_DECREF(exception);
      }
    }
    stop_parsing(reader);
  }
}

/* The core of the parsing routines.  Process the input source until parsing
 * is finished (OK or ERROR) or suspended (SUSPENDED).
 */
 Py_LOCAL_INLINE(ExpatStatus)
continue_parsing(ExpatReader *reader)
{
  Py_ssize_t (*read_func)(PyObject *, char *, int);
  PyObject *read_arg;
  enum XML_Status status;
  Py_ssize_t bytes_read;

  Debug_ParserFunctionCall(continue_parsing, reader);

  read_arg = reader->context->stream;
  if (PyFile_Check(read_arg)) {
    read_func = read_file;
    read_arg = (PyObject *) PyFile_AsFile(read_arg);
  }
  else if (PycStringIO_InputCheck(read_arg)) {
    read_func = read_stringio;
  } else {
    read_func = read_object;
  }

  do {
    XML_ParsingStatus parsing_status;
    void *buffer = XML_GetBuffer(reader->context->parser, EXPAT_BUFSIZ);
    if (buffer == NULL) {
      process_error(reader);
      Debug_ReturnStatus(continue_parsing, EXPAT_STATUS_ERROR);
      return EXPAT_STATUS_ERROR;
    }

    bytes_read = read_func(read_arg, (char *)buffer, EXPAT_BUFSIZ);
    if (bytes_read < 0) {
      Debug_ReturnStatus(continue_parsing, EXPAT_STATUS_ERROR);
      return EXPAT_STATUS_ERROR;
    }

    Debug_ParserFunctionCall(XML_ParseBuffer, reader);

    status = XML_ParseBuffer(reader->context->parser, (int)bytes_read,
                             bytes_read == 0);

    Debug_ReturnStatus(XML_ParseBuffer, status);

    switch (status) {
    case XML_STATUS_OK:
      /* determine if parsing was stopped prematurely */
      XML_GetParsingStatus(reader->context->parser, &parsing_status);
      if (parsing_status.parsing == XML_FINISHED && bytes_read > 0) {
        Debug_ReturnStatus(continue_parsing, EXPAT_STATUS_ERROR);
        return EXPAT_STATUS_ERROR;
      }
      break;
    case XML_STATUS_ERROR:
      process_error(reader);
      Debug_ReturnStatus(continue_parsing, EXPAT_STATUS_ERROR);
      return EXPAT_STATUS_ERROR;
    case XML_STATUS_SUSPENDED:
      Debug_ReturnStatus(continue_parsing, EXPAT_STATUS_SUSPENDED);
      return EXPAT_STATUS_SUSPENDED;
    }
  } while (bytes_read > 0);

  Debug_ReturnStatus(continue_parsing, EXPAT_STATUS_OK);
  return EXPAT_STATUS_OK;
}

/* The entry point for parsing any entity, document or otherwise. */
Py_LOCAL_INLINE(ExpatStatus)
do_parsing(ExpatReader *reader)
{
  XML_Char *encoding, *base;
  enum XML_Status xml_status;
  ExpatStatus status;

  Debug_ParserFunctionCall(do_parsing, reader);

  /* sanity check */
  if (reader->context == NULL) {
    PyErr_BadInternalCall();
    return EXPAT_STATUS_ERROR;
  }

  /* Set externally defined encoding, if defined */
  if (reader->context->encoding != Py_None) {
    encoding = XMLChar_FromObject(reader->context->encoding);
    if (encoding == NULL) {
      return EXPAT_STATUS_ERROR;
    }
    xml_status = XML_SetEncoding(reader->context->parser, encoding);
    free(encoding);
    if (xml_status != XML_STATUS_OK) {
      PyErr_NoMemory();
      return EXPAT_STATUS_ERROR;
    }
  }

  /* Set the base URI for the stream */
  base = XMLChar_FromObject(reader->context->uri);
  if (base == NULL) {
    return EXPAT_STATUS_ERROR;
  }
  xml_status = XML_SetBase(reader->context->parser, base);
  free(base);
  if (xml_status != XML_STATUS_OK) {
    PyErr_NoMemory();
    return EXPAT_STATUS_ERROR;
  }

  status = continue_parsing(reader);

  Debug_ReturnStatus(do_parsing, status);
  return status;
}

Py_LOCAL_INLINE(ExpatStatus)
start_parsing(ExpatReader *reader, XML_Parser parser, PyObject *source)
{
  ExpatStatus status;

  Debug_ParserFunctionCall(start_parsing, reader);

  status = begin_context(reader, parser, source);
  if (status == EXPAT_STATUS_ERROR)
    goto finally;
  begin_handlers(reader, &expat_handlers);

  status = ExpatFilter_StartDocument(reader->context->filters);
  if (status == EXPAT_STATUS_ERROR) goto cleanup;

  status = do_parsing(reader);
  if (status == EXPAT_STATUS_SUSPENDED)
    goto finally;
  else if (status == EXPAT_STATUS_OK) {
    if (reader->buffer_used) {
      status = charbuf_flush(reader);
      if (status == EXPAT_STATUS_ERROR) goto cleanup;
    }
    status = ExpatFilter_EndDocument(reader->context->filters);
    if (status == EXPAT_STATUS_ERROR) goto cleanup;
  }
cleanup:
  /* parsing finished, cleanup parsing state */
  destroy_contexts(reader);
finally:
  Debug_ReturnStatus(start_parsing, status);
  return status;
}

/** Expat StartElement Handler ****************************************/

Py_LOCAL_INLINE(ExpatStatus)
validate_entity_ref(ExpatReader *reader, PyObject *name)
{
  DTD *dtd = reader->context->dtd;
  PyObject *notation;

  notation = PyDict_GetItem(dtd->entities, name);
  if (notation == NULL) {
    return report_error(reader, "UNDECLARED_ENTITY", "{sO}", "entity", name);
  }
  if (notation == Py_None) {
    return report_error(reader, "INVALID_ENTITY", "{sO}", "entity", name);
  }
  if (PyDict_GetItem(dtd->notations, notation) == NULL) {
    return report_error(reader, "UNDECLARED_NOTATION", "{sO}",
                        "notation", notation);
  }

  return EXPAT_STATUS_OK;
}

Py_LOCAL_INLINE(ExpatStatus)
validate_attribute(ExpatReader *reader, PyObject *attribute_type,
                   PyObject *name, PyObject *value)
{
  DTD *dtd = reader->context->dtd;
  PyObject *values;
  Py_ssize_t size;

  /* validate the value for correctness */
  switch (AttributeType_GET_TYPE(attribute_type)) {
  case ATTRIBUTE_TYPE_CDATA:
    /* all content valid */
    break;
  case ATTRIBUTE_TYPE_ID:
  case ATTRIBUTE_TYPE_IDREF:
  case ATTRIBUTE_TYPE_ENTITY:
    switch (XmlString_IsName(value)) {
    case 0:
      if (report_error(reader, "INVALID_NAME_VALUE", "{sO}", "attr", name)
          == EXPAT_STATUS_ERROR)
        return EXPAT_STATUS_ERROR;
    case 1:
      break;
    default:
      return stop_parsing(reader);
    }
    break;
  case ATTRIBUTE_TYPE_IDREFS:
  case ATTRIBUTE_TYPE_ENTITIES:
    switch (XmlString_IsNames(value)) {
    case 0:
      if (report_error(reader, "INVALID_NAME_SEQ_VALUE", "{sO}", "attr", name)
          == EXPAT_STATUS_ERROR)
        return EXPAT_STATUS_ERROR;
    case 1:
      break;
    default:
      return stop_parsing(reader);
    }
    break;
  case ATTRIBUTE_TYPE_NMTOKEN:
    switch (XmlString_IsNmtoken(value)) {
    case 0:
      if (report_error(reader, "INVALID_NMTOKEN_VALUE", "{sO}", "attr", name)
          == EXPAT_STATUS_ERROR)
        return EXPAT_STATUS_ERROR;
    case 1:
      break;
    default:
      return stop_parsing(reader);
    }
    break;
  case ATTRIBUTE_TYPE_NMTOKENS:
    switch (XmlString_IsNmtokens(value)) {
    case 0:
      if (report_error(reader, "INVALID_NMTOKEN_SEQ_VALUE", "{sO}",
                       "attr", name) == EXPAT_STATUS_ERROR)
        return EXPAT_STATUS_ERROR;
    case 1:
      break;
    default:
      return stop_parsing(reader);
    }
    break;
  case ATTRIBUTE_TYPE_NOTATION:
  case ATTRIBUTE_TYPE_ENUMERATION:
    values = AttributeType_GET_ALLOWED_VALUES(attribute_type);
    switch (PySequence_Contains(values, value)) {
    case 0:
      if (report_error(reader, "INVALID_ENUM_VALUE", "{sOsO}", "attr", name,
                       "value", value) == EXPAT_STATUS_ERROR)
        return EXPAT_STATUS_ERROR;
    case 1:
      break;
    default:
      return stop_parsing(reader);
    }
    break;
  }

  /* perform additional validation for some types */
  switch (AttributeType_GET_TYPE(attribute_type)) {
  case ATTRIBUTE_TYPE_ID:
    if (PyDict_GetItem(dtd->ids, value) != NULL) {
      if (report_error(reader, "DUPLICATE_ID", "{sO}", "id", value)
          == EXPAT_STATUS_ERROR)
        return EXPAT_STATUS_ERROR;
    }
    if (PyDict_SetItem(dtd->ids, value, Py_True) < 0) {
      return stop_parsing(reader);
    }
    break;
  case ATTRIBUTE_TYPE_IDREF:
    if (PyList_Append(dtd->used_ids, value) < 0) {
      return stop_parsing(reader);
    }
    break;
  case ATTRIBUTE_TYPE_IDREFS:
    values = PyUnicode_Split(value, unicode_space_char, (Py_ssize_t)-1);
    if (values == NULL) {
      return stop_parsing(reader);
    }
    /* this construct is basically list.extend() */
    size = PyList_GET_SIZE(dtd->used_ids);
    if (PyList_SetSlice(dtd->used_ids, size, size, values) < 0) {
      Py_DECREF(values);
      return stop_parsing(reader);
    }
    Py_DECREF(values);
    break;
  case ATTRIBUTE_TYPE_ENTITY:
    if (validate_entity_ref(reader, value) == EXPAT_STATUS_ERROR) {
      return EXPAT_STATUS_ERROR;
    }
    break;
  case ATTRIBUTE_TYPE_ENTITIES:
    values = PyUnicode_Split(value, unicode_space_char, (Py_ssize_t)-1);
    if (values == NULL) {
      return stop_parsing(reader);
    }
    for (size = 0; size < PyList_GET_SIZE(values); size++) {
      if (validate_entity_ref(reader, PyList_GET_ITEM(values, size))
          == EXPAT_STATUS_ERROR) {
        Py_DECREF(values);
        return EXPAT_STATUS_ERROR;
      }
    }
    Py_DECREF(values);
    break;
  default:
    break;
  }

  return EXPAT_STATUS_OK;
}

Py_LOCAL_INLINE(ExpatStatus)
validate_attributes(ExpatReader *reader, PyObject *element_type,
                    ExpatAttribute *attributes, size_t nattributes)
{
  PyObject *attribute_type, *attribute_name;
  ExpatAttribute *attribute;
  Py_ssize_t i, size;

  for (i = nattributes, attribute = attributes; i > 0; i--, attribute++) {
    attribute_type = \
      ElementType_GET_ATTRIBUTE(element_type, attribute->qualifiedName);
    if (attribute_type == NULL) {
      if (report_error(reader, "UNDECLARED_ATTRIBUTE", "{sO}",
                       "attr", attribute->qualifiedName) == EXPAT_STATUS_ERROR)
        return EXPAT_STATUS_ERROR;
      continue;
    }

    if (validate_attribute(reader, attribute_type, attribute->qualifiedName,
                           attribute->value) == EXPAT_STATUS_ERROR) {
      return EXPAT_STATUS_ERROR;
    }
  }

  /* check for missing required attributes */
  while (PyDict_Next(ElementType_GET_ATTRIBUTES(element_type), &i,
                     &attribute_name, &attribute_type)) {
    if (AttributeType_GET_DECL(attribute_type) == ATTRIBUTE_DECL_REQUIRED) {
      for (size = nattributes, attribute = attributes; size > 0;
           size--, attribute++) {
        switch (PyObject_RichCompareBool(attribute->qualifiedName,
                                         attribute_name, Py_EQ)) {
        case 1:
          goto found;
        case 0:
          break;
        default:
          return stop_parsing(reader);
        }
      }
      if (report_error(reader, "MISSING_ATTRIBUTE", "{sO}",
                       "attr", attribute_name) == EXPAT_STATUS_ERROR)
        return EXPAT_STATUS_ERROR;
    found:
      continue;
    }
  }

  return EXPAT_STATUS_OK;
}

Py_LOCAL_INLINE(ExpatStatus)
validate_element(ExpatReader *reader, ExpatName *element,
                 ExpatAttribute *attributes, size_t nattributes)
{
  DTD *dtd = reader->context->dtd;
  PyObject *element_type;
  ExpatStatus status;

  if (dtd == NULL) {
    /* document didn't declare a document type */
    if (Expat_HasFlag(reader, EXPAT_FLAG_INFOSET_FIXUP)) {
      /* handling an XInclude; disable DTD validation for this document */
      Expat_ClearFlag(reader, EXPAT_FLAG_VALIDATE);
      return EXPAT_STATUS_OK;
    }
    /* validity constraint */
    status = report_error(reader, "MISSING_DOCTYPE", NULL);
    if (status == EXPAT_STATUS_ERROR)
      return status;
    /* create an empty DTD so we have something to validate against */
    reader->context->dtd = dtd = DTD_New();
    if (dtd == NULL) {
      return stop_parsing(reader);
    }
  }

  /* root_element will be Py_None once it has been verified */
  if (dtd->root_element == Py_None) {
    switch (Validator_ValidateEvent(dtd->validator,
                                    element->qualifiedName)) {
    case 0:
      status = report_error(reader, "INVALID_ELEMENT", "{sO}",
                            "element", element->qualifiedName);
      if (status == EXPAT_STATUS_ERROR)
        return status;
      /* fall through */
    case 1:
      /* everything is hunky-dory */
      break;
    default:
      return stop_parsing(reader);
    }
  } else {
    /* verify the declared root element */
    switch (PyObject_RichCompareBool(dtd->root_element,
                                     element->qualifiedName, Py_EQ)) {
    case 0:
      status = report_error(reader, "ROOT_ELEMENT_MISMATCH", "{sO}",
                            "element", element->qualifiedName);
      if (status == EXPAT_STATUS_ERROR)
        return status;
      /* fall through */
    case 1:
      /* Reference to the root element is no longer needed */
      dtd->root_element = Py_None;
      break;
    default:
      return stop_parsing(reader);
    }
  }

  switch (Validator_StartElement(dtd->validator,
                                 element->qualifiedName)) {
  case 0:
    status = report_error(reader, "UNDECLARED_ELEMENT", "{sO}",
                          "element", element->qualifiedName);
    if (status == EXPAT_STATUS_ERROR)
      return status;
    /* fall through */
  case 1:
    /* everything is hunky-dory */
    break;
  default:
    return stop_parsing(reader);
  }

  /* validate the attributes against the element type */
  element_type = Validator_GetElementType(dtd->validator,
                                          element->qualifiedName);
  if (element_type != NULL) {
    /* only validate attributes for declared elements */
    status = validate_attributes(reader, element_type, attributes,
                                 nattributes);
    if (status == EXPAT_STATUS_ERROR) {
      return status;
    }
  }

  return EXPAT_STATUS_OK;
}

Py_LOCAL_INLINE(ExpatStatus)
resize_attribute_list(ExpatReader *reader, size_t size)
{
  ExpatAttribute *attrs = reader->attrs;
  int new_size = ROUND_UP(size);
  if (PyMem_Resize(attrs, ExpatAttribute, new_size) == NULL) {
    PyErr_NoMemory();
    return stop_parsing(reader);
  }
  reader->attrs = attrs;
  reader->attrs_size = new_size;
  return EXPAT_STATUS_OK;
}

/* callback functions cannot be declared Py_LOCAL */
static void expat_StartElement(ExpatReader *reader, const XML_Char *expat_name,
                               const XML_Char **expat_atts)
{
  ExpatStatus status;
  const XML_Char **ppattr;
  ExpatName *name;
  ExpatAttribute *attrs, *attr;
  PyObject *xml_base, *xml_lang, *xml_space, *xml_id, *preserve_whitespace;
  Py_ssize_t id_index;
  size_t i, attrs_size;

  Debug_Print("=== StartElement(context=");
  Debug_PrintVoidPtr(reader->context);
  Debug_Print(", name=");
  Debug_PrintXMLChar(expat_name);
  Debug_Print(", atts=");
  Debug_PrintArray(expat_atts, Debug_PrintXMLChar);
  Debug_Print(")\n");

  if (charbuf_reset(reader) == EXPAT_STATUS_ERROR)
    return;

  /** XML_Char -> PyObject **************************************/

  /* Convert XML_Char inputs to our format */
  name = create_name(reader, expat_name);
  if (name == NULL) {
    stop_parsing(reader);
    return;
  }

  /* Determine how much memory is needed for the attributes array */
  for (ppattr = expat_atts, attrs_size = 0; *ppattr; ppattr += 2, attrs_size++);

  /* get the array for storing the expanded attributes */
  if (attrs_size > reader->attrs_size) {
    if (resize_attribute_list(reader, attrs_size) == EXPAT_STATUS_ERROR) {
      return;
    }
  }

  attrs = attr = reader->attrs;
  id_index = XML_GetIdAttributeIndex(reader->context->parser);
  for (ppattr = expat_atts; *ppattr; ppattr += 2, attr++, id_index -= 2) {
    ExpatName *attr_name = create_name(reader, ppattr[0]);
    PyObject *attr_value = XMLChar_DecodeInterned(ppattr[1],
                                                  reader->unicode_cache);
    if (attr_name == NULL || attr_value == NULL) {
      stop_parsing(reader);
      return;
    }

    /* store attribute name/value pair */
    memcpy(attr, attr_name, sizeof(ExpatName));
    attr->value = attr_value;
    attr->type = (id_index == 0 ? ATTRIBUTE_TYPE_ID : ATTRIBUTE_TYPE_CDATA);
  }

  /** Validation ************************************************/

  if (Expat_HasFlag(reader, EXPAT_FLAG_VALIDATE)) {
    if (validate_element(reader, name, attrs, attrs_size) == EXPAT_STATUS_ERROR)
      return;
  }

  /** Attributes ************************************************/

  /* Get current xml:* settings */
  xml_base = Stack_PEEK(reader->xml_base_stack);
  xml_lang = Stack_PEEK(reader->xml_lang_stack);
  xml_space = Stack_PEEK(reader->xml_space_stack);
  id_index = -1;

  /* Now check for xml:* attributes */
  for (i = 0, attr = attrs; i < attrs_size; i++, attr++) {
    switch (PyObject_RichCompareBool(attr->namespaceURI,
                                     xml_namespace_string, Py_EQ)) {
    case 1:
      /* check for xml:base */
      switch (PyObject_RichCompareBool(attr->localName, base_string, Py_EQ)) {
      case 1:
        xml_base = attr->value;
      case 0:
        break;
      default:
        stop_parsing(reader);
        return;
      }
      /* check for xml:lang */
      switch (PyObject_RichCompareBool(attr->localName, lang_string, Py_EQ)) {
      case 1:
        xml_lang = attr->value;
      case 0:
        break;
      default:
        stop_parsing(reader);
        return;
      }
      /* check for xml:space */
      switch (PyObject_RichCompareBool(attr->localName, space_string, Py_EQ)) {
      case 1:
        switch (PyObject_RichCompareBool(attr->value, preserve_string, Py_EQ)) {
        case 1:
          xml_space = Py_True;
        case 0:
          break;
        default:
          stop_parsing(reader);
          return;
        }
        switch (PyObject_RichCompareBool(attr->value, default_string, Py_EQ)) {
        case 1:
          xml_space = Py_False;
        case 0:
          break;
        default:
          stop_parsing(reader);
          return;
        }
      case 0:
        break;
      default:
        stop_parsing(reader);
        return;
      }
      /* check for xml:id */
      switch (PyObject_RichCompareBool(attr->localName, id_string, Py_EQ)) {
      case 1:
        id_index = i;
        /* fall through */
      case 0:
        break;
      default:
        stop_parsing(reader);
        return;
      }
    }
  }

  if (Expat_HasFlag(reader, EXPAT_FLAG_INFOSET_FIXUP)) {
    /* Ensure that there is enough room in the array to add the attributes */
    size_t new_size = attrs_size + 2;
    Expat_ClearFlag(reader, EXPAT_FLAG_INFOSET_FIXUP);
    if (new_size > reader->attrs_size) {
      if (resize_attribute_list(reader, new_size) == EXPAT_STATUS_ERROR) {
        return;
      }
      attrs = reader->attrs;
    }
    attr = attrs + attrs_size;

    /* XInclude 4.5.5 - Base URI Fixup */
    if (xml_base == Stack_PEEK(reader->xml_base_stack)) {
      /* attribute not present on element, check for fixup */
      switch (PyObject_RichCompareBool(reader->context->xml_base, xml_base,
                                       Py_EQ)) {
      case 0: /* different, add an attribute */
        attr->namespaceURI = xml_namespace_string;
        attr->localName = base_string;
        attr->qualifiedName = xml_base_string;
        if (xml_base == Py_None) {
          attr->value = empty_string;
        } else {
          attr->value = xml_base;
        }
        attrs_size++;
        attr++;
      case 1: /* identical, no fixup required */
        break;
      default: /* error */
        stop_parsing(reader);
        return;
      }
    }

    /* XInclude 4.5.6 - Language Fixup */
    if (xml_lang == Stack_PEEK(reader->xml_lang_stack)) {
      switch (PyObject_RichCompareBool(reader->context->xml_lang, xml_lang,
                                       Py_EQ)) {
      case 0: /* different, add an attribute */
        attr->namespaceURI = xml_namespace_string;
        attr->localName = lang_string;
        attr->qualifiedName = xml_lang_string;
        if (xml_lang == Py_None) {
          attr->value = empty_string;
        } else {
          attr->value = xml_lang;
        }
        attrs_size++;
        attr++;
      case 1: /* identical, no fixup required */
        break;
      default: /* error */
        stop_parsing(reader);
        return;
      }
    }
  }

  /* Save updated xml:* settings */
  Stack_Push(reader->xml_base_stack, xml_base);
  Stack_Push(reader->xml_lang_stack, xml_lang);
  Stack_Push(reader->xml_space_stack, xml_space);
  if (id_index >= 0) {
    xml_id = XmlString_NormalizeSpace(attrs[id_index].value);
    if (xml_id == NULL) {
      stop_parsing(reader);
      return;
    }
    attrs[id_index].value = xml_id;
    attrs[id_index].type = ATTRIBUTE_TYPE_ID;
  } else {
    xml_id = NULL;
  }

  /** XSLT Whitespace Stripping *********************************/

  preserve_whitespace = is_whitespace_preserving(reader,
                                                 name->namespaceURI,
                                                 name->localName);
  if (xml_space == Py_True)
    preserve_whitespace = Py_True;
  Stack_Push(reader->preserve_whitespace_stack, preserve_whitespace);

  /** Callback **************************************************/

  status = ExpatFilter_StartElement(reader->context->filters,
                                    name, attrs, attrs_size);
  if (status == EXPAT_STATUS_ERROR)
    stop_parsing(reader);

  Py_XDECREF(xml_id);
}

/** Expat EndElement Handler ******************************************/

/* callback functions cannot be declared Py_LOCAL */
static void expat_EndElement(ExpatReader *reader, const XML_Char *expat_name)
{
  ExpatStatus status;
  ExpatName *name;
  PyObject *temp;

  Debug_Print("=== EndElement(context=");
  Debug_PrintVoidPtr(reader->context);
  Debug_Print(", name=");
  Debug_PrintXMLChar(expat_name);
  Debug_Print(")\n");

  if (charbuf_reset(reader) == EXPAT_STATUS_ERROR)
    return;

  name = create_name(reader, expat_name);
  if (name == NULL) {
    stop_parsing(reader);
    return;
  }

  /* If DTD validating, ensure all required elements have been seen. */
  if (Expat_HasFlag(reader, EXPAT_FLAG_VALIDATE)) {
    DTD *dtd = reader->context->dtd;
    switch (Validator_EndElement(dtd->validator)) {
    case 1:
      break;
    case 0:
      status = report_error(reader, "INCOMPLETE_ELEMENT", "{sO}",
                            "element", name->qualifiedName);
      if (status == EXPAT_STATUS_OK) break;
    default:
      stop_parsing(reader);
      return;
    }
  }

  status = ExpatFilter_EndElement(reader->context->filters, name);
  if (status == EXPAT_STATUS_ERROR)
    stop_parsing(reader);

  /* Cleanup the xml:* attribute stacks. */
  temp = Stack_Pop(reader->xml_base_stack);
  Py_DECREF(temp);

  temp = Stack_Pop(reader->xml_lang_stack);
  Py_DECREF(temp);

  temp = Stack_Pop(reader->xml_space_stack);
  Py_DECREF(temp);

  temp = Stack_Pop(reader->preserve_whitespace_stack);
  Py_DECREF(temp);
}

/** Expat CharacterData Handler ***************************************/

/* callback functions cannot be declared Py_LOCAL */
static void expat_CharacterData(ExpatReader *reader, const XML_Char *data,
                                int len)
{
  Debug_Print("=== CharacterData(context=");
  Debug_PrintVoidPtr(reader->context);
  Debug_Print(", data=");
  Debug_PrintXMLCharN(data, len);
  Debug_Print(")\n");

  if (charbuf_write(reader, data, len) == EXPAT_STATUS_ERROR)
    stop_parsing(reader);
}

/** Expat ProcessingInstruction Handler *******************************/

/* callback functions cannot be declared Py_LOCAL */
static void expat_ProcessingInstruction(ExpatReader *reader,
                                        const XML_Char *target,
                                        const XML_Char *data)
{
  PyObject *python_target, *python_data;
  ExpatStatus status;

  Debug_Print("=== ProcessingInstruction(context=");
  Debug_PrintVoidPtr(reader->context);
  Debug_Print(", target=");
  Debug_PrintXMLChar(target);
  Debug_Print(", data=");
  Debug_PrintXMLChar(data);
  Debug_Print(")\n");

  if (charbuf_reset(reader) == EXPAT_STATUS_ERROR)
    return;

  python_target = XMLChar_DecodeInterned(target, reader->unicode_cache);
  if (python_target == NULL) {
    stop_parsing(reader);
    return;
  }

  python_data = XMLChar_DecodeInterned(data, reader->unicode_cache);
  if (python_data == NULL) {
    stop_parsing(reader);
    return;
  }

  status = ExpatFilter_ProcessingInstruction(reader->context->filters,
                                             python_target, python_data);
  if (status == EXPAT_STATUS_ERROR)
    stop_parsing(reader);
}

/** Expat Comment Handler *********************************************/

/* callback functions cannot be declared Py_LOCAL */
static void expat_Comment(ExpatReader *reader, const XML_Char *data)
{
  PyObject *python_data;
  ExpatStatus status;

  Debug_Print("=== Comment(context=");
  Debug_PrintVoidPtr(reader->context);
  Debug_Print(", data=");
  Debug_PrintXMLChar(data);
  Debug_Print(")\n");

  if (charbuf_reset(reader) == EXPAT_STATUS_ERROR)
    return;

  /* Note, comment data rarely repeats, no need to intern it. */
  python_data = XMLChar_Decode(data);
  if (python_data == NULL) {
    stop_parsing(reader);
    return;
  }

  status = ExpatFilter_Comment(reader->context->filters, python_data);
  if (status == EXPAT_STATUS_ERROR)
    stop_parsing(reader);

  Py_DECREF(python_data);
}

/** Expat StartNamespaceDecl Handler **********************************/

/* callback functions cannot be declared Py_LOCAL */
static void expat_StartNamespaceDecl(ExpatReader *reader,
                                     const XML_Char *prefix,
                                     const XML_Char *uri)
{
  PyObject *python_prefix, *python_uri;
  ExpatStatus status;

  Debug_Print("=== StartNamespaceDecl(context=");
  Debug_PrintVoidPtr(reader->context);
  Debug_Print(", prefix=");
  Debug_PrintXMLChar(prefix);
  Debug_Print(", uri=");
  Debug_PrintXMLChar(uri);
  Debug_Print(")\n");

  if (charbuf_reset(reader) == EXPAT_STATUS_ERROR)
    return;

  if (prefix) {
    python_prefix = XMLChar_DecodeInterned(prefix, reader->unicode_cache);
    if (python_prefix == NULL) {
      stop_parsing(reader);
      return;
    }
  } else {
    python_prefix = Py_None;
  }

  if (uri) {
    python_uri = XMLChar_DecodeInterned(uri, reader->unicode_cache);
    if (python_uri == NULL) {
      stop_parsing(reader);
      return;
    }
  } else {
    python_uri = Py_None;
  }

  status = ExpatFilter_StartNamespaceDecl(reader->context->filters,
                                          python_prefix, python_uri);
  if (status == EXPAT_STATUS_ERROR)
    stop_parsing(reader);
}

/** Expat EndNamespaceDecl Handler ************************************/

/* callback functions cannot be declared Py_LOCAL */
static void expat_EndNamespaceDecl(ExpatReader *reader, const XML_Char *prefix)
{
  PyObject *python_prefix;
  ExpatStatus status;

  Debug_Print("=== EndNamespaceDecl(context=");
  Debug_PrintVoidPtr(reader->context);
  Debug_Print(", prefix=");
  Debug_PrintXMLChar(prefix);
  Debug_Print(")\n");

  if (charbuf_reset(reader) == EXPAT_STATUS_ERROR)
    return;

  if (prefix) {
    python_prefix = XMLChar_DecodeInterned(prefix, reader->unicode_cache);
    if (python_prefix == NULL) {
      stop_parsing(reader);
      return;
    }
  } else {
    python_prefix = Py_None;
  }

  status = ExpatFilter_EndNamespaceDecl(reader->context->filters,
                                        python_prefix);
  if (status == EXPAT_STATUS_ERROR)
    stop_parsing(reader);
}

/** Expat StartDoctypeDecl Handler ************************************/

/* callback functions cannot be declared Py_LOCAL */
static void expat_StartDoctypeDecl(ExpatReader *reader, const XML_Char *name,
                                   const XML_Char *sysid, const XML_Char *pubid,
                                   int has_internal_subset)
{
  PyObject *python_name, *python_sysid, *python_pubid;
  ExpatStatus status;
  XML_Handlers *subset_handlers;

#ifdef DEBUG_CALLBACKS
  fprintf(stderr, "=== StartDoctypeDecl(%p, name=", reader->context);
  XMLChar_Print(stderr, name);
  fprintf(stderr, ", sysid=");
  XMLChar_Print(stderr, sysid);
  fprintf(stderr, ", pubid=");
  XMLChar_Print(stderr, pubid);
  fprintf(stderr, ", has_internal_subset=%d)\n", has_internal_subset);
#endif

  if (charbuf_reset(reader) == EXPAT_STATUS_ERROR)
    return;

  /* add the DTD to the parsing context */
  if (reader->context->dtd) {
    PyErr_SetString(PyExc_SystemError, "DTD already started");
    stop_parsing(reader);
    return;
  } else {
    if ((reader->context->dtd = DTD_New()) == NULL) {
      stop_parsing(reader);
      return;
    }
  }

  python_name = XMLChar_DecodeInterned(name, reader->unicode_cache);
  if (python_name == NULL) {
    stop_parsing(reader);
    return;
  }
  reader->context->dtd->root_element = python_name;

  if (sysid) {
    if ((python_sysid = XMLChar_Decode(sysid)) == NULL) {
      stop_parsing(reader);
      return;
    }
  } else {
    Py_INCREF(Py_None);
    python_sysid = Py_None;
  }

  if (pubid) {
    if ((python_pubid = XMLChar_Decode(pubid)) == NULL) {
      Py_DECREF(python_sysid);
      stop_parsing(reader);
      return;
    }
  } else {
    Py_INCREF(Py_None);
    python_pubid = Py_None;
  }

  status = ExpatFilter_StartDoctypeDecl(reader->context->filters,
                                        python_name, python_sysid,
                                        python_pubid);
  Py_DECREF(python_sysid);
  Py_DECREF(python_pubid);
  if (status == EXPAT_STATUS_ERROR) {
    stop_parsing(reader);
  } else {
    /* Begin subset handlers */
    subset_handlers = XML_Handlers_Copy(reader->context->handlers);
    subset_handlers->processing_instruction = NULL;
    subset_handlers->comment = NULL;
    begin_handlers(reader, subset_handlers);
  }
}

/** Expat EndDoctypeDecl Handler **************************************/

/* callback functions cannot be declared Py_LOCAL */
static void expat_EndDoctypeDecl(ExpatReader *reader)
{
  DTD *dtd = reader->context->dtd;
  PyObject *name, *temp;
  Py_ssize_t pos;
  ExpatStatus status;

#ifdef DEBUG_CALLBACKS
  fprintf(stderr, "=== EndDoctypeDecl(%p)\n", reader->context);
#endif

  if (charbuf_reset(reader) == EXPAT_STATUS_ERROR)
    return;

  pos = 0;
  while (PyDict_Next(dtd->used_elements, &pos, &name, &temp)) {
    if (report_warning(reader, "ATTRIBUTES_WITHOUT_ELEMENT", "{sO}",
                       "element", name) == EXPAT_STATUS_ERROR)
      return;
  }
  PyDict_Clear(dtd->used_elements);

  if (Expat_HasFlag(reader, EXPAT_FLAG_VALIDATE)) {
    pos = 0;
    while (PyDict_Next(dtd->used_notations, &pos, &name, &temp)) {
      /* Undeclared notations in attributes are errors */
      if (report_error(reader, "ATTRIBUTE_UNDECLARED_NOTATION", "{sOsO}",
                       "attr", temp, "notation", name) == EXPAT_STATUS_ERROR)
        return;
    }
  }
  PyDict_Clear(dtd->used_notations);

  switch (Validator_StartElement(dtd->validator, dtd->root_element)) {
  }

  status = ExpatFilter_EndDoctypeDecl(reader->context->filters);
  if (status == EXPAT_STATUS_ERROR)
    stop_parsing(reader);
  else
    /* Restore content handlers */
    end_handlers(reader);
}

/** Expat CdataSection Handlers ***************************************/

/* callback functions cannot be declared Py_LOCAL */
static void expat_StartCdataSection(ExpatReader *reader)
{
  ExpatStatus status;

#ifdef DEBUG_CALLBACKS
  fprintf(stderr, "=== StartCdataSection(%p)\n", reader->context);
#endif

  status = ExpatFilter_StartCdataSection(reader->context->filters);
  if (status == EXPAT_STATUS_ERROR)
    stop_parsing(reader);
}

/* callback functions cannot be declared Py_LOCAL */
static void expat_EndCdataSection(ExpatReader *reader)
{
  ExpatStatus status;

#ifdef DEBUG_CALLBACKS
  fprintf(stderr, "=== EndCdataSection(%p)\n", reader->context);
#endif

  status = ExpatFilter_EndCdataSection(reader->context->filters);
  if (status == EXPAT_STATUS_ERROR)
    stop_parsing(reader);
}

/** Expat SkippedEntity Handler ***************************************/

/* callback functions cannot be declared Py_LOCAL */
static void expat_SkippedEntity(ExpatReader *reader,
                                const XML_Char *entityName,
                                int is_parameter_entity)
{
  PyObject *python_entityName;
  ExpatStatus status;

#ifdef DEBUG_CALLBACKS
  fprintf(stderr, "=== SkippedEntity(%p, entityName=", reader->context);
  XMLChar_Print(stderr, entityName);
  fprintf(stderr, ", is_parameter_entity=%d)\n", is_parameter_entity);
#endif

  if (charbuf_reset(reader) == EXPAT_STATUS_ERROR)
    return;

  if (is_parameter_entity) {
    /* The SAX spec requires to report skipped PEs with a '%' */
    size_t len = XMLChar_Len(entityName);
    XML_Char *temp = (XML_Char *) PyObject_MALLOC(sizeof(XML_Char) * (len+1));
    if (temp == NULL) {
      stop_parsing(reader);
      return;
    }
    temp[0] = '%';
    memcpy(temp + 1, entityName, len);
    python_entityName = XMLChar_DecodeSized(temp, len + 1);
    PyObject_FREE(temp);
  } else {
    python_entityName = XMLChar_Decode(entityName);
  }
  if (python_entityName == NULL) {
    stop_parsing(reader);
    return;
  }

  status = ExpatFilter_SkippedEntity(reader->context->filters,
                                     python_entityName);
  if (status == EXPAT_STATUS_ERROR)
    stop_parsing(reader);
  Py_DECREF(python_entityName);
}

/** Expat ElementDecl Handler *****************************************/

Py_LOCAL(ExpatStatus)
parse_content(ExpatReader *reader, PyObject *model, XML_Content *content,
              Py_ssize_t initial_state, Py_ssize_t final_state);

Py_LOCAL_INLINE(ExpatStatus)
parse_name(ExpatReader *reader, PyObject *model, XML_Content *content,
           Py_ssize_t initial_state, Py_ssize_t final_state)
{
  PyObject *token;
  int rv;

  token = XMLChar_DecodeInterned(content->name, reader->unicode_cache);
  if (token == NULL) {
    return stop_parsing(reader);
  }

  rv = ContentModel_AddTransition(model, token, initial_state, final_state);
  if (rv < 0) {
    return stop_parsing(reader);
  }

  return EXPAT_STATUS_OK;
}

Py_LOCAL_INLINE(ExpatStatus)
parse_seq(ExpatReader *reader, PyObject *model, XML_Content *content,
          Py_ssize_t initial_state, Py_ssize_t final_state)
{
  register unsigned int i;
  register unsigned int last;
  Py_ssize_t next_state;

  last = content->numchildren - 1;
  for (i = 0; i < last; i++) {
    next_state = ContentModel_NewState(model);
    if (next_state < 0) {
      return stop_parsing(reader);
    }
    if (parse_content(reader, model, &content->children[i], initial_state,
                      next_state) == EXPAT_STATUS_ERROR) {
      return EXPAT_STATUS_ERROR;
    }
    initial_state = next_state;
  }

  if (parse_content(reader, model, &content->children[last], initial_state,
                    final_state) == EXPAT_STATUS_ERROR) {
    return EXPAT_STATUS_ERROR;
  }

  return EXPAT_STATUS_OK;
}

Py_LOCAL_INLINE(ExpatStatus)
parse_choice(ExpatReader *reader, PyObject *model, XML_Content *content,
             Py_ssize_t initial_state, Py_ssize_t final_state)
{
  register unsigned int i;
  register unsigned int last;

  last = content->numchildren;
  for (i = 0; i < last; i++) {
    if (parse_content(reader, model, &content->children[i], initial_state,
                      final_state) == EXPAT_STATUS_ERROR) {
      return EXPAT_STATUS_ERROR;
    }
  }
  return EXPAT_STATUS_OK;
}

Py_LOCAL(ExpatStatus)
parse_content(ExpatReader *reader, PyObject *model, XML_Content *content,
              Py_ssize_t initial_state, Py_ssize_t final_state)
{
  Py_ssize_t s1, s2;
  ExpatStatus status;

  switch (content->quant) {
  case XML_CQUANT_OPT:
    if (ContentModel_AddEpsilonMove(model, initial_state, final_state) < 0) {
      return stop_parsing(reader);
    }
    /* fall through */
  case XML_CQUANT_NONE:
    switch (content->type) {
    case XML_CTYPE_SEQ:
      return parse_seq(reader, model, content, initial_state, final_state);
    case XML_CTYPE_CHOICE:
      return parse_choice(reader, model, content, initial_state, final_state);
    case XML_CTYPE_NAME:
      return parse_name(reader, model, content, initial_state, final_state);
    default:
      PyErr_Format(PyExc_SystemError, "invalid type %d", content->type);
      return stop_parsing(reader);
    }
    break;
  case XML_CQUANT_REP:
    if (ContentModel_AddEpsilonMove(model, initial_state, final_state) < 0) {
      return stop_parsing(reader);
    }
    /* fall through */
  case XML_CQUANT_PLUS:
    s1 = ContentModel_NewState(model);
    s2 = ContentModel_NewState(model);
    if (s1 < 0 || s2 < 0) {
      return stop_parsing(reader);
    }
    if (ContentModel_AddEpsilonMove(model, initial_state, s1) < 0) {
      return stop_parsing(reader);
    }

    switch (content->type) {
    case XML_CTYPE_SEQ:
      status = parse_seq(reader, model, content, s1, s2);
      break;
    case XML_CTYPE_MIXED:
      if (ContentModel_AddTransition(model, content_model_pcdata,
                                     s1, s2) < 0) {
        return stop_parsing(reader);
      }
      /* fall through */
    case XML_CTYPE_CHOICE:
      status = parse_choice(reader, model, content, s1, s2);
      break;
    case XML_CTYPE_NAME:
      status = parse_name(reader, model, content, s1, s2);
      break;
    default:
      PyErr_Format(PyExc_SystemError, "invalid type %d", content->type);
      status = stop_parsing(reader);
    }
    if (status == EXPAT_STATUS_ERROR) return status;

    if (ContentModel_AddEpsilonMove(model, s2, s1) < 0) {
      return stop_parsing(reader);
    }
    if (ContentModel_AddEpsilonMove(model, s2, final_state) < 0) {
      return stop_parsing(reader);
    }
    break;
  }
  return EXPAT_STATUS_OK;
}

Py_LOCAL_INLINE(ExpatStatus)
stringify_content(ExpatReader *reader, XML_Content *cp)
{
  static const XML_Char quant_chars[] = { '\0', '?', '*', '+' };
  XML_Char sep;
  unsigned int i;

  switch (cp->type) {
  case XML_CTYPE_NAME:
    if (charbuf_puts(reader, cp->name) == EXPAT_STATUS_ERROR) {
      return EXPAT_STATUS_ERROR;
    }
    break;
  case XML_CTYPE_SEQ:
  case XML_CTYPE_CHOICE:
    if (charbuf_putc(reader, '(') == EXPAT_STATUS_ERROR) {
      return EXPAT_STATUS_ERROR;
    }

    /* Now loop over the children */
    sep = (cp->type == XML_CTYPE_SEQ ? ',' : '|');
    for (i = 0; i < cp->numchildren; i++) {
      XML_Content *child = &cp->children[i];
      if (i > 0) {
        if (charbuf_putc(reader, sep) == EXPAT_STATUS_ERROR) {
          return EXPAT_STATUS_ERROR;
        }
      }
      if (stringify_content(reader, child) == EXPAT_STATUS_ERROR) {
        return EXPAT_STATUS_ERROR;
      }
    }

    if (charbuf_putc(reader, ')') == EXPAT_STATUS_ERROR) {
      return EXPAT_STATUS_ERROR;
    }
    break;
  default:
    PyErr_SetString(PyExc_SystemError, "invalid content type");
    return stop_parsing(reader);
  }

  return charbuf_putc(reader, quant_chars[cp->quant]);
}

Py_LOCAL_INLINE(PyObject *)
stringify_model(ExpatReader *reader, XML_Content *model)
{
  static const XML_Char start[] = { '(', '#', 'P', 'C', 'D', 'A', 'T', 'A' };
  static const XML_Char close[] = { ')', '*' };
  PyObject *result;
  unsigned int i;

  switch (model->type) {
  case XML_CTYPE_EMPTY:
    Py_INCREF(content_model_empty);
    return content_model_empty;
  case XML_CTYPE_ANY:
    Py_INCREF(content_model_any);
    return content_model_any;
  case XML_CTYPE_MIXED:
    if (model->numchildren == 0) {
      Py_INCREF(content_model_pcdata);
      return content_model_pcdata;
    }
    if (charbuf_write(reader, start, 8) == EXPAT_STATUS_ERROR) {
      return NULL;
    }
    /* Now loop over the Names */
    for (i = 0; i < model->numchildren; i++) {
      XML_Content *cp = &model->children[i];
      if (charbuf_putc(reader, '|') == EXPAT_STATUS_ERROR) {
        return NULL;
      }
      if (charbuf_puts(reader, cp->name) == EXPAT_STATUS_ERROR) {
        return NULL;
      }
    }
    if (charbuf_write(reader, close, 2) == EXPAT_STATUS_ERROR) {
      return NULL;
    }
    break;
  default:
    if (stringify_content(reader, model) == EXPAT_STATUS_ERROR) {
      return NULL;
    }
  }

  result = XMLChar_DecodeSized(reader->buffer, reader->buffer_used);
  reader->buffer_used = 0;
  return result;
}

/* callback functions cannot be declared Py_LOCAL */
static void expat_ElementDecl(ExpatReader *reader, const XML_Char *name,
                              XML_Content *content)
{
  PyObject *element_name, *element_type, *model_string;
  PyObject *model = NULL;
  ExpatStatus status;

#if defined(DEBUG_CALLBACKS)
  fprintf(stderr, "=== ElementDecl(%p, name=", reader->context);
  XMLChar_Print(stderr, name);
  fprintf(stderr, ", content=");
  model_string = stringify_model(reader, content);
  PyObject_Print(model_string, stderr, Py_PRINT_RAW);
  Py_DECREF(model_string);
  fprintf(stderr, ")\n");
#endif

  element_name = XMLChar_DecodeInterned(name, reader->unicode_cache);
  if (element_name == NULL) {
    goto error;
  }

  switch (content->type) {
  case XML_CTYPE_EMPTY:
    model = ContentModel_New();
    if (model == NULL) {
      goto error;
    }
    if (ContentModel_AddEpsilonMove(model, 0, 1) < 0) {
      goto error;
    }
    if (ContentModel_AddTransition(model, empty_event, 0, 1) < 0) {
      goto error;
    }
    break;
  case XML_CTYPE_ANY:
    model = NULL;
    break;
  case XML_CTYPE_MIXED:
    content->quant = XML_CQUANT_REP;
  case XML_CTYPE_CHOICE:
  case XML_CTYPE_SEQ:
    model = ContentModel_New();
    if (model == NULL) {
      goto error;
    }
    if (parse_content(reader, model, content, 0, 1) == EXPAT_STATUS_ERROR) {
      goto finally;
    }
    break;
  default:
    PyErr_Format(PyExc_SystemError, "invalid content type %d", content->type);
    goto error;
  }

  /* see if an ElementType has already been created by an ATTLIST decl */
  element_type = PyDict_GetItem(reader->context->dtd->used_elements,
                                element_name);
  if (element_type == NULL) {
    element_type = ElementType_New(element_name, model);
    if (element_type == NULL) {
      goto error;
    }
  } else {
    /* Set the content model */
    if (ElementType_SetContentModel(element_type, model) < 0) {
      goto error;
    }

    /* removed it from the set of pre-declared elements */
    Py_INCREF(element_type);
    if (PyDict_DelItem(reader->context->dtd->used_elements,
                       element_name) < 0) {
      Py_DECREF(element_type);
      goto error;
    }
  }

  switch (Validator_AddElementType(reader->context->dtd->validator,
                                   element_type)) {
  case 0:
    Py_DECREF(element_type);
    if (report_error(reader, "DUPLICATE_ELEMENT_DECL", "{sO}",
                     "element", element_name) == EXPAT_STATUS_ERROR)
      goto error;
    break;
  case 1:
    Py_DECREF(element_type);
    break;
  default:
    Py_DECREF(element_type);
    goto error;
  }

  /* only create the model string if DTD declarations are needed. */
  if (ExpatReader_HasFlag(reader, ExpatReader_DTD_DECLARATIONS)) {
    model_string = stringify_model(reader, content);
    if (model_string == NULL) goto error;
    status = ExpatFilter_ElementDecl(reader->context->filters,
                                     element_name, model_string);
    Py_DECREF(model_string);
    if (status == EXPAT_STATUS_ERROR)
      goto error;
  }

 finally:
  Py_XDECREF(model);
  XML_FreeContentModel(reader->context->parser, content);
  return;

 error:
  stop_parsing(reader);
  goto finally;
}

/** Expat AttlistDecl Handler *****************************************/

Py_LOCAL_INLINE(PyObject *)
parse_enumeration(ExpatReader *reader, const XML_Char *enumeration)
{
  const XML_Char *p;
  PyObject *items, *item;
  Py_ssize_t nitems;

  Debug_ParserFunctionCall(parse_enumeration, reader);

  /* find the number of individual items */
  for (nitems = 1, p = enumeration; *p; p++) {
    if (*p == '|') nitems++;
  }

  items = PyTuple_New(nitems);
  if (items == NULL) {
    return items;
  }

  for (nitems = 0, p = enumeration; *p++ != ')'; nitems++) {
    const XML_Char *start = p;
    /* find the end of an item */
    while (*p != '|' && *p != ')') {
      p++;
    }
    item = XMLChar_DecodeSizedInterned(start, p - start,
                                       reader->unicode_cache);
    if (item == NULL) {
      Py_DECREF(items);
      return NULL;
    }
    Py_INCREF(item);
    PyTuple_SET_ITEM(items, nitems, item);
  };

  return items;
}

/* callback functions cannot be declared Py_LOCAL */
static void expat_AttlistDecl(ExpatReader *reader, const XML_Char *elname,
                              const XML_Char *attname, const XML_Char *att_type,
                              const XML_Char *dflt, int isrequired)
{
  DTD *dtd = reader->context->dtd;
  AttributeDecl decl;
  AttributeType type;
  PyObject *element_type, *element_name, *attribute_name, *default_value;
  PyObject *allowed_values;
  Py_ssize_t i;
  ExpatStatus status;

#ifdef DEBUG_CALLBACKS
  fprintf(stderr, "=== AttlistDecl(%p, elname=", reader->context);
  XMLChar_Print(stderr, elname);
  fprintf(stderr, ", attname=");
  XMLChar_Print(stderr, attname);
  fprintf(stderr, ", att_type=");
  XMLChar_Print(stderr, att_type);
  fprintf(stderr, ", dflt=");
  XMLChar_Print(stderr, dflt);
  fprintf(stderr, ", isrequired=%d)\n", isrequired);
#endif

  element_name = XMLChar_DecodeInterned(elname, reader->unicode_cache);
  if (element_name == NULL) {
    stop_parsing(reader);
    return;
  }

  attribute_name = XMLChar_DecodeInterned(attname, reader->unicode_cache);
  if (attribute_name == NULL) {
    stop_parsing(reader);
    return;
  }

  if (dflt == NULL) {
    decl = isrequired ? ATTRIBUTE_DECL_REQUIRED : ATTRIBUTE_DECL_IMPLIED;
    default_value = Py_None;
  } else {
    decl = isrequired ? ATTRIBUTE_DECL_FIXED : ATTRIBUTE_DECL_DEFAULT;
    default_value = XMLChar_DecodeInterned(dflt, reader->unicode_cache);
    if (default_value == NULL) {
      stop_parsing(reader);
      return;
    }
  }

  /* This is simplified by the fact that Expat already checks validity */
  allowed_values = NULL;
  switch (*att_type) {
  case 'C': /* CDATA */
    type = ATTRIBUTE_TYPE_CDATA;
    break;
  case 'I': /* ID, IDREF, IDREFS */
    if (att_type[2] == 0) {
      type = ATTRIBUTE_TYPE_ID;
      /* VC: ID Attribute Default */
      if (dflt) {
        if (report_error(reader, "ID_ATTRIBUTE_DEFAULT", NULL)
            == EXPAT_STATUS_ERROR)
          return;
      }
    } else if (att_type[5] == 0) {
      type = ATTRIBUTE_TYPE_IDREF;
    } else {
      type = ATTRIBUTE_TYPE_IDREFS;
    }
    break;
  case 'E': /* ENTITY, ENTITIES */
    if (att_type[6] == 0) {
      type = ATTRIBUTE_TYPE_ENTITY;
    } else {
      type = ATTRIBUTE_TYPE_ENTITIES;
    }
    break;
  case 'N': /* NMTOKEN, NMTOKENS, NOTATION */
    if (att_type[1] == 'M') {
      if (att_type[7] == 0) {
        type = ATTRIBUTE_TYPE_NMTOKEN;
      } else {
        type = ATTRIBUTE_TYPE_NMTOKENS;
      }
    } else {
      type = ATTRIBUTE_TYPE_NOTATION;
      allowed_values = parse_enumeration(reader, att_type+8);
      if (allowed_values == NULL) {
        stop_parsing(reader);
        return;
      }
      for (i = PyTuple_GET_SIZE(allowed_values); i-- > 0;) {
        PyObject *notation = PyTuple_GET_ITEM(allowed_values, i);
        if (PyDict_GetItem(dtd->notations, notation) == NULL) {
          if (PyDict_SetItem(dtd->used_notations, notation,
                             attribute_name) < 0) {
            Py_DECREF(allowed_values);
            stop_parsing(reader);
            return;
          }
        }
      }
    }
    break;
  default: /* Enumeration */
    type = ATTRIBUTE_TYPE_ENUMERATION;
    allowed_values = parse_enumeration(reader, att_type);
    if (allowed_values == NULL) {
      stop_parsing(reader);
      return;
    }
    break;
  }

  /* xml:space, when declared, MUST be given as an enumerated type whose
   * values are one or both of "default" and "preserve". */
  switch (PyObject_RichCompareBool(attribute_name, xml_space_string, Py_EQ)) {
  case 1:
    if (type != ATTRIBUTE_TYPE_ENUMERATION) {
      if (report_error(reader, "XML_SPACE_DECL", NULL) == EXPAT_STATUS_ERROR)
        return;
    } else {
      int cmp = 1;
      for (i = 0; cmp == 1 && i < PyTuple_GET_SIZE(allowed_values); i++) {
        PyObject *value = PyTuple_GET_ITEM(allowed_values, i);
        cmp = PyObject_RichCompareBool(value, default_string, Py_EQ);
        if (cmp == 0) {
          cmp = PyObject_RichCompareBool(value, preserve_string, Py_EQ);
        }
      }
      switch (cmp) {
      case 0: /* value other than "default" or "preserve" in enumeration */
        if (report_error(reader, "XML_SPACE_VALUES", NULL)
            == EXPAT_STATUS_ERROR)
          return;
        /* fall through */
      case 1:
        break;
      default:
        stop_parsing(reader);
        return;
      }
    }
    /* fall through */
  case 0:
    break;
  default:
    stop_parsing(reader);
    return;
  }

  element_type = Validator_GetElementType(dtd->validator, element_name);
  if (element_type == NULL) {
    /* ATTLIST prior to ELEMENT declaration */
    element_type = PyDict_GetItem(dtd->used_elements, element_name);
    if (element_type == NULL) {
      /* first attribute declaration; create a new ElementType to hold the
       * information.
       */
      element_type = ElementType_New(element_name, NULL);
      if (element_type == NULL) {
        stop_parsing(reader);
        return;
      }
      if (PyDict_SetItem(dtd->used_elements, element_name, element_type) < 0) {
        Py_DECREF(element_type);
        stop_parsing(reader);
        return;
      }
      Py_DECREF(element_type);
    }
  }

  if (type == ATTRIBUTE_TYPE_ID) {
    /* VC: One ID per Element Type */
    PyObject *attributes, *key, *value;
    attributes = ElementType_GET_ATTRIBUTES(element_type);
    i = 0;
    while (PyDict_Next(attributes, &i, &key, &value)) {
      if (AttributeType_GET_TYPE(value) == ATTRIBUTE_TYPE_ID) {
        if (report_error(reader, "DUPLICATE_ID_DECL", NULL)
            == EXPAT_STATUS_ERROR)
          return;
        /* Only report once */
        break;
      }
    }
  }

  /* add the attribute decl to the ElementType */
  switch (ElementType_AddAttribute(element_type, attribute_name, type, decl,
                                   allowed_values, default_value)) {
  case 0:
    /* already declared, issue warning */
    if (report_warning(reader, "ATTRIBUTE_DECLARED", "{sO}",
                       "attr", attribute_name) == EXPAT_STATUS_ERROR)
      goto finally;
    break;
  case 1:
    if (ExpatReader_HasFlag(reader, ExpatReader_DTD_DECLARATIONS)) {
      PyObject *type_str, *decl_str;

      type_str = XMLChar_DecodeInterned(att_type, reader->unicode_cache);
      if (type_str == NULL) {
        stop_parsing(reader);
        goto finally;
      }

      switch (decl) {
      case ATTRIBUTE_DECL_IMPLIED:
        decl_str = attribute_decl_implied;
        break;
      case ATTRIBUTE_DECL_REQUIRED:
        decl_str = attribute_decl_required;
        break;
      case ATTRIBUTE_DECL_FIXED:
        decl_str = attribute_decl_fixed;
        break;
      default:
        decl_str = Py_None;
      }

      status = ExpatFilter_AttributeDecl(reader->context->filters,
                                         element_name, attribute_name,
                                         type_str, decl_str, default_value);
      if (status == EXPAT_STATUS_ERROR) {
        stop_parsing(reader);
        goto finally;
      }
    }
    break;
  default:
    stop_parsing(reader);
    break;
  }
finally:
  Py_XDECREF(allowed_values);
}

/** Expat EntityDecl Handler ******************************************/

/* callback functions cannot be declared Py_LOCAL */
static void expat_EntityDecl(ExpatReader *reader, const XML_Char *entityName,
                             int is_parameter_entity, const XML_Char *value,
                             int value_length, const XML_Char *base,
                             const XML_Char *systemId, const XML_Char *publicId,
                             const XML_Char *notationName)
{
  DTD *dtd = reader->context->dtd;
  PyObject *python_entityName;
  size_t len;
  ExpatStatus status;

#ifdef DEBUG_CALLBACKS
  fprintf(stderr, "=== EntityDecl(%p, entityName=", reader->context);
  XMLChar_Print(stderr, entityName);
  fprintf(stderr, ", is_parameter_entity=%d, value=", is_parameter_entity);
  XMLChar_NPrint(stderr, value, value_length);
  fprintf(stderr, ", base=");
  XMLChar_Print(stderr, base);
  fprintf(stderr, ", systemId=");
  XMLChar_Print(stderr, systemId);
  fprintf(stderr, ", publicId=");
  XMLChar_Print(stderr, publicId);
  fprintf(stderr, ", notationName=");
  XMLChar_Print(stderr, notationName);
  fprintf(stderr, ")\n");
#endif

  len = XMLChar_Len(entityName);
  if (is_parameter_entity) {
    /* parameter entity names begin with '%' */
    XML_Char *temp = (XML_Char *) PyObject_MALLOC((len+1) * sizeof(XML_Char));
    if (temp == NULL) {
      stop_parsing(reader);
      return;
    }
    temp[0] = (XML_Char) '%';
    memcpy(temp+1, entityName, len * sizeof(XML_Char));
    python_entityName = XMLChar_DecodeSizedInterned(temp, len+1,
                                                    reader->unicode_cache);
    PyObject_FREE(temp);
  } else {
    python_entityName = XMLChar_DecodeSizedInterned(entityName, len,
                                                    reader->unicode_cache);
  }
  if (python_entityName == NULL) {
    stop_parsing(reader);
    return;
  }

  if (Expat_HasFlag(reader, EXPAT_FLAG_VALIDATE)) {
    if (PyDict_GetItem(dtd->entities, python_entityName)) {
      /* If the same entity is declared more than once, the first declaration
       * encountered is binding. */
      /* NOTE: no need to test return status of this as the handler is going
       * to exit regardless. */
      (void) report_warning(reader, "ENTITY_DECLARED", "{sO}",
                            "entity", python_entityName);
      return;
    }
  }

  if (value == NULL) {
    /* external entity decl */
    PyObject *python_notationName;
    PyObject *python_base;
    PyObject *python_systemId;
    PyObject *python_publicId;

    python_base = XMLChar_Decode(base);
    python_systemId = XMLChar_Decode(systemId);
    if (publicId) {
      python_publicId = XMLChar_Decode(publicId);
    } else {
      Py_INCREF(Py_None);
      python_publicId = Py_None;
    }
    if (python_base == NULL
        || python_systemId == NULL
        || python_publicId == NULL) {
      Py_XDECREF(python_publicId);
      Py_XDECREF(python_systemId);
      Py_XDECREF(python_base);
      stop_parsing(reader);
      return;
    }
    python_systemId = PyObject_CallFunction(absolutize_function, "NN",
                                            python_systemId, python_base);
    if (python_systemId == NULL) {
      stop_parsing(reader);
      return;
    }

    if (notationName == NULL) {
      python_notationName = Py_None;
      status = ExpatFilter_ExternalEntityDecl(reader->context->filters,
                                              python_entityName,
                                              python_publicId,
                                              python_systemId);
      if (status == EXPAT_STATUS_ERROR) stop_parsing(reader);
    } else {
      python_notationName = XMLChar_DecodeInterned(notationName,
                                                   reader->unicode_cache);
      if (python_notationName == NULL) {
        Py_DECREF(python_publicId);
        Py_DECREF(python_systemId);
        stop_parsing(reader);
        return;
      }
      status = ExpatFilter_UnparsedEntityDecl(reader->context->filters,
                                              python_entityName,
                                              python_publicId,
                                              python_systemId,
                                              python_notationName);
      if (status == EXPAT_STATUS_ERROR) stop_parsing(reader);
    }
    Py_DECREF(python_publicId);
    Py_DECREF(python_systemId);

    if (Expat_HasFlag(reader, EXPAT_FLAG_VALIDATE)) {
      if (notationName != NULL) {
        /* unparsed entity */
        if (PyDict_GetItem(dtd->notations, python_notationName) == NULL) {
          if (PyDict_SetItem(dtd->used_notations, python_notationName,
                             python_entityName) < 0) {
            stop_parsing(reader);
            return;
          }
        }
      }
      if (PyDict_SetItem(dtd->entities, python_entityName,
                         python_notationName) < 0) {
        stop_parsing(reader);
        return;
      }
    }
  } else {
    /* internal entity decl */
    PyObject *python_value = XMLChar_DecodeSized(value, value_length);
    if (python_value == NULL) {
      stop_parsing(reader);
      return;
    }
    status = ExpatFilter_InternalEntityDecl(reader->context->filters,
                                            python_entityName, python_value);
    if (status == EXPAT_STATUS_ERROR) stop_parsing(reader);
    Py_DECREF(python_value);
  }
}

/** Expat NotationDecl Handler ****************************************/

/* callback functions cannot be declared Py_LOCAL */
static void expat_NotationDecl(ExpatReader *reader, const XML_Char *notationName,
                               const XML_Char *base, const XML_Char *systemId,
                               const XML_Char *publicId)
{
  DTD *dtd = reader->context->dtd;
  PyObject *python_notationName;
  ExpatStatus status;

#ifdef DEBUG_CALLBACKS
  fprintf(stderr, "=== NotationDecl(%p, notationName=", reader->context);
  XMLChar_Print(stderr, notationName);
  fprintf(stderr, ", base=");
  XMLChar_Print(stderr, base);
  fprintf(stderr, ", systemId=");
  XMLChar_Print(stderr, systemId);
  fprintf(stderr, ", publicId=");
  XMLChar_Print(stderr, publicId);
  fprintf(stderr, ")\n");
#endif

  python_notationName = XMLChar_Decode(notationName);
  if (python_notationName == NULL) {
    stop_parsing(reader);
    return;
  }

  if (Expat_HasFlag(reader, EXPAT_FLAG_VALIDATE)) {
    if (PyDict_SetItem(dtd->notations, python_notationName, Py_True) < 0) {
      Py_DECREF(python_notationName);
      stop_parsing(reader);
      return;
    }
    if (PyDict_GetItem(dtd->used_notations, python_notationName) != NULL) {
      if (PyDict_DelItem(dtd->used_notations, python_notationName) < 0) {
        Py_DECREF(python_notationName);
        stop_parsing(reader);
        return;
      }
    }
  }

  if (ExpatReader_HasFlag(reader, ExpatReader_DTD_DECLARATIONS)) {
    PyObject *python_publicId, *python_systemId;
    if (systemId) {
      python_systemId = XMLChar_Decode(systemId);
    } else {
      Py_INCREF(Py_None);
      python_systemId = Py_None;
    }
    if (publicId) {
      python_publicId = XMLChar_Decode(publicId);
    } else {
      Py_INCREF(Py_None);
      python_publicId = Py_None;
    }
    if (python_publicId == NULL || python_systemId == NULL) {
      Py_XDECREF(python_publicId);
      Py_XDECREF(python_systemId);
      Py_DECREF(python_notationName);
      stop_parsing(reader);
      return;
    }
    status = ExpatFilter_NotationDecl(reader->context->filters,
                                      python_notationName,
                                      python_publicId, python_systemId);
    if (status == EXPAT_STATUS_ERROR) stop_parsing(reader);

    Py_DECREF(python_publicId);
    Py_DECREF(python_systemId);
  }

  Py_DECREF(python_notationName);
}

/** Expat ExternalEntityRef Handler ***********************************/

/* callback functions cannot be declared Py_LOCAL */
static int expat_ExternalEntityRef(XML_Parser parser, const XML_Char *context,
                                   const XML_Char *base, const XML_Char *systemId,
                                   const XML_Char *publicId)
{
  ExpatReader *reader = (ExpatReader *) XML_GetUserData(parser);
  PyObject *python_base, *python_systemId, *python_publicId, *source;
  XML_Parser new_parser;
  ExpatStatus status;
  enum XML_Status result = XML_STATUS_OK;

#if defined(DEBUG_CALLBACKS)
  fprintf(stderr, "=== ExternalEntityRef(%p, context=", reader->context);
  XMLChar_Print(stderr, context);
  fprintf(stderr, ", base=");
  XMLChar_Print(stderr, base);
  fprintf(stderr, ", systemId=");
  XMLChar_Print(stderr, systemId);
  fprintf(stderr, ", publicId=");
  XMLChar_Print(stderr, publicId);
  fprintf(stderr, ")\n");
#endif

  python_base = XMLChar_Decode(base);
  python_systemId = XMLChar_Decode(systemId);
  if (publicId) {
    python_publicId = XMLChar_Decode(publicId);
  } else {
    Py_INCREF(Py_None);
    python_publicId = Py_None;
  }
  if (python_base == NULL
      || python_systemId == NULL
      || python_publicId == NULL) {
    Py_XDECREF(python_publicId);
    Py_XDECREF(python_systemId);
    Py_XDECREF(python_base);
    stop_parsing(reader);
    return result;
  }
  python_systemId = PyObject_CallFunction(absolutize_function, "NN",
                                          python_systemId, python_base);
  if (python_systemId == NULL) {
    stop_parsing(reader);
    return result;
  }

  new_parser = XML_ExternalEntityParserCreate(parser, context, NULL);
  if (new_parser == NULL) {
    Py_DECREF(python_publicId);
    Py_DECREF(python_systemId);
    PyErr_NoMemory();
    stop_parsing(reader);
    return result;
  }

  /* If no resolver is provided, use the default behavior from the
   * InputSource object. */
  source = Py_None;
  if (ExpatReader_HasFlag(reader, ExpatReader_ENTITY_RESOLVER)) {
    FilterState *state = reader->context->filters;
    while (state) {
      if (state->active) {
        ExpatFilter *filter = state->filter;
        ExpatHandlers handlers = filter->handlers;
        if (handlers.resolve_entity) {
          source = handlers.resolve_entity(filter->arg,
                                           python_publicId, python_systemId);
          if (source == NULL) break;
        }
        if (ExpatFilter_HasFlag(filter, ExpatFilter_HANDLER_TYPE)) break;
      }
    }
  }
  if (source == Py_None)
    source = PyObject_CallMethod(reader->context->source, "resolveEntity",
                                 "OO", python_publicId, python_systemId);
  Py_DECREF(python_publicId);
  Py_DECREF(python_systemId);
  if (source == NULL) {
    XML_ParserFree(new_parser);
    stop_parsing(reader);
    return result;
  }

  status = begin_context(reader, new_parser, source);
  Py_DECREF(source);
  if (status == EXPAT_STATUS_ERROR) {
    XML_ParserFree(new_parser);
    stop_parsing(reader);
    return result;
  }

  /* copy DTD from parent parsing context */
  reader->context->dtd = reader->context->next->dtd;

  status = do_parsing(reader);

  Debug_ReturnStatus(expat_ExternalEntityRef, status);

  switch (status) {
  case EXPAT_STATUS_OK:
    /* remove DTD pointer to prevent "double free" */
    reader->context->dtd = NULL;
    end_context(reader);
    break;
  case EXPAT_STATUS_ERROR:
    /* remove DTD pointer to prevent "double free" */
    reader->context->dtd = NULL;
    end_context(reader);
    /* stop the parent parser */
    result = XML_StopParser(parser, 0);
    break;
  case EXPAT_STATUS_SUSPENDED:
    /* suspend the parent parser */
    result = XML_StopParser(parser, 1);
  }

  return result;
}

/** Expat UnknownEncoding Handler *************************************/

typedef struct {
  PyObject *decoder;
  int length[256];
} UnknownEncoding;

/* callback functions cannot be declared Py_LOCAL */
static int encoding_convert(void *userData, const char *bytes)
{
  UnknownEncoding *encoding = (UnknownEncoding *) userData;
  PyObject *result;
  int ch;

  result = PyObject_CallFunction(encoding->decoder, "s#s", bytes,
                                 encoding->length[(unsigned char)(*bytes)],
                                 "strict");
  if (result == NULL)
    return -1;

  if (PyTuple_Check(result) && PyTuple_GET_SIZE(result) == 2 &&
      PyUnicode_Check(PyTuple_GET_ITEM(result, 0))) {
    ch = (int)*PyUnicode_AS_UNICODE(PyTuple_GET_ITEM(result, 0));
  }
  else {
    PyErr_SetString(PyExc_TypeError,
                    "decoder must return a tuple (unicode, integer)");
    ch = -1;
  }
  Py_DECREF(result);

  return ch;
}

/* callback functions cannot be declared Py_LOCAL */
static void encoding_release(void *userData)
{
  UnknownEncoding *encoding = (UnknownEncoding *) userData;

  Py_DECREF(encoding->decoder);
  PyObject_FREE(encoding);
}

static const unsigned char template[] = {
  0x00,  0x01,  0x02,  0x03,  0x04,  0x05,  0x06,  0x07,
  0x08,  0x09,  0x0A,  0x0B,  0x0C,  0x0D,  0x0E,  0x0F,
  0x10,  0x11,  0x12,  0x13,  0x14,  0x15,  0x16,  0x17,
  0x18,  0x19,  0x1A,  0x1B,  0x1C,  0x1D,  0x1E,  0x1F,
  0x20,  0x21,  0x22,  0x23,  0x24,  0x25,  0x26,  0x27,
  0x28,  0x29,  0x2A,  0x2B,  0x2C,  0x2D,  0x2E,  0x2F,
  0x30,  0x31,  0x32,  0x33,  0x34,  0x35,  0x36,  0x37,
  0x38,  0x39,  0x3A,  0x3B,  0x3C,  0x3D,  0x3E,  0x3F,
  0x40,  0x41,  0x42,  0x43,  0x44,  0x45,  0x46,  0x47,
  0x48,  0x49,  0x4A,  0x4B,  0x4C,  0x4D,  0x4E,  0x4F,
  0x50,  0x51,  0x52,  0x53,  0x54,  0x55,  0x56,  0x57,
  0x58,  0x59,  0x5A,  0x5B,  0x5C,  0x5D,  0x5E,  0x5F,
  0x60,  0x61,  0x62,  0x63,  0x64,  0x65,  0x66,  0x67,
  0x68,  0x69,  0x6A,  0x6B,  0x6C,  0x6D,  0x6E,  0x6F,
  0x70,  0x71,  0x72,  0x73,  0x74,  0x75,  0x76,  0x77,
  0x78,  0x79,  0x7A,  0x7B,  0x7C,  0x7D,  0x7E,  0x7F,
  0x80,  0x81,  0x82,  0x83,  0x84,  0x85,  0x86,  0x87,
  0x88,  0x89,  0x8A,  0x8B,  0x8C,  0x8D,  0x8E,  0x8F,
  0x90,  0x91,  0x92,  0x93,  0x94,  0x95,  0x96,  0x97,
  0x98,  0x99,  0x9A,  0x9B,  0x9C,  0x9D,  0x9E,  0x9F,
  0xA0,  0xA1,  0xA2,  0xA3,  0xA4,  0xA5,  0xA6,  0xA7,
  0xA8,  0xA9,  0xAA,  0xAB,  0xAC,  0xAD,  0xAE,  0xAF,
  0xB0,  0xB1,  0xB2,  0xB3,  0xB4,  0xB5,  0xB6,  0xB7,
  0xB8,  0xB9,  0xBA,  0xBB,  0xBC,  0xBD,  0xBE,  0xBF,
  0xC0,  0xC1,  0xC2,  0xC3,  0xC4,  0xC5,  0xC6,  0xC7,
  0xC8,  0xC9,  0xCA,  0xCB,  0xCC,  0xCD,  0xCE,  0xCF,
  0xD0,  0xD1,  0xD2,  0xD3,  0xD4,  0xD5,  0xD6,  0xD7,
  0xD8,  0xD9,  0xDA,  0xDB,  0xDC,  0xDD,  0xDE,  0xDF,
  0xE0,  0xE1,  0xE2,  0xE3,  0xE4,  0xE5,  0xE6,  0xE7,
  0xE8,  0xE9,  0xEA,  0xEB,  0xEC,  0xED,  0xEE,  0xEF,
  0xF0,  0xF1,  0xF2,  0xF3,  0xF4,  0xF5,  0xF6,  0xF7,
  0xF8,  0xF9,  0xFA,  0xFB,  0xFC,  0xFD,  0xFE,  0xFF,
  /* terminator */
  0x00
};

/* callback functions cannot be declared Py_LOCAL */
static int expat_UnknownEncoding(void *arg, const XML_Char *name,
                                 XML_Encoding *info)
{
  PyObject *_u_name, *_s_name;
  PyObject *encoder, *decoder;
  PyObject *result;
  Py_UNICODE unichr;
  int i;
  UnknownEncoding *encoding;

#if defined(DEBUG_CALLBACKS)
  fprintf(stderr, "=== UnknownEncoding(%p, name=",
          ((ExpatReader *)arg)->context);
  XMLChar_Print(stderr, name);
  fprintf(stderr, ", info=%p)\n", info);
#endif

  _u_name = XMLChar_Decode(name);
  if (_u_name == NULL)
    return XML_STATUS_ERROR;

  /* Encodings must be ASCII per the XML spec */
  _s_name = PyUnicode_EncodeASCII(PyUnicode_AS_UNICODE(_u_name),
                                  PyUnicode_GET_SIZE(_u_name),
                                  NULL);
  Py_DECREF(_u_name);
  if (_s_name == NULL)
    return XML_STATUS_ERROR;

  encoder = PyCodec_Encoder(PyString_AS_STRING(_s_name));
  decoder = PyCodec_Decoder(PyString_AS_STRING(_s_name));
  Py_DECREF(_s_name);
  if (encoder == NULL || decoder == NULL) {
    Py_XDECREF(encoder);
    Py_XDECREF(decoder);
    return XML_STATUS_ERROR;
  }

  /* Check if we can use the direct replacement method (8-bit encodings) */
  result = PyObject_CallFunction(decoder, "s#s", template, 256, "replace");
  if (result == NULL) {
    PyErr_Clear();
  } else if (PyTuple_Check(result) && PyTuple_GET_SIZE(result) == 2 &&
             PyUnicode_Check(PyTuple_GET_ITEM(result, 0)) &&
             PyUnicode_GET_SIZE(PyTuple_GET_ITEM(result, 0)) == 256) {
    /* we have a valid 8-bit encoding */
    Py_UNICODE *unistr = PyUnicode_AS_UNICODE(PyTuple_GET_ITEM(result, 0));
    for (i = 0; i < 256; i++) {
      unichr = unistr[i];
      if (unichr == Py_UNICODE_REPLACEMENT_CHARACTER)
        info->map[i] = -1;
      else
        info->map[i] = unichr;
    }
    Py_DECREF(result);
    Py_DECREF(encoder);
    Py_DECREF(decoder);
    return XML_STATUS_OK;
  } else {
    Py_DECREF(result);
  }

  /* Use the convert function method (multibyte encodings) */
  encoding = (UnknownEncoding *) PyObject_MALLOC(sizeof(UnknownEncoding));
  if (encoding == NULL) {
    Py_DECREF(encoder);
    Py_DECREF(decoder);
    return XML_STATUS_ERROR;
  }

  for (unichr = 0; unichr <= 0xFFFD; unichr++) {
    result = PyObject_CallFunction(encoder, "u#s", &unichr, 1, "ignore");
    if (result == NULL || !PyTuple_Check(result) ||
        PyTuple_GET_SIZE(result) != 2) {
      Py_XDECREF(result);
      Py_DECREF(encoder);
      Py_DECREF(decoder);
      PyObject_FREE(encoding);
      return XML_STATUS_ERROR;
    }

    /* treat non-string results as invalid value */
    if (PyString_Check(PyTuple_GET_ITEM(result, 0))) {
      int c = (unsigned char) *PyString_AS_STRING(PyTuple_GET_ITEM(result, 0));
      int n = (int)PyString_GET_SIZE(PyTuple_GET_ITEM(result, 0));
      if (n == 1) {
        /* one-to-one replacement */
        info->map[c] = unichr;
      }
      else if (n > 1) {
        /* multibyte replacement */
        info->map[c] = -n;
      }
      encoding->length[c] = n;
    }
    Py_DECREF(result);
  }

  /* consume the reference */
  encoding->decoder = decoder;
  info->data = (void *) encoding;
  info->convert = encoding_convert;
  info->release = encoding_release;

  Py_DECREF(encoder);
  return XML_STATUS_OK;
}

/** ExpatFilter *******************************************************/

/* Defined here to allow for compiler inlining */
Py_LOCAL_INLINE(ExpatStatus)
process_xml_attributes(ExpatReader *reader, const XML_Char **atts,
                       const XML_Char **xml_id)
{
  PyObject *xml_base, *xml_lang, *xml_space_preserve, *value;
  const XML_Char **ppattr;

  /* get current xml:* settings */
  xml_base = Stack_PEEK(reader->xml_base_stack);
  xml_lang = Stack_PEEK(reader->xml_lang_stack);
  xml_space_preserve = Stack_PEEK(reader->xml_space_stack);

  for (ppattr = atts; *ppattr; ppattr += 2) {
    /* check for xml:* attributes */
    if (XMLChar_NCmp(ppattr[0], expat_xml_namespace,
                     XMLChar_STATIC_LEN(expat_xml_namespace)) == 0) {
      const XML_Char *xml_attr_name =
        ppattr[0] + XMLChar_STATIC_LEN(expat_xml_namespace);

      /* borrowed reference */
      value = XMLChar_DecodeInterned(ppattr[1], reader->unicode_cache);
      if (value == NULL)
        return stop_parsing(reader);

      /* check for xml:base */
      if (XMLChar_STATIC_CMP(xml_attr_name, expat_base_string)) {
        xml_base = value;
      }
      /* check for xml:lang */
      else if (XMLChar_STATIC_CMP(xml_attr_name, expat_lang_string)) {
        xml_lang = value;
      }
      /* check for xml:space */
      else if (XMLChar_STATIC_CMP(xml_attr_name, expat_space_string)) {
        if (XMLChar_Cmp(ppattr[1], expat_preserve_string) == 0)
          xml_space_preserve = Py_True;
        else if (XMLChar_Cmp(ppattr[1], expat_default_string) == 0)
          xml_space_preserve = Py_False;
      }
      /* check for xml:id */
      else if (XMLChar_STATIC_CMP(xml_attr_name, expat_id_string)) {
        /* normalize the value as if an ID type */
        const XML_Char *src = ppattr[1];
        XML_Char *dst = (XML_Char *)src;

        dst = (XML_Char *)(src = *xml_id = ppattr[1]);

        /* skip leading spaces and collapse multiple spaces into one */
        while (src[0]) {
          XML_Char ch = *src++;
          if (ch == 0x20 && (dst == *xml_id || dst[-1] == 0x20)) continue;
          *dst++ = ch;
        }
        /* remove trailing space, if any */
        if (dst > *xml_id && dst[-1] == 0x20) dst--;
        *dst = '\0';
      }
    }
  }

  /* save updated xml:* settings */
  Stack_Push(reader->xml_base_stack, xml_base);
  Stack_Push(reader->xml_lang_stack, xml_lang);
  Stack_Push(reader->xml_space_stack, xml_space_preserve);

  return EXPAT_STATUS_OK;
}

/** External Interface ************************************************/

ExpatReader *
ExpatReader_New(ExpatFilter *filters[], size_t nfilters)
{
  ExpatReader *reader;
  size_t i;

  if (expat_library_error != NULL) {
    PyErr_SetObject(PyExc_RuntimeError, expat_library_error);
    return NULL;
  }

  reader = (ExpatReader *)PyObject_MALLOC(sizeof(struct ExpatReaderStruct));
  if (reader == NULL) {
    PyErr_NoMemory();
    return NULL;
  }
  memset(reader, 0, sizeof(struct ExpatReaderStruct));

  if ((reader->filters = PyMem_New(ExpatFilter, nfilters)) == NULL)
    goto memory_error;
  for (i = 0; i < nfilters; i++) {
    ExpatHandlers handlers;
    memcpy(&reader->filters[i], filters[i], sizeof(ExpatFilter));
    handlers = reader->filters[i].handlers;
    if (handlers.resolve_entity) {
      ExpatReader_SetFlag(reader, ExpatReader_ENTITY_RESOLVER);
    }
    if (handlers.warning || handlers.error || handlers.fatal_error) {
      ExpatReader_SetFlag(reader, ExpatReader_ERROR_HANDLERS);
    }
    if (handlers.element_decl || handlers.attribute_decl ||
        handlers.external_entity_decl || handlers.internal_entity_decl) {
      ExpatReader_SetFlag(reader, ExpatReader_DTD_DECLARATIONS);
    }
  }
  reader->filters_size = nfilters;

  /* caching of split-names */
  if ((reader->name_cache = HashTable_New()) == NULL)
    goto error;

  /* interning table for XML_Char -> PyUnicodeObjects */
  if ((reader->unicode_cache = HashTable_New()) == NULL)
    goto error;

  /* character data buffering */
  if ((reader->buffer = PyMem_New(XML_Char, XMLCHAR_BUFSIZ)) == NULL)
    goto memory_error;
  reader->buffer_size = XMLCHAR_BUFSIZ;
  reader->buffer_used = 0;

  /* attribute buffering */
  /* parser->attrs == NULL and parser->attrs_size == 0 already, so no
   * addition work is needed as the setup happens in expat_StartElement
   * as soon as the buffer is used.
   */

  /* base URI stack */
  if ((reader->xml_base_stack = Stack_New()) == NULL)
    goto error;
  Stack_Push(reader->xml_base_stack, Py_None);

  /* language stack */
  if ((reader->xml_lang_stack = Stack_New()) == NULL)
    goto error;
  Stack_Push(reader->xml_lang_stack, Py_None);

  /* xml:space='preserve' state stack */
  if ((reader->xml_space_stack = Stack_New()) == NULL)
    goto error;
  Stack_Push(reader->xml_space_stack, Py_False); /* xml:space='default' */

  /* whitespace preserving state stack */
  if ((reader->preserve_whitespace_stack = Stack_New()) == NULL)
    goto error;
  Stack_Push(reader->preserve_whitespace_stack, Py_True);

  return reader;

memory_error:
  PyErr_NoMemory();
error:
  ExpatReader_Del(reader);
  return NULL;
}

void
ExpatReader_Del(ExpatReader *reader)
{
  if (reader->context) {
   destroy_contexts(reader);
  }

  if (reader->preserve_whitespace_stack) {
    Stack_Del(reader->preserve_whitespace_stack);
    reader->preserve_whitespace_stack = NULL;
  }

  if (reader->xml_space_stack) {
    Stack_Del(reader->xml_space_stack);
    reader->xml_space_stack = NULL;
  }

  if (reader->xml_lang_stack) {
    Stack_Del(reader->xml_lang_stack);
    reader->xml_lang_stack = NULL;
  }

  if (reader->xml_base_stack) {
    Stack_Del(reader->xml_base_stack);
    reader->xml_base_stack = NULL;
  }

  if (reader->attrs) {
    PyMem_Del(reader->attrs);
    reader->attrs = NULL;
  }

  if (reader->buffer) {
    PyMem_Del(reader->buffer);
    reader->buffer = NULL;
  }

  if (reader->unicode_cache) {
    HashTable_Del(reader->unicode_cache);
    reader->unicode_cache = NULL;
  }

  if (reader->name_cache) {
    HashTable_Del(reader->name_cache);
    reader->name_cache = NULL;
  }

  PyObject_FREE(reader);
}

int
ExpatReader_GetValidation(ExpatReader *reader)
{
  return ExpatReader_HasFlag(reader, ExpatReader_DTD_VALIDATION) ? 1 : 0;
}

void
ExpatReader_SetValidation(ExpatReader *reader, int doValidation)
{
  /* do not allowing changing after parsing has begun */
  if (reader->context == NULL) {
    if (doValidation)
      ExpatReader_SetFlag(reader, ExpatReader_DTD_VALIDATION);
    else
      ExpatReader_ClearFlag(reader, ExpatReader_DTD_VALIDATION);
  }
}

int
ExpatReader_GetParamEntityParsing(ExpatReader *reader)
{
  return ExpatReader_HasFlag(reader, ExpatReader_PARAM_ENTITY_PARSING) ? 1 : 0;
}

void
ExpatReader_SetParamEntityParsing(ExpatReader *reader, int doParamEntityParsing)
{
  /* do not allowing changing after parsing has begun */
  if (reader->context == NULL) {
    if (doParamEntityParsing)
      ExpatReader_SetFlag(reader, ExpatReader_PARAM_ENTITY_PARSING);
    else
      ExpatReader_ClearFlag(reader, ExpatReader_PARAM_ENTITY_PARSING);
  }
}

PyObject *
ExpatReader_GetWhitespaceStripping(ExpatReader *reader)
{
  WhitespaceRules *rules = reader->whitespace_rules;
  PyObject *sequence, *item;
  size_t size, i;

  if (rules == NULL)
    return PyTuple_New(0);
  size = rules->size;
  sequence = PyTuple_New(size);
  if (sequence == NULL)
    return NULL;
  for (i = 0; i < size; i++) {
    WhitespaceRule *rule = &rules->items[i];
    switch (rule->test_type) {
    case EXPANDED_NAME_TEST:
      item = PyTuple_Pack(3, rule->test_namespace, rule->test_name,
                          rule->preserve_flag);
      break;
    case NAMESPACE_TEST:
      item = PyTuple_Pack(3, rule->test_namespace, asterisk_string,
                          rule->preserve_flag);
      break;
    case ELEMENT_TEST:
      item = PyTuple_Pack(3, Py_None, asterisk_string, rule->preserve_flag);
      break;
    default:
      PyErr_BadInternalCall();
      item = NULL;
    }
    if (item == NULL) {
      Py_DECREF(sequence);
      return NULL;
    }
    PyTuple_SET_ITEM(sequence, i, item);
  }
  return sequence;
}

ExpatStatus
ExpatReader_SetWhitespaceStripping(ExpatReader *reader, PyObject *seq)
{
  /* do not allowing changing after parsing has begun */
  if (reader->context == NULL) {
    WhitespaceRules *rules;
    if (seq == NULL) {
      rules = NULL;
    } else {
      rules = create_whitespace_rules(reader, seq);
      if (rules == NULL) {
        return EXPAT_STATUS_ERROR;
      }
    }
    if (reader->whitespace_rules != NULL) {
      destroy_whitespace_rules(reader->whitespace_rules);
    }
    reader->whitespace_rules = rules;
  }
  return EXPAT_STATUS_OK;
}

/** ExpatReader_Parse *************************************************/

ExpatStatus
ExpatReader_Parse(ExpatReader *reader, PyObject *source)
{
  XML_Parser parser;
  ExpatStatus status;

  Debug_FunctionCall(ExpatReader_Parse, reader);

  parser = create_parser(reader);
  if (parser == NULL) {
    return EXPAT_STATUS_ERROR;
  }

  status = start_parsing(reader, parser, source);

  Debug_ReturnStatus(ExpatReader_Parse, status);

  return status;
}

/** ExpatReader_ParseEntity *******************************************/

/* copied from xmlparse.c
   needed for entity parsing to recognize XML namespace
*/
static const XML_Char implicit_context[] = {
  'x', 'm', 'l', '=', 'h', 't', 't', 'p', ':', '/', '/',
  'w', 'w', 'w', '.', 'w', '3', '.', 'o', 'r', 'g', '/',
  'X', 'M', 'L', '/', '1', '9', '9', '8', '/',
  'n', 'a', 'm', 'e', 's', 'p', 'a', 'c', 'e', '\0'
};

Py_LOCAL_INLINE(XML_Char *)
create_parser_context(PyObject *namespaces)
{
  PyObject *prefix, *uri;
  XML_Char *context, *ptr;
  Py_ssize_t i, used, size, new_len;

  /* convert 'namespaces' to a true dictionary */
  if (PyDict_Check(namespaces)) {
    Py_INCREF(namespaces);
  } else {
    PyObject *dict = PyDict_New();
    if (dict == NULL) return NULL;
    if (PyDict_Merge(dict, namespaces, 1) < 0) {
      Py_DECREF(dict);
      return NULL;
    }
    namespaces = dict;
  }

  /* default initial allocation to the number of add'l namespaces */
  size = PyDict_Size(namespaces) + 1;
  used = XMLChar_STATIC_LEN(implicit_context);
  size = ROUND_UP(size*used);

#define XMLCHAR_CONCAT_AND_DEL(dst, ob) do { \
  assert(sizeof(XML_Char) == sizeof(Py_UNICODE)); \
  Py_UNICODE_COPY(dst, PyUnicode_AS_UNICODE(ob), PyUnicode_GET_SIZE(ob)); \
  dst += PyUnicode_GET_SIZE(ob); \
  Py_DECREF(ob); \
} while (0)

  /* the default namespace (prefix=`None`) must be the first entry.
   * Adjust the initial allocation to ensure that the URI will fit. */
  if ((uri = PyDict_GetItem(namespaces, Py_None)) != NULL) {
    uri = PyObject_Unicode(uri);
    if (uri == NULL) {
      Py_DECREF(namespaces);
      return NULL;
    }
    /* +2 for NAMESPACE_SEP ('=') and CONTEXT_SEP ('\f') */
    used += PyUnicode_GET_SIZE(uri) + 2;
    if (used > size) {
      size = ROUND_UP(used);
    }
  }
  ptr = context = PyMem_New(XML_Char, size);
  if (context == NULL) {
    Py_DECREF(namespaces);
    PyErr_NoMemory();
    return NULL;
  }
  /* copy the uri to the context */
  if (uri) {
    *ptr++ = '=';
    XMLCHAR_CONCAT_AND_DEL(ptr, uri);
    *ptr++ = '\f';
  }

  i = 0;
  while (PyDict_Next(namespaces, &i, &prefix, &uri)) {
    if (prefix == Py_None) continue;
    prefix = PyObject_Unicode(prefix);
    uri = PyObject_Unicode(uri);
    if (prefix == NULL || uri == NULL) {
      Py_DECREF(namespaces);
      PyMem_Del(context);
      return NULL;
    }

    /* +2 for NAMESPACE_SEP ('=') and CONTEXT_SEP ('\f') */
    new_len = used + PyUnicode_GET_SIZE(prefix) + PyUnicode_GET_SIZE(uri) + 2;
    if (new_len > size) {
      size = ROUND_UP(new_len);
      used = (Py_ssize_t)(ptr - context);
      ptr = context;
      if (PyMem_Resize(ptr, XML_Char, size) == NULL) {
        Py_DECREF(prefix);
        Py_DECREF(uri);
        Py_DECREF(namespaces);
        PyMem_Del(context);
        PyErr_NoMemory();
        return NULL;
      }
      context = ptr;
      ptr += used;
    }
    used = new_len;

    /* copy the prefix to the context */
    XMLCHAR_CONCAT_AND_DEL(ptr, prefix);
    *ptr++ = '=';

    /* copy the uri to the context */
    XMLCHAR_CONCAT_AND_DEL(ptr, uri);
    *ptr++ = '\f';
  }
  Py_DECREF(namespaces);

  /* add the default context */
  assert(((ptr - context) + XMLChar_STATIC_LEN(implicit_context)) == used);
  assert(used < size);
  memcpy(ptr, implicit_context, sizeof(implicit_context));

  return context;
}

ExpatStatus
ExpatReader_ParseEntity(ExpatReader *reader, PyObject *source,
                        PyObject *namespaces)
{
  XML_Char *parser_context = (XML_Char *)implicit_context;
  XML_Parser parser;
  ExpatStatus status;

  Debug_FunctionCall(ExpatReader_ParseEntity, reader);

  if (namespaces) {
    parser_context = create_parser_context(namespaces);
    if (parser_context == NULL) {
      return EXPAT_STATUS_ERROR;
    }
  }
  parser = create_parser(reader);
  if (parser == NULL) {
    PyMem_Del(parser_context);
    return EXPAT_STATUS_ERROR;
  }
  /* create a nested context to allow a resumed parser to do the cleanup */
  reader->context = Context_New(parser, Py_None);
  if (reader->context == NULL) {
    XML_ParserFree(parser);
    PyMem_Del(parser_context);
    return EXPAT_STATUS_ERROR;
  }
  parser = XML_ExternalEntityParserCreate(parser, parser_context, NULL);
  if (namespaces) {
    PyMem_Del(parser_context);
  }
  if (parser == NULL) {
    end_context(reader);
    PyErr_NoMemory();
    return EXPAT_STATUS_ERROR;
  }

  status = start_parsing(reader, parser, source);

  Debug_ReturnStatus(ExpatReader_ParseEntity, status);

  return status;
}

/** ExpatReader_Suspend ***********************************************/

ExpatStatus
ExpatReader_Suspend(ExpatReader *reader)
{
  Context *context = reader->context;
  if (context) {
    if (XML_StopParser(context->parser, 1) == XML_STATUS_ERROR) {
      process_error(reader);
      return stop_parsing(reader);
    }
  }
  return EXPAT_STATUS_OK;
}

/** ExpatReader_Resume ************************************************/

ExpatStatus
ExpatReader_Resume(ExpatReader *reader)
{
  enum XML_Status status;
  XML_ParsingStatus parsing_status;

  Debug_ParserFunctionCall(ExpatReader_Resume, reader);

  status = XML_ResumeParser(reader->context->parser);

  switch (status) {
  case XML_STATUS_OK:
    /* determine if parsing was suspended in the final buffer */
    XML_GetParsingStatus(reader->context->parser, &parsing_status);
    if (parsing_status.finalBuffer) {
      /* restore previous context */
      end_context(reader);
      /* if last context, exit now */
      if (reader->context == NULL) {
        return EXPAT_STATUS_OK;
      }
    }
    break;
  case XML_STATUS_ERROR:
    process_error(reader);
    return EXPAT_STATUS_ERROR;
  case XML_STATUS_SUSPENDED:
    return EXPAT_STATUS_SUSPENDED;
  }

  return continue_parsing(reader);
}

/** ExpatReader Locator Interface *************************************/

PyObject *ExpatReader_GetBase(ExpatReader *reader)
{
  PyObject *base;

  base = Stack_PEEK(reader->xml_base_stack);
  Py_INCREF(base);
  return base;
}

unsigned long ExpatReader_GetLineNumber(ExpatReader *reader)
{
  Context *context = reader->context;
  if (context)
    return XML_GetCurrentLineNumber(context->parser);
  return 0;
}

unsigned long ExpatReader_GetColumnNumber(ExpatReader *reader)
{
  Context *context = reader->context;
  if (context)
    return XML_GetCurrentColumnNumber(context->parser);
  return 0;
}

int ExpatReader_GetParsingStatus(ExpatReader *reader)
{
  Context *context = reader->context;
  static XML_ParsingStatus status;
  if (context) {
    XML_GetParsingStatus(context->parser, &status);
    return (status.parsing == XML_PARSING || status.parsing == XML_SUSPENDED);
  }
  return 0;
}

/** Module Interface **************************************************/

static PyMethodDef module_methods[] = {
  { NULL }
};

static Expat_APIObject Expat_API = {
  ExpatFilter_New,
  ExpatFilter_Del,
  ExpatReader_New,
  ExpatReader_Del,
  ExpatReader_SetValidation,
  ExpatReader_SetParamEntityParsing,
  ExpatReader_Parse,
  ExpatReader_ParseEntity,
  ExpatReader_Suspend,
  ExpatReader_Resume,
  ExpatReader_GetBase,
  ExpatReader_GetLineNumber,
  ExpatReader_GetColumnNumber,

};

struct submodule_t {
  int (*init)(PyObject *);
  void (*fini)(void);
};

#define SUBMODULE(name) { _Expat_##name##_Init, _Expat_##name##_Fini }
struct submodule_t submodules[] = {
  SUBMODULE(Util),
  SUBMODULE(ContentModel),
  SUBMODULE(InputSource),
  SUBMODULE(Attributes),
  SUBMODULE(Reader),
  SUBMODULE(Filter),
  SUBMODULE(SaxFilter),
  { NULL, NULL }
};

static void fini_expat(void *capi)
{
  struct submodule_t *submodule;
  for (submodule = submodules; submodule->fini; submodule++) {
    submodule->fini();
  }

  Py_DECREF(read_string);

  Py_DECREF(empty_string);
  Py_DECREF(asterisk_string);
  Py_DECREF(space_string);
  Py_DECREF(preserve_string);
  Py_DECREF(default_string);
  Py_DECREF(id_string);
  Py_DECREF(xml_namespace_string);
  Py_DECREF(xml_space_string);
  Py_DECREF(xml_base_string);
  Py_DECREF(xml_lang_string);
  Py_DECREF(base_string);
  Py_DECREF(lang_string);

  Py_DECREF(unicode_space_char);

  Py_DECREF(empty_event);
  Py_DECREF(content_model_empty);
  Py_DECREF(content_model_any);
  Py_DECREF(content_model_pcdata);
  Py_DECREF(attribute_decl_implied);
  Py_DECREF(attribute_decl_required);
  Py_DECREF(attribute_decl_fixed);

  Py_CLEAR(absolutize_function);

  Py_XDECREF(expat_library_error);
}

PyMODINIT_FUNC init_expat(void)
{
  PyObject *module, *import;
  struct submodule_t *submodule;

  XML_Expat_Version version = XML_ExpatVersionInfo();
  const XML_Feature *features = XML_GetFeatureList();
  const XML_Feature *f;

  if ((PycString_IMPORT) == NULL) return;
  if ((XmlString_IMPORT) == NULL) return;

  module = Py_InitModule3("_expat", module_methods, module_doc);
  if (module == NULL) return;

  for (submodule = submodules; submodule->init; submodule++) {
    if (submodule->init(module) < 0) return;
  }

#define DEFINE_OBJECT(name, ob) \
  (name) = (ob);                \
  if ((name) == NULL) return
#define DEFINE_PYSTRING(name, s) \
  DEFINE_OBJECT(name, PyString_FromString(s))
#define DEFINE_XMLSTRING(name, s) \
  DEFINE_OBJECT(name, XmlString_FromASCII(s))

  DEFINE_PYSTRING(read_string, "read");

  DEFINE_XMLSTRING(empty_string, "");
  DEFINE_XMLSTRING(asterisk_string, "*");
  DEFINE_XMLSTRING(space_string, "space");
  DEFINE_XMLSTRING(preserve_string, "preserve");
  DEFINE_XMLSTRING(default_string, "default");
  DEFINE_XMLSTRING(id_string, "id");
  DEFINE_XMLSTRING(xml_space_string, "xml:space");
  DEFINE_XMLSTRING(xml_base_string, "xml:base");
  DEFINE_XMLSTRING(xml_lang_string, "xml:lang");
  DEFINE_XMLSTRING(base_string, "base");
  DEFINE_XMLSTRING(lang_string, "lang");
  DEFINE_XMLSTRING(unicode_space_char, " ");
  DEFINE_XMLSTRING(empty_event, "(#EMPTY)");
  DEFINE_XMLSTRING(content_model_empty, "EMPTY");
  DEFINE_XMLSTRING(content_model_any, "ANY");
  DEFINE_XMLSTRING(content_model_pcdata, "(#PCDATA)");
  DEFINE_XMLSTRING(attribute_decl_implied, "#IMPLIED");
  DEFINE_XMLSTRING(attribute_decl_required, "#REQUIRED");
  DEFINE_XMLSTRING(attribute_decl_fixed, "#FIXED");

  import = PyImport_ImportModule("amara.lib");
  if (import == NULL) return;
  IriError = PyObject_GetAttrString(import, "IriError");
  if (IriError == NULL) {
    Py_DECREF(import);
    return;
  }
  Py_DECREF(import);

  IriError_RESOURCE_ERROR = PyObject_GetAttrString(IriError, "RESOURCE_ERROR");
  if (IriError_RESOURCE_ERROR == NULL) return;

  import = PyImport_ImportModule("amara.lib.iri");
  if (import == NULL) return;
  absolutize_function = PyObject_GetAttrString(import, "absolutize");
  if (absolutize_function == NULL) {
    Py_DECREF(import);
    return;
  }
  Py_DECREF(import);

  import = PyImport_ImportModule("amara");
  if (import == NULL) return;
  xml_namespace_string = PyObject_GetAttrString(import, "XML_NAMESPACE");
  xml_namespace_string = XmlString_FromObjectInPlace(xml_namespace_string);
  if (xml_namespace_string == NULL) {
    Py_DECREF(import);
    return;
  }
  ReaderError = PyObject_GetAttrString(import, "ReaderError");
  if (ReaderError == NULL) {
    Py_DECREF(import);
    return;
  }
  Py_DECREF(import);

  /* Update Expat's memory allocator to use the Python object allocator
   * if it is enabled. */
#ifdef WITH_PYMALLOC
  expat_memsuite.malloc_fcn = PyObject_MALLOC;
  expat_memsuite.realloc_fcn = PyObject_REALLOC;
  expat_memsuite.free_fcn = PyObject_FREE;
#endif

  /* verify Expat linkage due to late binding on Linux */
  expat_library_error = NULL;

  /* ensure that we're going to be using the proper Expat functions */
  if (version.major != XML_MAJOR_VERSION ||
      version.minor != XML_MINOR_VERSION ||
      version.micro != XML_MICRO_VERSION) {
    expat_library_error =
      PyString_FromFormat("Incompatible Expat library found; "          \
                          "version mismatch (expected %d.%d.%d, "       \
                          "found %d.%d.%d)", XML_MAJOR_VERSION,
                          XML_MINOR_VERSION, XML_MICRO_VERSION,
                          version.major, version.minor, version.micro);
    if (expat_library_error != NULL)
      PyErr_Warn(PyExc_RuntimeWarning,
                PyString_AS_STRING(expat_library_error));
    return;
  }

  /* check Expat features that we require depending on how we were
     compiled.  Unfortunately, we cannot test for namespace support.
  */
  for (f = features; f->feature != XML_FEATURE_END; f++) {
    if (f->feature == XML_FEATURE_SIZEOF_XML_CHAR &&
        f->value != sizeof(Py_UNICODE)) {
      expat_library_error =
        PyString_FromString("Incompatible Expat library found; "        \
                            "sizeof(XML_Char) != sizeof(Py_UNICODE)");
      if (expat_library_error != NULL)
        PyErr_Warn(PyExc_RuntimeWarning,
                   PyString_AS_STRING(expat_library_error));
      return;
    }
  }

#define CHECK_FEATURE(NAME)                                             \
  for (f = features; f->feature != XML_FEATURE_ ## NAME; f++) {         \
    if (f->feature == XML_FEATURE_END) {                                \
      expat_library_error =                                             \
        PyString_FromString("Incompatible Expat library found; "        \
                            "missing feature XML_" #NAME);              \
      if (expat_library_error != NULL)                                  \
        PyErr_Warn(PyExc_RuntimeWarning,                                \
                   PyString_AS_STRING(expat_library_error));            \
      return;                                                           \
    }                                                                   \
  }
#ifdef XML_UNICODE
  CHECK_FEATURE(UNICODE);
#endif
#ifdef XML_DTD
  CHECK_FEATURE(DTD);
#endif
#ifdef XML_NS
  CHECK_FEATURE(NS);
#endif
#undef CHECK_FEATURE

  PyModule_AddIntConstant(module, "XPTR_ELEMENT_ID", ELEMENT_ID);
  PyModule_AddIntConstant(module, "XPTR_ELEMENT_COUNT", ELEMENT_COUNT);
  PyModule_AddIntConstant(module, "XPTR_ELEMENT_MATCH", ELEMENT_MATCH);
  PyModule_AddIntConstant(module, "XPTR_ATTRIBUTE_MATCH", ATTRIBUTE_MATCH);

  /* Export C API - done last to serve as a cleanup function as well */
  PyModule_AddObject(module, "CAPI",
                     PyCObject_FromVoidPtr((void *)&Expat_API, fini_expat));
}
