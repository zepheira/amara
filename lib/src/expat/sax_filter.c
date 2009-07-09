#include "expat_interface.h"
#include "attributes.h"
#include "../domlette/domlette_interface.h"

#define DEBUG_SAX

static PyObject *uri_resolver;
static PyObject *xmlns_namespace_string;
static PyObject *feature_external_ges;
static PyObject *feature_external_pes;
static PyObject *feature_namespaces;
static PyObject *feature_namespace_prefixes;
static PyObject *feature_string_interning;
static PyObject *feature_validation;
static PyObject *feature_process_xincludes;
static PyObject *feature_generator;
static PyObject *property_declaration_handler;
static PyObject *property_dom_node;
static PyObject *property_lexical_handler;
/*static PyObject *property_xml_string;*/
static PyObject *property_whitespace_rules;
static PyObject *property_yield_result;
static PyObject *sax_input_source;

enum HandlerTypes {
  /* ContentHandler */
  Handler_SetLocator,
  Handler_StartDocument,
  Handler_EndDocument,
  Handler_StartNamespace,
  Handler_EndNamespace,
  Handler_StartElement,
  Handler_EndElement,
  Handler_Characters,
  Handler_IgnorableWhitespace,
  Handler_ProcessingInstruction,
  Handler_SkippedEntity,

  /* DTDHandler */
  Handler_NotationDecl,
  Handler_UnparsedEntityDecl,

  /* EntityResolver */
  Handler_ResolveEntity,

  /* ErrorHandler */
  Handler_Warning,
  Handler_Error,
  Handler_FatalError,

  /* LexicalHandler */
  Handler_StartDTD,
  Handler_EndDTD,
  Handler_StartCDATA,
  Handler_EndCDATA,
  Handler_Comment,

  /* DeclHandler */
  Handler_ElementDecl,
  Handler_AttributeDecl,
  Handler_InternalEntityDecl,
  Handler_ExternalEntityDecl,

  TotalHandlers
};

typedef struct {
  PyObject_HEAD
  ExpatReader *reader;

  PyObject *content_handler;
  PyObject *dtd_handler;
  PyObject *error_handler;
  PyObject *entity_resolver;

  /* SAX features */
  int generator;

  /* SAX properties */
  PyObject *yield_result;
  NodeObject *dom_node;
  PyObject *decl_handler;
  PyObject *lexical_handler;

  /* Python callbacks */
  PyObject *handlers[TotalHandlers];
} XMLParserObject;

typedef struct {
  PyObject_HEAD
  XMLParserObject *parser;
} SaxGenObject;

/* Cached PyCodeObjects for frames */
static PyCodeObject *tb_codes[TotalHandlers];

/** SAXExceptions *****************************************************/

static PyObject *SAXParseExceptionObject;
static PyObject *SAXNotRecognizedExceptionObject;
static PyObject *SAXNotSupportedExceptionObject;

static PyObject *SAXParseException(PyObject *exception, PyObject *locator)
{
  PyObject *message;

  /* Get the string representation of the exception value */
  message = PyObject_GetAttrString(exception, "message");
  if (message == NULL) {
    return NULL;
  }

  /* Create a SAXParseException for this error */
  return PyObject_CallFunction(SAXParseExceptionObject, "NOO",
                               message, exception, locator);
}

static PyObject *SAXNotRecognizedException(char *msg)
{
  PyObject *obj;

  obj = PyObject_CallFunction(SAXNotRecognizedExceptionObject, "s", msg);
  if (obj) {
    PyErr_SetObject(SAXNotRecognizedExceptionObject, obj);
    Py_DECREF(obj);
  }
  return NULL;
}

static PyObject *SAXNotSupportedException(char *msg)
{
  PyObject *obj;

  obj = PyObject_CallFunction(SAXNotSupportedExceptionObject, "s", msg);
  if (obj) {
    PyErr_SetObject(SAXNotSupportedExceptionObject, obj);
    Py_DECREF(obj);
  }
  return NULL;
}

/** Expat Callback Handlers *******************************************/

#define getcode(slot) _getcode(Handler_##slot, #slot, __LINE__)
Py_LOCAL_INLINE(PyCodeObject *)
_getcode(enum HandlerTypes slot, char *name, int lineno)
{
  if (tb_codes[slot] == NULL)
    tb_codes[slot] = _PyCode_Here(name, __FILE__, lineno);
  return tb_codes[slot];
}

