/* ----------------------------------------------------------------------
 * rulematch.c
 *
 * C interface to support rule matching in pushtree/itertree functions.
 * In order to do rule matching, the matching engine needs to receive
 * various events related to document structure.  The easiest way to do this
 * is to build the rule matching engine on top of a SAX content handler
 * object.
 *
 * This file merely provides C functions to trigger SAX callbacks in the
 * matching engine.
 * ---------------------------------------------------------------------- */

#include "expat_interface.h"

/* Enumeration of the SAX handler functions */

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

typedef struct RuleMatchObject {
  PyObject *content_handler;        /* SAX ContentHandler object */
  /* Python callbacks */
  PyObject *handlers[TotalHandlers];
} RuleMatchObject;

RuleMatchObject *
RuleMatchObject_New(PyObject *contenthandler) {
  RuleMatchObject *self;
  int i;
  self = PyMem_New(RuleMatchObject, 1);
  if (self == NULL) {
    return NULL;
  }
  for (i = 0; i < TotalHandlers; i++) {
    self->handlers[i] = NULL;
  }

  self->content_handler = contenthandler;
  Py_INCREF(contenthandler);

  /* Copy selected handlers of interest */

#define GET_CALLBACK(TYPE, NAME)                                        \
  self->handlers[Handler_##TYPE] = PyObject_GetAttrString(contenthandler, NAME); 

  GET_CALLBACK(StartDocument, "startDocument");
  GET_CALLBACK(StartElement, "startElementNS");
  GET_CALLBACK(EndElement, "endElementNS");
  GET_CALLBACK(ProcessingInstruction, "processingInstruction");
#undef GET_CALLBACK
  return self;
}

void RuleMatchObject_Del(RuleMatchObject *self) {
  int i;
  for (i = 0; i < TotalHandlers; i++) {
    if (self->handlers[i]) {
      Py_DECREF(self->handlers[i]);
    }
  }
  PyMem_Free(self);
}

int RuleMatch_StartElement(RuleMatchObject *self,
			      PyObject *node,
			      ExpatName *name,
			      ExpatAttribute atts[],
			      size_t natts) {
  PyObject *handler = self->handlers[Handler_StartElement];
  PyObject *args, *result;

  if (handler != NULL) {
    /* handler.startElement((namespaceURI, localName), tagName, attributes) */
    args = Py_BuildValue("O(OO)ON", node,name->namespaceURI, name->localName,
                         name->qualifiedName, Attributes_New(atts, natts));
    if (args == NULL)
      return -1;
    result = PyEval_CallObject(handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return -1;
    Py_DECREF(result);
  }
  return 0;
}

int RuleMatch_EndElement(RuleMatchObject *self, PyObject *node, ExpatName *name)
{
  PyObject *handler = self->handlers[Handler_EndElement];
  PyObject *args, *result;

  if (handler != NULL) {
    /* handler.endElement((namespaceURI, localName), tagName) */
    args = Py_BuildValue("O(OO)O", node,name->namespaceURI, name->localName,
                         name->qualifiedName);
    if (args == NULL)
      return -1;
    result = PyEval_CallObject(handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return -1;
    Py_DECREF(result);
  }
  return 0;
}


/* Receive notification of the beginning of a document. */
int RuleMatch_StartDocument(RuleMatchObject *self, PyObject *node)
{
  PyObject *handler, *args, *result;

  if ((handler = self->handlers[Handler_StartDocument]) != NULL) {
    /* handler.startDocument() */
    if ((args = PyTuple_Pack(1, node)) == NULL)
      return -1;
    result = PyEval_CallObject(handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return -1;
    Py_DECREF(result);
  }
  return 0;
}

/* Receive notification of a processing instruction. */
int RuleMatch_ProcessingInstruction(RuleMatchObject *self,
				       PyObject *node,
				       PyObject *target,
				       PyObject *data)
{
  PyObject *handler = self->handlers[Handler_ProcessingInstruction];
  PyObject *args, *result;

  if (handler != NULL) {
    /* handler.processingInstruction(node,target,data) */
    if ((args = PyTuple_Pack(3, node, target, data)) == NULL)
      return -1;
    result = PyEval_CallObject(handler, args);
    Py_DECREF(args);
    if (result == NULL)
      return -1;
    Py_DECREF(result);
  }
  return 0;
}

int RuleMatch_Init(void) {
  if (Expat_IMPORT == NULL) return -1;
  return 0;
}