/* Receive notification of the beginning of a document. */
static ExpatStatus sax_StartDocument(void *userData)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler, *args, *result;

  Debug_Print("--- sax_StartDocument(%p)\n", self);

  if ((handler = self->handlers[Handler_SetLocator]) != NULL) {
    /* handler.setDocumentLocator(locator) */
    if ((args = PyTuple_Pack(1, (PyObject *)self)) == NULL)
      return EXPAT_STATUS_ERROR;
    result = PyTrace_CallObject(getcode(SetLocator), handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  if ((handler = self->handlers[Handler_StartDocument]) != NULL) {
    /* handler.startDocument() */
    if ((args = PyTuple_New(0)) == NULL)
      return EXPAT_STATUS_ERROR;
    result = PyTrace_CallObject(getcode(StartDocument), handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

/* Receive notification of the end of a document. */
static ExpatStatus sax_EndDocument(void *userData)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_EndDocument];
  PyObject *args, *result;

  Debug_Print("--- sax_EndDocument(%p)\n", self);

  if (handler != NULL) {
    /* handler.endDocument() */
    if ((args = PyTuple_New(0)) == NULL)
      return EXPAT_STATUS_ERROR;
    result = PyTrace_CallObject(getcode(EndDocument), handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

/* Begin the scope of a prefix-URI Namespace mapping. */
static ExpatStatus sax_StartNamespaceDecl(void *userData, PyObject *prefix,
                                          PyObject *uri)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_StartNamespace];
  PyObject *args, *result;

  Debug_Print("--- sax_StartNamespaceDecl(%p, prefix=", self);
  Debug_PrintObject(prefix);
  Debug_Print(", uri=");
  Debug_PrintObject(uri);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.startNamespace(prefix, uri) */
    if ((args = PyTuple_Pack(2, prefix, uri)) == NULL)
      return EXPAT_STATUS_ERROR;
    result = PyTrace_CallObject(getcode(StartNamespace), handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

/* End the scope of a prefix-URI mapping. */
static ExpatStatus sax_EndNamespaceDecl(void *userData, PyObject *prefix)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_EndNamespace];
  PyObject *args, *result;

  Debug_Print("--- sax_EndNamespaceDecl(%p, prefix=", self);
  Debug_PrintObject(prefix);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.endNamespace(prefix) */
    if ((args = PyTuple_Pack(1, prefix)) == NULL)
      return EXPAT_STATUS_ERROR;
    result = PyTrace_CallObject(getcode(EndNamespace), handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus sax_StartElement(void *userData, ExpatName *name,
                                    ExpatAttribute atts[], size_t natts)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_StartElement];
  PyObject *args, *result;
#if defined(DEBUG_SAX)
  size_t i;
  Debug_Print("--- sax_StartElement(%p, name=", self);
  Debug_PrintObject(name->qualifiedName);
  Debug_Print(", atts={");
  for (i = 0; i < natts; i++) {
    if (i > 0)
      Debug_Print(", ");
    Debug_PrintObject(atts[i].qualifiedName);
    Debug_Print(": ");
    Debug_PrintObject(atts[i].value);
  }
  Debug_Print("})\n");
#endif


  if (handler != NULL) {
    /* handler.startElement((namespaceURI, localName), tagName, attributes) */
    args = Py_BuildValue("(OO)ON", name->namespaceURI, name->localName,
                         name->qualifiedName, Attributes_New(atts, natts));
    if (args == NULL)
      return EXPAT_STATUS_ERROR;
    result = PyTrace_CallObject(getcode(StartElement), handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus sax_EndElement(void *userData, ExpatName *name)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_EndElement];
  PyObject *args, *result;

  Debug_Print("--- sax_EndElement(%p, name=", self);
  Debug_PrintObject(name->qualifiedName);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.endElement((namespaceURI, localName), tagName) */
    args = Py_BuildValue("(OO)O", name->namespaceURI, name->localName,
                         name->qualifiedName);
    if (args == NULL)
      return EXPAT_STATUS_ERROR;
    result = PyTrace_CallObject(getcode(StartElement), handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus sax_CharacterData(void *userData, PyObject *data)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_Characters];
  PyObject *args, *result;

  Debug_Print("--- sax_Characters(%p, data=", self);
  Debug_PrintObject(data);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.characters(content) */
    if ((args = PyTuple_Pack(1, data)) == NULL)
      return EXPAT_STATUS_ERROR;
    result = PyTrace_CallObject(getcode(Characters), handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

/* Receive notification of ignorable whitespace in element content. */
static ExpatStatus sax_IgnorableWhitespace(void *userData, PyObject *data)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_IgnorableWhitespace];
  PyObject *args, *result;

  Debug_Print("--- sax_IgnorableWhitespace(%p, data=", self);
  Debug_PrintObject(data);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.ignoreableWhitespace(content) */
    if ((args = PyTuple_Pack(1, data)) == NULL)
      return EXPAT_STATUS_ERROR;
    result = PyTrace_CallObject(getcode(IgnorableWhitespace), handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

/* Receive notification of a processing instruction. */
static ExpatStatus sax_ProcessingInstruction(void *userData,
                                             PyObject *target,
                                             PyObject *data)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_ProcessingInstruction];
  PyObject *args, *result;

  Debug_Print("--- sax_ProcessingInstruction(%p, target=", self);
  Debug_PrintObject(target);
  Debug_Print(", data=");
  Debug_PrintObject(data);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.processingInstruction(target, data) */
    if ((args = PyTuple_Pack(2, target, data)) == NULL)
      return EXPAT_STATUS_ERROR;
    result = PyTrace_CallObject(getcode(ProcessingInstruction), handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus sax_SkippedEntity(void *userData, PyObject *name)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_SkippedEntity];
  PyObject *args, *result;

  Debug_Print("--- sax_SkippedEntity(%p, name=", self);
  Debug_PrintObject(name);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.skippedEntity(name) */
    if ((args = PyTuple_Pack(1, name)) == NULL)
      return EXPAT_STATUS_ERROR;
    result = PyTrace_CallObject(getcode(SkippedEntity), handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

/* Report the start of DTD declarations, if any. */
static ExpatStatus sax_StartDoctypeDecl(void *userData, PyObject *name,
                                        PyObject *systemId, PyObject *publicId)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_StartDTD];
  PyObject *args, *result;

  Debug_Print("--- sax_StartDoctypeDecl(%p, name=", self);
  Debug_PrintObject(name);
  Debug_Print(", systemId=");
  Debug_PrintObject(systemId);
  Debug_Print(", publicId=");
  Debug_PrintObject(publicId);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.startDTD(name, publicId, systemId) */
    if ((args = PyTuple_New(3)) == NULL) return EXPAT_STATUS_ERROR;
    PyTuple_SET_ITEM(args, 0, name);
    Py_INCREF(name); /* SET_ITEM steals reference */
    PyTuple_SET_ITEM(args, 1, publicId);
    Py_INCREF(publicId); /* SET_ITEM steals reference */
    PyTuple_SET_ITEM(args, 2, systemId);
    Py_INCREF(systemId); /* SET_ITEM steals reference */

    result = PyTrace_CallObject(getcode(StartDTD), handler, args);
    Py_DECREF(args);
    if (result == NULL) return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

/* Report the end of DTD declarations. */
static ExpatStatus sax_EndDoctypeDecl(void *userData)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_EndDTD];
  PyObject *args, *result;

  Debug_Print("--- sax_EndDoctypeDecl(%p)\n", self);

  if (handler != NULL) {
    /* handler.endDTD() */
    if ((args = PyTuple_New(0)) == NULL) return EXPAT_STATUS_ERROR;

    result = PyTrace_CallObject(getcode(EndDTD), handler, args);
    Py_DECREF(args);
    if (result == NULL) return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

/* Report the start of a CDATA section. */
static ExpatStatus sax_StartCdataSection(void *userData)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_StartCDATA];
  PyObject *args, *result;

  Debug_Print("--- sax_StartCdataSection(%p)\n", self);

  if (handler != NULL) {
    /* handler.startCDATA() */
    if ((args = PyTuple_New(0)) == NULL) return EXPAT_STATUS_ERROR;

    result = PyTrace_CallObject(getcode(StartCDATA), handler, args);
    Py_DECREF(args);
    if (result == NULL) return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

/* Report the end of a CDATA section. */
static ExpatStatus sax_EndCdataSection(void *userData)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_EndCDATA];
  PyObject *args, *result;

  Debug_Print("--- sax_EndCdataSection(%p)\n", self);

  if (handler != NULL) {
    /* handler.endCDATA() */
    if ((args = PyTuple_New(0)) == NULL) return EXPAT_STATUS_ERROR;

    result = PyTrace_CallObject(getcode(EndCDATA), handler, args);
    Py_DECREF(args);
    if (result == NULL) return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus sax_Comment(void *userData, PyObject *data)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_Comment];
  PyObject *args, *result;

  Debug_Print("--- sax_Comment(%p, data=", self);
  Debug_PrintObject(data);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.comment(content) */
    if ((args = PyTuple_New(1)) == NULL) return EXPAT_STATUS_ERROR;
    PyTuple_SET_ITEM(args, 0, data);
    Py_INCREF(data); /* SET_ITEM steals reference */

    result = PyTrace_CallObject(getcode(Comment), handler, args);
    Py_DECREF(args);
    if (result == NULL) return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus sax_NotationDecl(void *userData, PyObject *name,
                                    PyObject *publicId, PyObject *systemId)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_NotationDecl];
  PyObject *args, *result;

  Debug_Print("--- sax_NotationDecl(%p, name=", self);
  Debug_PrintObject(name);
  Debug_Print(", systemId=");
  Debug_PrintObject(systemId);
  Debug_Print(", publicId=");
  Debug_PrintObject(publicId);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.notationDecl(name, publicId, systemId) */
    if ((args = PyTuple_New(3)) == NULL) return EXPAT_STATUS_ERROR;
    PyTuple_SET_ITEM(args, 0, name);
    Py_INCREF(name); /* SET_ITEM steals reference */
    PyTuple_SET_ITEM(args, 1, publicId);
    Py_INCREF(publicId); /* SET_ITEM steals reference */
    PyTuple_SET_ITEM(args, 2, systemId);
    Py_INCREF(systemId); /* SET_ITEM steals reference */

    result = PyTrace_CallObject(getcode(NotationDecl), handler, args);
    Py_DECREF(args);
    if (result == NULL) return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus sax_UnparsedEntityDecl(void *userData,
                                          PyObject *name,
                                          PyObject *publicId,
                                          PyObject *systemId,
                                          PyObject *notationName)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_UnparsedEntityDecl];
  PyObject *args, *result;

  Debug_Print("--- sax_UnparsedEntityDecl(%p, name=", self);
  Debug_PrintObject(name);
  Debug_Print(", publicId=");
  Debug_PrintObject(publicId);
  Debug_Print(", systemId=");
  Debug_PrintObject(systemId);
  Debug_Print(", notationName=");
  Debug_PrintObject(notationName);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.unparsedEntityDecl(name, publicId, systemId, notationName) */
    if ((args = PyTuple_New(4)) == NULL) return EXPAT_STATUS_ERROR;
    PyTuple_SET_ITEM(args, 0, name);
    Py_INCREF(name); /* SET_ITEM steals reference */
    PyTuple_SET_ITEM(args, 1, publicId);
    Py_INCREF(publicId); /* SET_ITEM steals reference */
    PyTuple_SET_ITEM(args, 2, systemId);
    Py_INCREF(systemId); /* SET_ITEM steals reference */
    PyTuple_SET_ITEM(args, 3, notationName);
    Py_INCREF(notationName); /* SET_ITEM steals reference */

    result = PyTrace_CallObject(getcode(UnparsedEntityDecl), handler, args);
    Py_DECREF(args);
    if (result == NULL) return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus sax_Warning(void *userData, PyObject *exception)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_Warning];
  PyObject *args, *result;

  Debug_Print("--- sax_Warning(%p, exception=", self);
  Debug_PrintObject(exception);
  Debug_Print(")\n");

  exception = SAXParseException(exception, (PyObject *) self);
  if (exception == NULL) return EXPAT_STATUS_ERROR;

  if (handler != NULL) {
    /* handler.warning(exception) */
    if ((args = PyTuple_New(1)) == NULL) {
      Py_DECREF(exception);
      return EXPAT_STATUS_ERROR;
    }
    PyTuple_SET_ITEM(args, 0, exception);

    result = PyTrace_CallObject(getcode(Warning), handler, args);
    Py_DECREF(args);
    if (result == NULL) return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  } else {
    PyObject *stream = PySys_GetObject("stdout");
    if (stream != NULL) {
      if (PyFile_WriteObject(exception, stream, Py_PRINT_RAW) < 0) {
        Py_DECREF(exception);
        return EXPAT_STATUS_ERROR;
      }
      if (PyFile_WriteString("\n", stream) < 0) {
        Py_DECREF(exception);
        return EXPAT_STATUS_ERROR;
      }
    }
    Py_DECREF(exception);
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus sax_Error(void *userData, PyObject *exception)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_Error];
  PyObject *args, *result;

  Debug_Print("--- sax_Error(%p, exception=", self);
  Debug_PrintObject(exception);
  Debug_Print(")\n");

  exception = SAXParseException(exception, (PyObject *) self);
  if (exception == NULL) return EXPAT_STATUS_ERROR;

  if (handler != NULL) {
    /* handler.error(exception) */
    if ((args = PyTuple_New(1)) == NULL) {
      Py_DECREF(exception);
      return EXPAT_STATUS_ERROR;
    }
    PyTuple_SET_ITEM(args, 0, exception);

    result = PyTrace_CallObject(getcode(Error), handler, args);
    Py_DECREF(args);
    if (result == NULL) return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  } else {
    PyErr_SetObject(PyExceptionInstance_Class(exception), exception);
    Py_DECREF(exception);
    return EXPAT_STATUS_ERROR;
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus sax_FatalError(void *userData, PyObject *exception)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_FatalError];
  PyObject *args, *result;

  Debug_Print("--- sax_FatalError(%p, exception=", self);
  Debug_PrintObject(exception);
  Debug_Print(")\n");

  exception = SAXParseException(exception, (PyObject *) self);
  if (exception == NULL)
    return EXPAT_STATUS_ERROR;
  if (handler != NULL) {
    /* handler.fatalError(exception) */
    if ((args = PyTuple_New(1)) == NULL) {
      Py_DECREF(exception);
      return EXPAT_STATUS_ERROR;
    }
    PyTuple_SET_ITEM(args, 0, exception);

    result = PyTrace_CallObject(getcode(FatalError), handler, args);
    Py_DECREF(args);
    if (result == NULL) return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  } else {
    PyErr_SetObject(PyExceptionInstance_Class(exception), exception);
    Py_DECREF(exception);
    return EXPAT_STATUS_ERROR;
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus sax_ElementDecl(void *userData, PyObject *name,
                                   PyObject *model)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_ElementDecl];
  PyObject *args, *result;

  Debug_Print("--- sax_ElementDecl(%p, name=", self);
  Debug_PrintObject(name);
  Debug_Print(", model=");
  Debug_PrintObject(model);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.elementDecl(name, model) */
    if ((args = PyTuple_Pack(2, name, model)) == NULL)
      return EXPAT_STATUS_ERROR;
    result = PyTrace_CallObject(getcode(ElementDecl), handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus sax_AttributeDecl(void *userData, PyObject *eName,
                                     PyObject *aName, PyObject *type,
                                     PyObject *decl, PyObject *value)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_AttributeDecl];
  PyObject *args, *result;

  Debug_Print("--- sax_AttributeDecl(%p, eName=", self);
  Debug_PrintObject(eName);
  Debug_Print(", aName=");
  Debug_PrintObject(aName);
  Debug_Print(", type=");
  Debug_PrintObject(type);
  Debug_Print(", decl=");
  Debug_PrintObject(decl);
  Debug_Print(", value=");
  Debug_PrintObject(value);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.attributeDecl(eName, aName, type, decl, value) */
    if ((args = PyTuple_Pack(5, eName, aName, type, decl, value)) == NULL)
      return EXPAT_STATUS_ERROR;
    result = PyTrace_CallObject(getcode(AttributeDecl), handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus sax_InternalEntityDecl(void *userData, PyObject *name,
                                          PyObject *value)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_InternalEntityDecl];
  PyObject *args, *result;

  Debug_Print("--- sax_InternalEntityDecl(%p, name=", self);
  Debug_PrintObject(name);
  Debug_Print(", value=");
  Debug_PrintObject(value);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.internalEntityDecl(name, value) */
    if ((args = PyTuple_Pack(2, name, value)) == NULL)
      return EXPAT_STATUS_ERROR;
    result = PyTrace_CallObject(getcode(InternalEntityDecl), handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

static ExpatStatus sax_ExternalEntityDecl(void *userData,
                                          PyObject *name,
                                          PyObject *publicId,
                                          PyObject *systemId)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_ExternalEntityDecl];
  PyObject *args, *result;

  Debug_Print("--- sax_ExternalEntityDecl(%p, name=", self);
  Debug_PrintObject(name);
  Debug_Print(", publicId=");
  Debug_PrintObject(publicId);
  Debug_Print(", systemId=");
  Debug_PrintObject(systemId);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.externalEntityDecl(name, publicId, systemId) */
    if ((args = PyTuple_Pack(3, name, publicId, systemId)) == NULL)
      return EXPAT_STATUS_ERROR;
    result = PyTrace_CallObject(getcode(ExternalEntityDecl), handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return EXPAT_STATUS_ERROR;
    Py_DECREF(result);
  }
  return EXPAT_STATUS_OK;
}

static PyObject *sax_ResolveEntity(void *userData, PyObject *publicId,
                                   PyObject *systemId)
{
  XMLParserObject *self = (XMLParserObject *) userData;
  PyObject *handler = self->handlers[Handler_ResolveEntity];
  PyObject *args, *result;

  Debug_Print("--- sax_ResolveEntity(%p, publicId=", self);
  Debug_PrintObject(publicId);
  Debug_Print(", systemId=");
  Debug_PrintObject(systemId);
  Debug_Print(")\n");

  if (handler != NULL) {
    /* handler.resolveEntity(publicId, systemId) */
    if ((args = PyTuple_Pack(2, publicId, systemId)) == NULL)
      return NULL;
    result = PyTrace_CallObject(getcode(ResolveEntity), handler, args);
    Py_DECREF(args);
  } else {
    Py_INCREF(Py_None);
    result = Py_None;
  }
  return result;
}

static ExpatHandlers sax_handlers = {
  /* start_filter           */ NULL,
  /* end_filter             */ NULL,
  /* start_document         */ sax_StartDocument,
  /* end_document           */ sax_EndDocument,
  /* start_element          */ sax_StartElement,
  /* end_element            */ sax_EndElement,
  /* attribute              */ NULL, /* FIXME: add attribute buffering */
  /* characters             */ sax_CharacterData,
  /* ignorable_whitespace   */ sax_IgnorableWhitespace,
  /* processing_instruction */ sax_ProcessingInstruction,
  /* comment                */ sax_Comment,
  /* start_namespace_decl   */ sax_StartNamespaceDecl,
  /* end_namespace_decl     */ sax_EndNamespaceDecl,
  /* start_doctype_decl     */ sax_StartDoctypeDecl,
  /* end_doctype_decl       */ sax_EndDoctypeDecl,
  /* element_decl           */ sax_ElementDecl,
  /* attribute_decl         */ sax_AttributeDecl,
  /* internal_entity_decl   */ sax_InternalEntityDecl,
  /* external_entity_decl   */ sax_ExternalEntityDecl,
  /* unparsed_entity_decl   */ sax_UnparsedEntityDecl,
  /* notation_decl          */ sax_NotationDecl,
  /* skipped_entity         */ sax_SkippedEntity,
  /* start_cdata_section    */ sax_StartCdataSection,
  /* end_cdata_section      */ sax_EndCdataSection,
  /* warning                */ sax_Warning,
  /* error                  */ sax_Error,
  /* fatal_error            */ sax_FatalError,
  /* resolve_entity         */ sax_ResolveEntity,
};

/** DOMWalker *********************************************************/

static PyObject *get_prefix(PyObject *nodeName)
{
  Py_UNICODE *p;
  Py_ssize_t len, i;

  p = PyUnicode_AS_UNICODE(nodeName);
  len = PyUnicode_GET_SIZE(nodeName);
  for (i = 0; i < len; i++) {
    if (p[i] == ':') {
      return PyUnicode_FromUnicode(p, i);
    }
  }
  Py_INCREF(Py_None);
  return Py_None;
}

static int domwalker_visit(XMLParserObject *parser,
                           NodeObject *node,
                           PyObject *current_namespaces,
                           int preserve_whitespace)
{
  if (Element_Check(node)) {
    PyObject *new_namespaces, *attrs, *prefixes, *namespaceURI, *prefix;
    PyObject *key, *value;
    PyObject *handler, *args, *result;
    Py_ssize_t i;

    attrs = Attributes_New(NULL, 0);
    if (attrs == NULL) {
      return 0;
    }

    new_namespaces = PyDict_New();
    if (new_namespaces == NULL) {
      Py_DECREF(attrs);
      return 0;
    }

    /** Attributes ************************************************/

    /* Create expat-style attribute names and trim out namespaces */
    i = 0;
    while (PyDict_Next(Element_ATTRIBUTES(node), &i, &key, &value)) {
      PyObject *nodeName, *localName, *nodeValue;
      namespaceURI = Attr_GET_NAMESPACE_URI(value);
      nodeName = Attr_GET_QNAME(value);
      localName = Attr_GET_LOCAL_NAME(value);
      nodeValue = Attr_GET_VALUE(value);

      /* get the prefix/namespaceURI pair to add */
      switch (PyObject_RichCompareBool(namespaceURI, xmlns_namespace_string,
                                       Py_EQ)) {
      case 0: /* normal attribute */
        /* DOM doesn't need separate namespace declarations */
        if (namespaceURI != Py_None) {
          PyObject *prefix = get_prefix(nodeName);
          if (prefix == NULL) {
            Py_DECREF(new_namespaces);
            Py_DECREF(attrs);
            return 0;
          }
          if (PyDict_SetItem(new_namespaces, prefix, namespaceURI)) {
            Py_DECREF(prefix);
            Py_DECREF(new_namespaces);
            Py_DECREF(attrs);
            return 0;
          }
          Py_DECREF(prefix);
        }

        if (Attributes_SetItem(attrs, namespaceURI, localName, nodeName,
                               nodeValue) < 0) {
          Py_DECREF(new_namespaces);
          Py_DECREF(attrs);
          return 0;
        }
        break;
      case 1: /* namespace attribute */
        if (PyUnicode_AS_UNICODE(nodeName)[5] == ':') {
          /* xmlns:foo = 'namespaceURI' */
          prefix = localName;
        } else {
          /* xmlns = 'namespaceURI' */
          prefix = Py_None;
        }
        if (PyDict_SetItem(new_namespaces, prefix, nodeValue)) {
          Py_DECREF(new_namespaces);
          Py_DECREF(attrs);
          return 0;
        }
        break;
      default:
        return -1;
      }
    }

    /* DOM doesn't need separate namespace declarations */
    namespaceURI = Element_NAMESPACE_URI(node);
    prefix = get_prefix(Element_QNAME(node));
    if (prefix == NULL) {
      Py_DECREF(new_namespaces);
      Py_DECREF(attrs);
      return 0;
    }
    if (namespaceURI != Py_None) {
      if (PyDict_SetItem(new_namespaces, prefix, namespaceURI)) {
        Py_DECREF(prefix);
        Py_DECREF(new_namespaces);
        Py_DECREF(attrs);
        return 0;
      }
    }
    Py_DECREF(prefix);

    /* notify start of namespace declaration(s) */
    current_namespaces = PyDict_Copy(current_namespaces);
    if (current_namespaces == NULL) {
      Py_DECREF(new_namespaces);
      Py_DECREF(attrs);
      return 0;
    }
    prefixes = PyList_New(0);
    if (prefixes == NULL) {
      Py_DECREF(current_namespaces);
      Py_DECREF(new_namespaces);
      Py_DECREF(attrs);
      return 0;
    }

    i = 0;
    while (PyDict_Next(new_namespaces, &i, &key, &value)) {
      namespaceURI = PyDict_GetItem(current_namespaces, key);
      if (namespaceURI == NULL ||
          PyObject_RichCompareBool(namespaceURI, value, Py_NE)) {
        if (PyDict_SetItem(current_namespaces, key, value) ||
            PyList_Append(prefixes, key)) {
          Py_DECREF(prefixes);
          Py_DECREF(current_namespaces);
          Py_DECREF(new_namespaces);
          Py_DECREF(attrs);
          return 0;
        }

        sax_StartNamespaceDecl(parser, key, value);
        if (PyErr_Occurred()) {
          Py_DECREF(prefixes);
          Py_DECREF(current_namespaces);
          Py_DECREF(new_namespaces);
          Py_DECREF(attrs);
          return 0;
        }
      }
    }
    Py_DECREF(new_namespaces);

    /* report element start */
    handler = parser->handlers[Handler_StartElement];
    if (handler != NULL) {
      args = Py_BuildValue("(OO)OO",
                           Element_NAMESPACE_URI(node),
                           Element_LOCAL_NAME(node),
                           Element_QNAME(node),
                           attrs);
      if (args == NULL) {
        Py_DECREF(current_namespaces);
        Py_DECREF(prefixes);
        Py_DECREF(attrs);
        return 0;
      }
      result = PyTrace_CallObject(getcode(StartElement), handler, args);
      Py_DECREF(args);
      if (result == NULL) {
        Py_DECREF(current_namespaces);
        Py_DECREF(prefixes);
        Py_DECREF(attrs);
        return 0;
      }
      Py_DECREF(result);
    }
    Py_DECREF(attrs);

//    /* update preserving whitespace state for child nodes */
//    preserve_whitespace =
//      Expat_IsWhitespacePreserving(parser->reader,
//                                   Element_NAMESPACE_URI(node),
//                                   Element_LOCAL_NAME(node));

    /* process the children */
    for (i = 0; i < Container_GET_COUNT(node); i++) {
      NodeObject *child = Container_GET_CHILD(node, i);
      if (domwalker_visit(parser, child, current_namespaces,
                          preserve_whitespace) == 0) {
        Py_DECREF(current_namespaces);
        Py_DECREF(prefixes);
        return 0;
      }
    }

    /* report element end */
    handler = parser->handlers[Handler_EndElement];
    if (handler != NULL) {
      args = Py_BuildValue("(OO)O",
                           Element_NAMESPACE_URI(node),
                           Element_LOCAL_NAME(node),
                           Element_QNAME(node));
      if (args == NULL) {
        Py_DECREF(current_namespaces);
        Py_DECREF(prefixes);
        return 0;
      }
      result = PyTrace_CallObject(getcode(StartElement), handler, args);
      Py_DECREF(args);
      if (result == NULL) {
        Py_DECREF(current_namespaces);
        Py_DECREF(prefixes);
        return 0;
      }
      Py_DECREF(result);
    }
    Py_DECREF(current_namespaces);

    /* report end of namespace declaration(s) */
    for (i = 0; i < PyList_GET_SIZE(prefixes); i++) {
      sax_EndNamespaceDecl(parser, PyList_GET_ITEM(prefixes, i));
      if (PyErr_Occurred()) {
        Py_DECREF(prefixes);
        return 0;
      }
    }
    Py_DECREF(prefixes);
  }
  else if (Text_Check(node)) {
    PyObject *data = Text_GET_VALUE(node);
    if (preserve_whitespace)
      sax_CharacterData(parser, data);
    else if (XmlString_IsSpace(data))
      sax_IgnorableWhitespace(parser, data);
    else
      sax_CharacterData(parser, data);
    if (PyErr_Occurred()) return 0;
  }

  return 1;
}

static ExpatStatus ParseDOM(XMLParserObject *parser)
{
  PyObject *namespaces;
  Py_ssize_t i;

  sax_StartDocument(parser);
  if (PyErr_Occurred()) return EXPAT_STATUS_ERROR;

  namespaces = PyDict_New();
  if (namespaces == NULL) return EXPAT_STATUS_ERROR;

  for (i = 0; i < Container_GET_COUNT(parser->dom_node); i++) {
    NodeObject *node = Container_GET_CHILD(parser->dom_node, i);
    if (domwalker_visit(parser, node, namespaces, 1) == 0) {
      Py_DECREF(namespaces);
      return EXPAT_STATUS_ERROR;
    }
  }
  Py_DECREF(namespaces);

  sax_EndDocument(parser);
  if (PyErr_Occurred()) return EXPAT_STATUS_ERROR;

  return EXPAT_STATUS_OK;
}

/**********************************************************************/
/** Python Objects ****************************************************/
/**********************************************************************/

#define METHOD_DOC(PREFIX, NAME) \
static char PREFIX##_##NAME##_doc[]

#define METHOD_DEF(PREFIX, NAME, OBJECT) \
static PyObject * PREFIX##_##NAME(OBJECT *self, PyObject *args)

#define Py_METHOD(PREFIX, NAME) \
  { #NAME, (PyCFunction) PREFIX##_##NAME, METH_VARARGS, PREFIX##_##NAME##_doc }

#define Py_MEMBER(NAME, TYPE, OBJECT) \
  { #NAME, TYPE, offsetof(OBJECT, NAME), 0 }

/********** XMLPARSERITER **********/

static void saxgen_dealloc(SaxGenObject *self)
{
  PyObject_GC_UnTrack(self);
  Py_XDECREF(self->parser);
  PyObject_GC_Del(self);
}

static int saxgen_traverse(SaxGenObject *self, visitproc visit, void *arg)
{
  return visit((PyObject *)self->parser, arg);
}

static PyObject *saxgen_iter(SaxGenObject *self)
{
  Py_INCREF(self);
  return (PyObject *)self;
}

static PyObject *saxgen_iternext(SaxGenObject *self)
{
  PyObject *result;

  if (ExpatReader_GetParsingStatus(self->parser->reader)) {
    /* Still parsing (either suspended or actively) */
    if (self->parser->yield_result == NULL) {
      /* Resume parsing to get the next value.  Returns when suspended or
       * totally completed. */
      if (ExpatReader_Resume(self->parser->reader) == EXPAT_STATUS_ERROR) {
        return NULL;
      }
    }
  }

  /* Consume the yieled value */
  result = self->parser->yield_result;
  self->parser->yield_result = NULL;

  return result;
}

static char saxgen_doc[] =
"SAX event generator.";

static PyTypeObject SaxGenerator_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Expat_MODULE_NAME "." "SaxGenerator",
  /* tp_basicsize      */ sizeof(SaxGenObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) saxgen_dealloc,
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
  /* tp_flags          */ Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
  /* tp_doc            */ (char *) saxgen_doc,
  /* tp_traverse       */ (traverseproc) saxgen_traverse,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) saxgen_iter,
  /* tp_iternext       */ (iternextfunc) saxgen_iternext,
  /* tp_methods        */ (PyMethodDef *) 0,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
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

static PyObject *SaxGen_New(XMLParserObject *parser)
{
  SaxGenObject *self;

  self = PyObject_GC_New(SaxGenObject, &SaxGenerator_Type);
  if (self != NULL) {
    Py_INCREF(parser);
    self->parser = parser;
    PyObject_GC_Track(self);
  }

  return (PyObject *) self;
}

/********** XMLPARSER **********/

#define XMLPARSER_METHOD_DOC(NAME) METHOD_DOC(parser, NAME)
#define XMLPARSER_METHOD_DEF(NAME) METHOD_DEF(parser, NAME, XMLParserObject)
#define Py_XMLPARSER_METHOD(NAME) Py_METHOD(parser, NAME)
#define Py_XMLPARSER_MEMBER(NAME, TYPE) Py_MEMBER(NAME, TYPE, XMLParserObject)

Py_LOCAL_INLINE(PyObject *)
prepare_input_source(PyObject *source)
{
  int rc;
  PyObject *systemId, *byteStream, *encoding;

  if (InputSource_Check(source)) {
    Py_INCREF(source);
    return source;
  }

  rc = PyObject_IsInstance(source, sax_input_source);
  if (rc == -1)
    return NULL;
  else if (rc) {
    systemId = PyObject_CallMethod(source, "getSystemId", NULL);
    byteStream = PyObject_CallMethod(source, "getByteStream", NULL);
    encoding = PyObject_CallMethod(source, "getEncoding", NULL);
    if (byteStream == NULL || systemId == NULL || encoding == NULL) {
      Py_XDECREF(byteStream);
      Py_XDECREF(systemId);
      Py_XDECREF(encoding);
      return NULL;
    }
    source = PyObject_CallFunction((PyObject *)&InputSource_Type, "NNN",
                                   byteStream, systemId, encoding);
  }
  /* check for stream */
  else if (PyObject_HasAttrString(source, "read")) {
    systemId = PyObject_GetAttrString(source, "name");
    if (systemId == NULL) {
      PyErr_Clear();
      Py_INCREF(Py_None);
      systemId = Py_None;
    }
    encoding = PyObject_GetAttrString(source, "encoding");
    if (encoding == NULL) {
      PyErr_Clear();
      Py_INCREF(Py_None);
      encoding = Py_None;
    }
    source = PyObject_CallFunction((PyObject *)&InputSource_Type, "ONN",
                                   source, systemId, encoding);
  }
  /* check for URL */
  else if (PyString_Check(source) || PyUnicode_Check(source)) {
    byteStream = PyObject_CallMethod(uri_resolver, "resolve", "O", source);
    if (byteStream == NULL) {
      return NULL;
    }
    source = PyObject_CallFunction((PyObject *)&InputSource_Type, "NOO",
                                   byteStream, source, Py_None);
  }
  else {
    /* error */
    PyErr_SetString(PyExc_TypeError, "expected InputSource, stream or URL");
    source = NULL;
  }
  return source;
}


XMLPARSER_METHOD_DOC(getContentHandler) = \
"getContentHandler()\n\
\n\
Return the current ContentHandler.";

XMLPARSER_METHOD_DEF(getContentHandler)
{
  PyObject *handler;

  if (!PyArg_ParseTuple(args, ":getContentHandler"))
    return NULL;

  if (self->content_handler != NULL)
    handler = self->content_handler;
  else
    handler = Py_None;

  Py_INCREF(handler);
  return handler;
}


XMLPARSER_METHOD_DOC(setContentHandler) = \
"setContentHandler(handler)\n\
\n\
Registers a handler to receive document content events.";

XMLPARSER_METHOD_DEF(setContentHandler)
{
  PyObject *handler, *temp;

  if (!PyArg_ParseTuple(args, "O:setContentHandler", &handler))
    return NULL;

  if (handler == Py_None)
    handler = NULL;
  else
    Py_INCREF(handler);
  temp = self->content_handler;
  self->content_handler = handler;
  Py_XDECREF(temp);

#define GET_CALLBACK(TYPE, NAME)                                        \
  temp = self->handlers[Handler_##TYPE];                                \
  self->handlers[Handler_##TYPE] = PyObject_GetAttrString(handler, NAME); \
  Py_XDECREF(temp);

  GET_CALLBACK(SetLocator, "setDocumentLocator");
  GET_CALLBACK(StartDocument, "startDocument");
  GET_CALLBACK(EndDocument, "endDocument");
  GET_CALLBACK(StartNamespace, "startPrefixMapping");
  GET_CALLBACK(EndNamespace, "endPrefixMapping");
  GET_CALLBACK(StartElement, "startElementNS");
  GET_CALLBACK(EndElement, "endElementNS");
  GET_CALLBACK(Characters, "characters");
  GET_CALLBACK(IgnorableWhitespace, "ignorableWhitespace");
  GET_CALLBACK(ProcessingInstruction, "processingInstruction");
  GET_CALLBACK(SkippedEntity, "skippedEntity");
#undef GET_CALLBACK

  /* ignore any undefined event handler errors */
  PyErr_Clear();

  Py_INCREF(Py_None);
  return Py_None;
}


XMLPARSER_METHOD_DOC(getEntityResolver) = \
"getEntityResolver()\n\
\n\
Return the current EntityResolver.";

XMLPARSER_METHOD_DEF(getEntityResolver)
{
  PyObject *resolver;

  if (!PyArg_ParseTuple(args, ":getEntityResolver"))
    return NULL;

  if (self->entity_resolver != NULL)
    resolver = self->entity_resolver;
  else
    resolver = Py_None;

  Py_INCREF(resolver);
  return resolver;
}


XMLPARSER_METHOD_DOC(setEntityResolver) = \
"setEntityResolver(resolver)\n\
\n\
Set the current EntityResolver.\n\
\n\
If no EntityResolver is set, attempts to resolve an external entity will\n\
result in opening the system identifier for the entity, and fail if it is\n\
not available.";

XMLPARSER_METHOD_DEF(setEntityResolver)
{
  PyObject *resolver, *temp;

  if (!PyArg_ParseTuple(args, "O:setEntityResolver", &resolver))
    return NULL;

  if (resolver == Py_None)
    resolver = NULL;
  else
    Py_INCREF(resolver);
  temp = self->entity_resolver;
  self->entity_resolver = resolver;
  Py_XDECREF(temp);

#define GET_CALLBACK(TYPE, NAME)                                        \
  temp = self->handlers[Handler_##TYPE];                                \
  self->handlers[Handler_##TYPE] = PyObject_GetAttrString(resolver, NAME); \
  Py_XDECREF(temp);

  GET_CALLBACK(ResolveEntity, "resolveEntity");
#undef GET_CALLBACK

  /* ignore any undefined event handler errors */
  PyErr_Clear();

  Py_INCREF(Py_None);
  return Py_None;
}


XMLPARSER_METHOD_DOC(getErrorHandler) = \
"getErrorHandler()\n\
\n\
Return the current ErrorHandler or None if none has been registered.";

XMLPARSER_METHOD_DEF(getErrorHandler)
{
  PyObject *handler;

  if (!PyArg_ParseTuple(args, ":getErrorHandler"))
    return NULL;

  if (self->error_handler != NULL)
    handler = self->error_handler;
  else
    handler = Py_None;

  Py_INCREF(handler);
  return handler;
}


XMLPARSER_METHOD_DOC(setErrorHandler) = \
"setErrorHandler(handler)\n\
\n\
Set the current error handler.\n\
\n\
If no ErrorHandler is set, errors will be raised as exceptions, and\n\
warnings will be silently ignored.";

XMLPARSER_METHOD_DEF(setErrorHandler)
{
  PyObject *handler, *temp;

  if (!PyArg_ParseTuple(args, "O:setErrorHandler", &handler))
    return NULL;

  if (handler == Py_None)
    handler = NULL;
  else
    Py_INCREF(handler);
  temp = self->error_handler;
  self->error_handler = handler;
  Py_XDECREF(temp);

#define GET_CALLBACK(TYPE, NAME)                                        \
  temp = self->handlers[Handler_##TYPE];                                \
  self->handlers[Handler_##TYPE] = PyObject_GetAttrString(handler, NAME); \
  Py_XDECREF(temp);

  GET_CALLBACK(Warning, "warning");
  GET_CALLBACK(Error, "error");
  GET_CALLBACK(FatalError, "fatalError");
#undef GET_CALLBACK

  /* ignore any undefined event handler errors */
  PyErr_Clear();

  Py_INCREF(Py_None);
  return Py_None;
}

XMLPARSER_METHOD_DOC(getDTDHandler) = \
"getDTDHandler()\n\
\n\
Return the current DTDHandler or None if none has been registered.";

XMLPARSER_METHOD_DEF(getDTDHandler)
{
  PyObject *handler;

  if (!PyArg_ParseTuple(args, ":getDTDHandler"))
    return NULL;

  if (self->dtd_handler != NULL)
    handler = self->dtd_handler;
  else
    handler = Py_None;

  Py_INCREF(handler);
  return handler;
}


XMLPARSER_METHOD_DOC(setDTDHandler) = \
"setDTDHandler(handler)\n\
\n\
Set the current DTDHandler.\n\
\n\
If no DTDHandler is set, DTD events will be discarded.";

XMLPARSER_METHOD_DEF(setDTDHandler)
{
  PyObject *handler, *temp;

  if (!PyArg_ParseTuple(args, "O:setDTDHandler", &handler))
    return NULL;

  if (handler == Py_None)
    handler = NULL;
  else
    Py_INCREF(handler);
  temp = self->dtd_handler;
  self->dtd_handler = handler;
  Py_XDECREF(temp);

#define GET_CALLBACK(TYPE, NAME)                                        \
  temp = self->handlers[Handler_##TYPE];                                \
  self->handlers[Handler_##TYPE] = PyObject_GetAttrString(handler, NAME); \
  Py_XDECREF(temp);

  GET_CALLBACK(NotationDecl, "notationDecl");
  GET_CALLBACK(UnparsedEntityDecl, "unparsedEntityDecl");
#undef GET_CALLBACK

  /* ignore any undefined event handler errors */
  PyErr_Clear();

  Py_INCREF(Py_None);
  return Py_None;
}

XMLPARSER_METHOD_DOC(parse) = \
"parse(source)\n\
\n\
Parse an XML document from an InputSource.";

XMLPARSER_METHOD_DEF(parse)
{
  PyObject *source;
  ExpatStatus status;

  if (!PyArg_ParseTuple(args, "O:parse", &source))
    return NULL;

  if (self->dom_node) {
    /* walk over a DOM, ignoring the source argument */
    status = ParseDOM(self);
  } else {
    source = prepare_input_source(source);
    if (source == NULL) return NULL;

    /* parse the document indicated by the InputSource */
    status = ExpatReader_Parse(self->reader, source);
    Py_DECREF(source);
  }

  if (status == EXPAT_STATUS_ERROR) {
    return NULL;
  }

  if (self->generator) {
    return SaxGen_New(self);
  } else {
    Py_INCREF(Py_None);
    return Py_None;
  }
}

XMLPARSER_METHOD_DOC(getFeature) = \
"getFeature(featurename)\n\
\n\
Return the current setting for feature featurename. If the feature\n\
is not recognized, SAXNotRecognizedException is raised. The well-known\n\
featurenames are listed in the module xml.sax.handler.";

XMLPARSER_METHOD_DEF(getFeature)
{
  PyObject *featurename;
  PyObject *state;

  if (!PyArg_ParseTuple(args, "O:getFeature", &featurename))
    return NULL;

  /* SAX features */
  if (PyObject_RichCompareBool(featurename, feature_validation,
                                    Py_EQ)) {
    state = ExpatReader_GetValidation(self->reader) ? Py_True : Py_False;
  }
  else if (PyObject_RichCompareBool(featurename, feature_external_ges,
                                    Py_EQ)) {
    state = Py_True;
  }
  else if (PyObject_RichCompareBool(featurename, feature_external_pes,
                                    Py_EQ)) {
    if (ExpatReader_GetValidation(self->reader)) {
      /* always true if validating */
      state = Py_True;
    } else {
      state = ExpatReader_GetParamEntityParsing(self->reader) ? Py_True
                                                              : Py_False;
    }
  }
  else if (PyObject_RichCompareBool(featurename, feature_namespaces, Py_EQ)) {
    state = Py_True;
  }
  else if (PyObject_RichCompareBool(featurename, feature_namespace_prefixes,
                                    Py_EQ)) {
    state = Py_False;
  }
  else if (PyObject_RichCompareBool(featurename, feature_string_interning,
                                    Py_EQ)) {
    state = Py_True;
  }
  /* 4Suite-specific features */
//  else if (PyObject_RichCompareBool(featurename, feature_process_xincludes,
//                                    Py_EQ)) {
//    state = Expat_GetXIncludeProcessing(self->reader) ? Py_True : Py_False;
//  }
  else if (PyObject_RichCompareBool(featurename, feature_generator, Py_EQ)) {
    state = self->generator ? Py_True : Py_False;
  }
  else {
    PyObject *repr = PyObject_Repr(featurename);
    if (repr) {
      SAXNotRecognizedException(PyString_AsString(repr));
      Py_DECREF(repr);
    }
    return NULL;
  }

  Py_INCREF(state);
  return state;
}

XMLPARSER_METHOD_DOC(setFeature) = \
"setFeature(featurename, value)\n\
\n\
Set the featurename to value. If the feature is not recognized,\n\
SAXNotRecognizedException is raised. If the feature or its setting\n\
is not supported by the parser, SAXNotSupportedException is raised.";

XMLPARSER_METHOD_DEF(setFeature)
{
  PyObject *featurename, *value;
  int state;

  if (!PyArg_ParseTuple(args, "OO:setFeature", &featurename, &value))
    return NULL;

  if ((state = PyObject_IsTrue(value)) == -1) return NULL;

  if (ExpatReader_GetParsingStatus(self->reader)) {
    return SAXNotSupportedException("cannot set features while parsing");
  }
  /* SAX features */
  else if (PyObject_RichCompareBool(featurename, feature_validation,
                                    Py_EQ)) {
    ExpatReader_SetValidation(self->reader, state);
  }
  else if (PyObject_RichCompareBool(featurename, feature_external_ges,
                                    Py_EQ)) {
    if (state == 0)
      return SAXNotSupportedException(
                "external general entities always processed");
  }
  else if (PyObject_RichCompareBool(featurename, feature_external_pes,
                                    Py_EQ)) {
    ExpatReader_SetParamEntityParsing(self->reader, state);
  }
  else if (PyObject_RichCompareBool(featurename, feature_namespaces, Py_EQ)) {
    if (state == 0)
      return SAXNotSupportedException("namespace processing always enabled");
  }
  else if (PyObject_RichCompareBool(featurename, feature_namespace_prefixes,
                                    Py_EQ)) {
    if (state == 1)
      return SAXNotSupportedException("namespace prefixes never reported");
  }
  else if (PyObject_RichCompareBool(featurename, feature_string_interning,
                                    Py_EQ)) {
    if (state == 0)
      return SAXNotSupportedException("string interning always enabled");
  }
  /* 4Suite-specific features */
//  else if (PyObject_RichCompareBool(featurename, feature_process_xincludes,
//                                    Py_EQ)) {
//    Expat_SetXIncludeProcessing(self->reader, state);
//  }
  else if (PyObject_RichCompareBool(featurename, feature_generator, Py_EQ)) {
    self->generator = state;
    if (state == 0 && self->yield_result) {
      Py_DECREF(self->yield_result);
      self->yield_result = NULL;
    }
  }
  else {
    PyObject *repr = PyObject_Repr(featurename);
    if (repr) {
      SAXNotRecognizedException(PyString_AsString(repr));
      Py_DECREF(repr);
    }
    return NULL;
  }

  Py_INCREF(Py_None);
  return Py_None;
}

XMLPARSER_METHOD_DOC(getProperty) = \
"getProperty(propertyname)\n\
\n\
Return the current setting for property propertyname. If the property is\n\
not recognized, a SAXNotRecognizedException is raised. The well-known\n\
propertynames are listed in the module xml.sax.handler.";

XMLPARSER_METHOD_DEF(getProperty)
{
  PyObject *propertyname, *value;

  if (!PyArg_ParseTuple(args, "O:getProperty", &propertyname))
    return NULL;

  if (PyObject_RichCompareBool(propertyname, property_lexical_handler,
                                    Py_EQ)) {
    if (self->lexical_handler == NULL)
      value = Py_None;
    else
      value = self->lexical_handler;
    Py_INCREF(value);
  }
  else if (PyObject_RichCompareBool(propertyname, property_declaration_handler,
                                    Py_EQ)) {
    if (self->decl_handler == NULL)
      value = Py_None;
    else
      value = self->decl_handler;
    Py_INCREF(value);
  }
  else if (PyObject_RichCompareBool(propertyname, property_dom_node,
                                    Py_EQ)) {
    if (self->dom_node == NULL)
      value = Py_None;
    else
      value = (PyObject*) self->dom_node;
    Py_INCREF(value);
  }
  /* 4Suite-specific properties */
  else if (PyObject_RichCompareBool(propertyname, property_whitespace_rules,
                                    Py_EQ)) {
    /* XSLT-style whitespace stripping rules */
    value = ExpatReader_GetWhitespaceStripping(self->reader);
  }
  else if (PyObject_RichCompareBool(propertyname, property_yield_result,
                                    Py_EQ)) {
    /* result value used when generator feature is enabled */
    if (self->yield_result == NULL) {
      value = Py_None;
    } else {
      value = self->yield_result;
    }
    Py_INCREF(value);
  }
  else {
    PyObject *repr = PyObject_Repr(propertyname);
    if (repr) {
      SAXNotRecognizedException(PyString_AsString(repr));
      Py_DECREF(repr);
    }
    value = NULL;
  }

  return value;
}

XMLPARSER_METHOD_DOC(setProperty) = \
"setProperty(propertyname, value)\n\
\n\
Set the propertyname to value. If the property is not recognized,\n\
SAXNotRecognizedException is raised. If the property or its setting\n\
is not supported by the parser, SAXNotSupportedException is raised.";

XMLPARSER_METHOD_DEF(setProperty)
{
  PyObject *propertyname, *value, *temp;

  if (!PyArg_ParseTuple(args, "OO:setProperty", &propertyname, &value))
    return NULL;

  if (PyObject_RichCompareBool(propertyname, property_yield_result, Py_EQ)) {
    /* result value used when generator feature is enabled */
    if (self->generator) {
      temp = self->yield_result;
      Py_INCREF(value);
      self->yield_result = value;
      Py_XDECREF(temp);
      if (ExpatReader_Suspend(self->reader) == EXPAT_STATUS_ERROR) {
        return NULL;
      }
    } else {
      return SAXNotSupportedException(
                "yield-result only allowed for generator parser");
    }
  }
  else if (ExpatReader_GetParsingStatus(self->reader)) {
    return SAXNotSupportedException("cannot set properties while parsing");
  }
  else if (PyObject_RichCompareBool(propertyname, property_lexical_handler,
                                    Py_EQ)) {
    if (value == Py_None)
      value = NULL;
    else
      Py_INCREF(value);
    temp = self->lexical_handler;
    self->lexical_handler = value;
    Py_XDECREF(temp);

#define GET_CALLBACK(TYPE, NAME)                                        \
    temp = self->handlers[Handler_##TYPE];                              \
    self->handlers[Handler_##TYPE] = PyObject_GetAttrString(value, NAME); \
    Py_XDECREF(temp);

    GET_CALLBACK(StartDTD, "startDTD");
    GET_CALLBACK(EndDTD, "endDTD");
    GET_CALLBACK(StartCDATA, "startCDATA");
    GET_CALLBACK(EndCDATA, "endCDATA");
    GET_CALLBACK(Comment, "comment");
#undef GET_CALLBACK

    /* ignore any undefined event handler errors */
    PyErr_Clear();
  }
  else if (PyObject_RichCompareBool(propertyname, property_declaration_handler,
                                    Py_EQ)) {
    if (value == Py_None)
      value = NULL;
    else
      Py_INCREF(value);
    temp = self->decl_handler;
    self->decl_handler = value;
    Py_XDECREF(temp);

#define GET_CALLBACK(TYPE, NAME)                                        \
    temp = self->handlers[Handler_##TYPE];                              \
    self->handlers[Handler_##TYPE] = PyObject_GetAttrString(value, NAME); \
    Py_XDECREF(temp);

    GET_CALLBACK(ElementDecl, "elementDecl");
    GET_CALLBACK(AttributeDecl, "attributeDecl");
    GET_CALLBACK(InternalEntityDecl, "internalEntityDecl");
    GET_CALLBACK(ExternalEntityDecl, "externalEntityDecl");
#undef GET_CALLBACK

    /* ignore any undefined event handler errors */
    PyErr_Clear();
  }
  else if (PyObject_RichCompareBool(propertyname, property_dom_node,
                                    Py_EQ)) {
    /* create a "DOM Walker"-style parser */
    if (Entity_Check(value)) {
      Py_XDECREF(self->dom_node);
      Py_INCREF(value);
      self->dom_node = (NodeObject *) value;
    } else {
      return SAXNotSupportedException("dom-node must be a Document node");
    }
  }
  else if (PyObject_RichCompareBool(propertyname, property_whitespace_rules,
                                    Py_EQ)) {
    ExpatStatus status;
    /* XSLT-style whitespace stripping rules */
    if (value == Py_None)
      value = NULL;
    status = ExpatReader_SetWhitespaceStripping(self->reader, value);
    if (status == EXPAT_STATUS_ERROR)
      return NULL;
  }
  else {
    PyObject *repr = PyObject_Repr(propertyname);
    if (repr) {
      SAXNotRecognizedException(PyString_AsString(repr));
      Py_DECREF(repr);
    }
    return NULL;
  }

  Py_INCREF(Py_None);
  return Py_None;
}

/** Locator Interface **/

XMLPARSER_METHOD_DOC(getLineNumber) = \
"getLineNumber() -> int\n\
\n\
Return the line number where the current event ends.";

XMLPARSER_METHOD_DEF(getLineNumber)
{
  unsigned long n;

  if (!PyArg_ParseTuple(args, ":getLineNumber"))
    return NULL;

  if (self->dom_node)
    return PyInt_FromLong(-1);

  n = ExpatReader_GetLineNumber(self->reader);
  if (n > (unsigned long)LONG_MAX)
    return PyLong_FromUnsignedLong(n);
  else
    return PyInt_FromLong(n);
}

XMLPARSER_METHOD_DOC(getColumnNumber) = \
"getColumnNumber() -> int\n\
\n\
Return the column number where the current event ends.";

XMLPARSER_METHOD_DEF(getColumnNumber)
{
  unsigned long n;

  if (!PyArg_ParseTuple(args, ":getColumnNumber"))
    return NULL;

  if (self->dom_node)
    return PyInt_FromLong(-1);

  n = ExpatReader_GetColumnNumber(self->reader);
  if (n > (unsigned long)LONG_MAX)
    return PyLong_FromUnsignedLong(n);
  else
    return PyInt_FromLong(n);
}

XMLPARSER_METHOD_DOC(getSystemId) = \
"getSystemId() -> string\n\
\n\
Return the system identifier for the current event.";

XMLPARSER_METHOD_DEF(getSystemId)
{
  PyObject *systemId;

  if (!PyArg_ParseTuple(args, ":getSystemId"))
    return NULL;

  if (self->dom_node) {
    systemId = Entity_GET_DOCUMENT_URI(self->dom_node);
    Py_INCREF(systemId);
  } else {
    systemId = ExpatReader_GetBase(self->reader);
  }
  return systemId;
}

static PyMethodDef parser_methods[] = {
  Py_XMLPARSER_METHOD(getContentHandler),
  Py_XMLPARSER_METHOD(setContentHandler),
  Py_XMLPARSER_METHOD(getEntityResolver),
  Py_XMLPARSER_METHOD(setEntityResolver),
  Py_XMLPARSER_METHOD(getErrorHandler),
  Py_XMLPARSER_METHOD(setErrorHandler),
  Py_XMLPARSER_METHOD(getDTDHandler),
  Py_XMLPARSER_METHOD(setDTDHandler),
  Py_XMLPARSER_METHOD(parse),
  Py_XMLPARSER_METHOD(getFeature),
  Py_XMLPARSER_METHOD(setFeature),
  Py_XMLPARSER_METHOD(getProperty),
  Py_XMLPARSER_METHOD(setProperty),

  /* Locator Methods */
  Py_XMLPARSER_METHOD(getLineNumber),
  Py_XMLPARSER_METHOD(getColumnNumber),
  Py_XMLPARSER_METHOD(getSystemId),

  { NULL }
};

static struct memberlist parser_members[] = {
  { NULL }
};

static PyObject *
parser_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = { NULL };
  ExpatFilter *filters[2];
  XMLParserObject *self;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, ":SaxReader", kwlist))
    return NULL;

  self = (XMLParserObject *)type->tp_alloc(type, 0);
  if (self != NULL) {
    filters[0] = ExpatFilter_New(self, &sax_handlers,
                                 ExpatFilter_HANDLER_TYPE, NULL);
    if (filters[0] == NULL) {
      Py_DECREF(self);
      return NULL;
    }
    self->reader = ExpatReader_New(filters, 1);
    if (self->reader == NULL) {
      Py_DECREF(self);
      return NULL;
    }
  }
  return (PyObject *)self;
}

static void
parser_dealloc(XMLParserObject *self)
{
  int i;

  PyObject_GC_UnTrack(self);

  Py_XDECREF(self->dom_node);
  Py_XDECREF(self->yield_result);
  Py_XDECREF(self->lexical_handler);
  Py_XDECREF(self->decl_handler);
  Py_XDECREF(self->entity_resolver);
  Py_XDECREF(self->error_handler);
  Py_XDECREF(self->dtd_handler);
  Py_XDECREF(self->content_handler);

  for (i = 0; i < TotalHandlers; i++) {
    Py_XDECREF(self->handlers[i]);
  }

  if (self->reader) {
    ExpatReader_Del(self->reader);
    self->reader = NULL;
  }

  self->ob_type->tp_free((PyObject *)self);
}

static int parser_traverse(XMLParserObject *self, visitproc visit, void *arg)
{
  int i;

  Py_VISIT(self->content_handler);
  Py_VISIT(self->dtd_handler);
  Py_VISIT(self->error_handler);
  Py_VISIT(self->entity_resolver);
  Py_VISIT(self->decl_handler);
  Py_VISIT(self->lexical_handler);
  for (i = 0; i < TotalHandlers; i++) {
    Py_VISIT(self->handlers[i]);
  }
  return 0;
}

static int parser_clear(XMLParserObject *self)
{
  int i;

  Py_CLEAR(self->content_handler);
  Py_CLEAR(self->dtd_handler);
  Py_CLEAR(self->error_handler);
  Py_CLEAR(self->entity_resolver);
  Py_CLEAR(self->decl_handler);
  Py_CLEAR(self->lexical_handler);
  for (i = 0; i < TotalHandlers; i++) {
    Py_CLEAR(self->handlers[i]);
  }
  return 0;
}

static char parser_doc[] =
"Interface for reading an XML document using callbacks.\n\
\n\
Parser is the interface that an XML parser's SAX2 driver must\n\
implement. This interface allows an application to set and query\n\
features and properties in the parser, to register event handlers\n\
for document processing, and to initiate a document parse.\n\
\n\
All SAX interfaces are assumed to be synchronous: the parse\n\
methods must not return until parsing is complete, and readers\n\
must wait for an event-handler callback to return before reporting\n\
the next event.";

static PyTypeObject XMLParser_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ Expat_MODULE_NAME "." "SaxReader",
  /* tp_basicsize      */ sizeof(XMLParserObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) parser_dealloc,
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
  /* tp_flags          */ Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
  /* tp_doc            */ (char *) parser_doc,
  /* tp_traverse       */ (traverseproc) parser_traverse,
  /* tp_clear          */ (inquiry) parser_clear,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) parser_methods,
  /* tp_members        */ (PyMemberDef *) parser_members,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) parser_new,
  /* tp_free           */ 0,
};

/**********************************************************************/
/** External interfaces ***********************************************/
/**********************************************************************/

int _Expat_SaxFilter_Init(PyObject *module)
{
  PyObject *import;

  import = PyImport_ImportModule("amara.lib.iri");
  if (import == NULL) return -1;
  uri_resolver = PyObject_GetAttrString(import, "DEFAULT_RESOLVER");
  if (uri_resolver == NULL) {
    Py_DECREF(import);
    return -1;
  }
  Py_DECREF(import);

  import = PyImport_ImportModule("amara");
  if (import == NULL) return -1;
  xmlns_namespace_string = PyObject_GetAttrString(import, "XMLNS_NAMESPACE");
  xmlns_namespace_string = XmlString_FromObjectInPlace(xmlns_namespace_string);
  if (xmlns_namespace_string == NULL) {
    Py_DECREF(import);
    return -1;
  }
  Py_DECREF(import);

  if (PyType_Ready(&SaxGenerator_Type) < 0)
    return -1;

  if (PyModule_AddType(module, &XMLParser_Type) < 0)
    return -1;

  /* define 4Suite's extended feature & property constants */
#define ADD_STRING_CONST(cname, pname, string)          \
  if ((cname = PyString_FromString(string)) == NULL)    \
    return -1;                                          \
  if (PyModule_AddObject(module, pname, cname) == -1) { \
    Py_DECREF(cname);                                   \
    return -1;                                          \
  }                                                     \
  Py_INCREF(cname);

  ADD_STRING_CONST(feature_process_xincludes, "FEATURE_PROCESS_XINCLUDES",
                   "http://4suite.org/sax/features/process-xincludes");
  ADD_STRING_CONST(feature_generator, "FEATURE_GENERATOR",
                   "http://4suite.org/sax/features/generator");
  ADD_STRING_CONST(property_whitespace_rules, "PROPERTY_WHITESPACE_RULES",
                   "http://4suite.org/sax/properties/whitespace-rules");
  ADD_STRING_CONST(property_yield_result, "PROPERTY_YIELD_RESULT",
                   "http://4suite.org/sax/properties/yield-result");

#define GET_MODULE_EXC(name)                            \
  name##Object = PyObject_GetAttrString(import, #name); \
  if (name##Object == NULL) {                           \
    Py_DECREF(import);                                  \
    return -1;                                          \
  }

  /* load the SAX exceptions */
  import = PyImport_ImportModule("xml.sax");
  if (import == NULL) return -1;
  GET_MODULE_EXC(SAXNotRecognizedException);
  GET_MODULE_EXC(SAXNotSupportedException);
  GET_MODULE_EXC(SAXParseException);
  Py_DECREF(import);

#define GET_MODULE_CONST(name)                  \
  name = PyObject_GetAttrString(import, #name); \
  if (name == NULL) {                           \
    Py_DECREF(import);                          \
    return -1;                                  \
  }

  /* load the SAX standard feature & property constants */
  import = PyImport_ImportModule("xml.sax.handler");
  if (import == NULL) return -1;
  GET_MODULE_CONST(feature_external_ges);
  GET_MODULE_CONST(feature_external_pes);
  GET_MODULE_CONST(feature_namespaces);
  GET_MODULE_CONST(feature_namespace_prefixes);
  GET_MODULE_CONST(feature_string_interning);
  GET_MODULE_CONST(feature_validation);
  GET_MODULE_CONST(property_declaration_handler);
  GET_MODULE_CONST(property_dom_node);
  GET_MODULE_CONST(property_lexical_handler);
  /*GET_MODULE_CONST(property_xml_string);*/
  Py_DECREF(import);

  /* load the SAX InputSource class */
  import = PyImport_ImportModule("xml.sax.xmlreader");
  if (import == NULL) return -1;
  sax_input_source = PyObject_GetAttrString(import, "InputSource");
  if (sax_input_source == NULL) {
    Py_DECREF(import);
    return -1;
  }
  Py_DECREF(import);

  return 0;
}

void _Expat_SaxFilter_Fini(void)
{
  int i;

  for (i = 0; i < TotalHandlers; i++) {
    PyCodeObject *code = tb_codes[i];
    if (code != NULL) {
      tb_codes[i] = NULL;
      Py_DECREF(code);
    }
  }

  Py_DECREF(uri_resolver);
  Py_DECREF(xmlns_namespace_string);
  Py_DECREF(feature_process_xincludes);
  Py_DECREF(feature_generator);
  Py_DECREF(property_whitespace_rules);
  Py_DECREF(property_yield_result);
  Py_DECREF(SAXNotRecognizedExceptionObject);
  Py_DECREF(SAXNotSupportedExceptionObject);
  Py_DECREF(SAXParseExceptionObject);
  Py_DECREF(feature_external_ges);
  Py_DECREF(feature_external_pes);
  Py_DECREF(feature_namespaces);
  Py_DECREF(feature_namespace_prefixes);
  Py_DECREF(feature_string_interning);
  Py_DECREF(feature_validation);
  Py_DECREF(property_declaration_handler);
  Py_DECREF(property_dom_node);
  Py_DECREF(property_lexical_handler);
  /*Py_DECREF(property_xml_string);*/
  Py_DECREF(sax_input_source);

  PyType_CLEAR(&SaxGenerator_Type);
  PyType_CLEAR(&XMLParser_Type);
}
