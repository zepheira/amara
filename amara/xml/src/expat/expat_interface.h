#ifndef EXPAT_INTERFACE_H
#define EXPAT_INTERFACE_H

#ifdef __cplusplus
extern "C" {
#endif

/*

  This header provides access to the ExpatReader interface from C.

  Before calling any of the functions or macros, you must initialize
  the routines with:

    Expat_IMPORT

  This would typically be done in your init function.

*/

#define EXPAT_MODULE_NAME "Ft.Xml.Lib.ExpatReader"

#include "Python.h"
#include "structmember.h"
#include "validation.h"
#include "input_source.h"

  struct ExpatFilterStruct;
  typedef struct ExpatFilterStruct ExpatFilter;

  struct ExpatReaderStruct;
  typedef struct ExpatReaderStruct ExpatReader;

  typedef struct {
    PyObject *namespaceURI;
    PyObject *localName;
    PyObject *qualifiedName;
  } ExpatName;

  typedef struct {
    PyObject *namespaceURI;
    PyObject *localName;
    PyObject *qualifiedName;
    PyObject *value;
    AttributeType type;
  } ExpatAttribute;

  typedef enum {
    EXPAT_STATUS_ERROR = 0,
    EXPAT_STATUS_OK,
    EXPAT_STATUS_SUSPENDED,
  } ExpatStatus;

  typedef ExpatStatus (*ExpatStartDocumentHandler)(void *arg);

  typedef ExpatStatus (*ExpatEndDocumentHandler)(void *arg);

  /* name is a PyUnicodeObject, atts is a PyDictObject */
  typedef ExpatStatus (*ExpatStartElementHandler)(
                                    void *arg,
                                    ExpatName *name,
                                    ExpatAttribute atts[],
                                    int natts);

  /* name is a PyUnicodeObject */
  typedef ExpatStatus (*ExpatEndElementHandler)(
                                    void *arg,
                                    ExpatName *name);

  /* data is a PyUnicodeObject */
  typedef ExpatStatus (*ExpatCharacterDataHandler)(
                                    void *arg,
                                    PyObject *data);

  /* target is a PyUnicodeObject, data is a PyUnicodeObject */
  typedef ExpatStatus (*ExpatProcessingInstructionHandler)(
                                    void *arg,
                                    PyObject *target,
                                    PyObject *data);

  /* data is a PyUnicodeObject */
  typedef ExpatStatus (*ExpatCommentHandler)(
                                    void *arg,
                                    PyObject *data);

  /* prefix is a PyUnicodeObject or Py_None, uri is a PyUnicodeObject */
  typedef ExpatStatus (*ExpatStartNamespaceDeclHandler)(
                                    void *arg,
                                    PyObject *prefix,
                                    PyObject *uri);

  /* prefix is a PyUnicodeObject or Py_None */
  typedef ExpatStatus (*ExpatEndNamespaceDeclHandler)(
                                    void *arg,
                                    PyObject *prefix);

  /* name is a PyUnicodeObject
     systemId is a PyUnicodeObject or Py_None,
     publicId is a PyUnicodeObject or Py_None
  */
  typedef ExpatStatus (*ExpatStartDoctypeDeclHandler)(
                                    void *arg,
                                    PyObject *name,
                                    PyObject *systemId,
                                    PyObject *publicId);

  typedef ExpatStatus (*ExpatEndDoctypeDeclHandler)(void *arg);

  /* name is a PyUnicodeObject
     model is a PyUnicodeObject
  */
  typedef ExpatStatus (*ExpatElementDeclHandler)(
                                    void *arg,
                                    PyObject *name,
                                    PyObject *model);

  /* elementName is a PyUnicodeObject
     attributeName is a PyUnicodeObject
     type is a PyUnicodeObject
     mode is a PyUnicodeObject oy Py_None
     value is a PyUnicodeObject or Py_None
  */
  typedef ExpatStatus (*ExpatAttributeDeclHandler)(
                                    void *arg,
                                    PyObject *elementName,
                                    PyObject *attributeName,
                                    PyObject *type,
                                    PyObject *mode,
                                    PyObject *value);

  /* name is a PyUnicodeObject
     value is a PyUnicodeObject
  */
  typedef ExpatStatus (*ExpatInternalEntityDeclHandler)(
                                    void *arg,
                                    PyObject *name,
                                    PyObject *value);

  /* name is a PyUnicodeObject
     publicId is a PyUnicodeObject or Py_None
     systemId is a PyUnicodeObject
  */
  typedef ExpatStatus (*ExpatExternalEntityDeclHandler)(
                                    void *arg,
                                    PyObject *name,
                                    PyObject *publicId,
                                    PyObject *systemId);

  /* name is a PyUnicodeObject
     publicId is a PyUnicodeObject or Py_None
     systemId is a PyUnicodeObject
     notationName is a PyUnicodeObject
  */
  typedef ExpatStatus (*ExpatUnparsedEntityDeclHandler)(
                                    void *arg,
                                    PyObject *name,
                                    PyObject *publicId,
                                    PyObject *systemId,
                                    PyObject *notationName);

  /* name is a PyUnicodeObject
     publicId is a PyUnicodeObject or Py_None
     systemId is a PyUnicodeObject or Py_None
  */
  typedef ExpatStatus (*ExpatNotationDeclHandler)(
                                    void *arg,
                                    PyObject *name,
                                    PyObject *publicId,
                                    PyObject *systemId);

  /* name is a PyUnicodeObject */
  typedef ExpatStatus (*ExpatSkippedEntityHandler)(
                                    void *arg,
                                    PyObject *name);

  typedef ExpatStatus (*ExpatStartCdataSectionHandler)(void *arg);

  typedef ExpatStatus (*ExpatEndCdataSectionHandler)(void *arg);

  /* data is a PyUnicodeObject */
  typedef ExpatStatus (*ExpatIgnorableWhitespaceHandler)(
                                    void *arg,
                                    PyObject *data);

  /* exception is an ReaderException instance */
  typedef ExpatStatus (*ExpatNotificationHandler)(
                                    void *arg,
                                    PyObject *exception);

  typedef PyObject *(*ExpatResolveEntityHandler)(void *arg,
                                                 PyObject *publicId,
                                                 PyObject *systemId);

  typedef struct {
    void *arg;
    ExpatStartDocumentHandler start_document;
    ExpatEndDocumentHandler end_document;
    ExpatStartElementHandler start_element;
    ExpatEndElementHandler end_element;
    ExpatCharacterDataHandler characters;
    ExpatCharacterDataHandler ignorable_whitespace;
    ExpatProcessingInstructionHandler processing_instruction;
    ExpatCommentHandler comment;
    ExpatStartNamespaceDeclHandler start_namespace_decl;
    ExpatEndNamespaceDeclHandler end_namespace_decl;
    ExpatStartDoctypeDeclHandler start_doctype_decl;
    ExpatEndDoctypeDeclHandler end_doctype_decl;
    ExpatElementDeclHandler element_decl;
    ExpatAttributeDeclHandler attribute_decl;
    ExpatInternalEntityDeclHandler internal_entity_decl;
    ExpatExternalEntityDeclHandler external_entity_decl;
    ExpatUnparsedEntityDeclHandler unparsed_entity_decl;
    ExpatNotationDeclHandler notation_decl;
    ExpatSkippedEntityHandler skipped_entity;
    ExpatStartCdataSectionHandler start_cdata_section;
    ExpatEndCdataSectionHandler end_cdata_section;

    ExpatNotificationHandler warning;
    ExpatNotificationHandler error;
    ExpatNotificationHandler fatal_error;

    ExpatResolveEntityHandler resolve_entity;
  } ExpatHandlers;

  typedef struct {
    ExpatReader *(*Reader_New)(PyObject *filters);
    void (*Reader_Del)(ExpatReader *reader);

    ExpatStatus (*Reader_Parse)(ExpatReader *reader, PyObject *source);
    ExpatStatus (*Reader_ParseEntity)(ExpatReader *reader, PyObject *source,
                                      PyObject *namespaces);
    ExpatStatus (*Reader_Suspend)(ExpatReader *reader);
    ExpatStatus (*Reader_Resume)(ExpatReader *reader);

    PyObject *(*GetBase)(ExpatReader *reader);
    unsigned long (*GetLineNumber)(ExpatReader *reader);
    unsigned long (*GetColumnNumber)(ExpatReader *reader);

    void (*SetStartDocumentHandler)(ExpatReader *reader,
                                    ExpatStartDocumentHandler handler);

    void (*SetEndDocumentHandler)(ExpatReader *reader,
                                  ExpatEndDocumentHandler handler);

    void (*SetStartElementHandler)(ExpatReader *reader,
                                   ExpatStartElementHandler handler);

    void (*SetEndElementHandler)(ExpatReader *reader,
                                 ExpatEndElementHandler handler);

    void (*SetCharacterDataHandler)(ExpatReader *reader,
                                    ExpatCharacterDataHandler handler);

    void (*SetProcessingInstructionHandler)(
                                    ExpatReader *reader,
                                    ExpatProcessingInstructionHandler handler);

    void (*SetCommentHandler)(ExpatReader *reader,
                              ExpatCommentHandler handler);

    void (*SetStartNamespaceDeclHandler)(
                                    ExpatReader *reader,
                                    ExpatStartNamespaceDeclHandler handler);

    void (*SetEndNamespaceDeclHandler)(
                                    ExpatReader *reader,
                                    ExpatEndNamespaceDeclHandler handler);

    void (*SetStartDoctypeDeclHandler)(
                                    ExpatReader *reader,
                                    ExpatStartDoctypeDeclHandler handler);

    void (*SetEndDoctypeDeclHandler)(
                                    ExpatReader *reader,
                                    ExpatEndDoctypeDeclHandler handler);

    void (*SetSkippedEntityHandler)(ExpatReader *reader,
                                    ExpatSkippedEntityHandler handler);

    void (*SetStartCdataSectionHandler)(
                                    ExpatReader *reader,
                                    ExpatStartCdataSectionHandler handler);

    void (*SetEndCdataSectionHandler)(
                                    ExpatReader *reader,
                                    ExpatEndCdataSectionHandler handler);

    void (*SetIgnorableWhitespaceHandler)(
                                    ExpatReader *reader,
                                    ExpatIgnorableWhitespaceHandler handler);

    void (*SetWarningHandler)(ExpatReader *reader,
                              ExpatNotificationHandler handler);

    void (*SetErrorHandler)(ExpatReader *reader,
                            ExpatNotificationHandler handler);

    void (*SetFatalErrorHandler)(ExpatReader *reader,
                                 ExpatNotificationHandler handler);

    void (*SetNotationDeclHandler)(ExpatReader *reader,
                                   ExpatNotationDeclHandler handler);

    void (*SetUnparsedEntityDeclHandler)(
                                    ExpatReader *reader,
                                    ExpatUnparsedEntityDeclHandler handler);

    void (*SetElementDeclHandler)(ExpatReader *reader,
                                  ExpatElementDeclHandler handler);

    void (*SetAttributeDeclHandler)(ExpatReader *reader,
                                    ExpatAttributeDeclHandler handler);

    void (*SetInternalEntityDeclHandler)(
                                    ExpatReader *reader,
                                    ExpatInternalEntityDeclHandler handler);

    void (*SetExternalEntityDeclHandler)(
                                    ExpatReader *reader,
                                    ExpatExternalEntityDeclHandler handler);

    void (*SetResolveEntityHandler)(ExpatReader *reader,
                                    ExpatResolveEntityHandler handler);

    void (*SetValidation)(ExpatReader *reader, int doValidation);

    void (*SetParamEntityParsing)(ExpatReader *reader, int doParsing);

  } Expat_APIObject;

#ifdef Expat_BUILDING_MODULE

#define XmlString_SHARED
#include "xmlstring.h"
#include "util.h"
#include "debug.h"

  ExpatReader *ExpatReader_New(PyObject *filters);
  void ExpatReader_Del(ExpatReader *reader);

  int ExpatReader_GetValidation(ExpatReader *reader);
  void ExpatReader_SetValidation(ExpatReader *reader, int validate);

  int ExpatReader_GetParamEntityParsing(ExpatReader *reader);
  void ExpatReader_SetParamEntityParsing(ExpatReader *reader, int parsing);

  PyObject *ExpatReader_GetBase(ExpatReader *reader);
  unsigned long ExpatReader_GetLineNumber(ExpatReader *reader);
  unsigned long ExpatReader_GetColumnNumber(ExpatReader *reader);

  ExpatStatus ExpatReader_Parse(ExpatReader *reader, PyObject *source);
  ExpatStatus ExpatReader_ParseEntity(ExpatReader *reader, PyObject *source,
                                      PyObject *namespaces);
  ExpatStatus ExpatReader_Suspend(ExpatReader *reader);
  ExpatStatus ExpatReader_Resume(ExpatReader *reader);
  int ExpatReader_GetParsingStatus(ExpatReader *reader);

  void ExpatReader_SetStartDocumentHandler(
                                ExpatReader *reader,
                                ExpatStartDocumentHandler handler);

  void ExpatReader_SetEndDocumentHandler(
                                ExpatReader *reader,
                                ExpatEndDocumentHandler handler);

  void ExpatReader_SetStartElementHandler(
                                ExpatReader *reader,
                                ExpatStartElementHandler handler);

  void ExpatReader_SetEndElementHandler(
                                ExpatReader *reader,
                                ExpatEndElementHandler handler);

  void ExpatReader_SetCharacterDataHandler(
                                ExpatReader *reader,
                                ExpatCharacterDataHandler handler);

  void ExpatReader_SetProcessingInstructionHandler(
                                ExpatReader *reader,
                                ExpatProcessingInstructionHandler handler);

  void ExpatReader_SetCommentHandler(
                                ExpatReader *reader,
                                ExpatCommentHandler handler);

  void ExpatReader_SetStartNamespaceDeclHandler(
                                ExpatReader *reader,
                                ExpatStartNamespaceDeclHandler handler);

  void ExpatReader_SetEndNamespaceDeclHandler(
                                ExpatReader *reader,
                                ExpatEndNamespaceDeclHandler handler);

  void ExpatReader_SetStartDoctypeDeclHandler(
                                ExpatReader *reader,
                                ExpatStartDoctypeDeclHandler handler);

  void ExpatReader_SetEndDoctypeDeclHandler(
                                ExpatReader *reader,
                                ExpatEndDoctypeDeclHandler handler);

  void ExpatReader_SetUnparsedEntityDeclHandler(
                                ExpatReader *reader,
                                ExpatUnparsedEntityDeclHandler handler);

  void ExpatReader_SetSkippedEntityHandler(
                                ExpatReader *reader,
                                ExpatSkippedEntityHandler handler);

  void ExpatReader_SetStartCdataSectionHandler(
                                ExpatReader *reader,
                                ExpatStartCdataSectionHandler handler);

  void ExpatReader_SetEndCdataSectionHandler(
                                ExpatReader *reader,
                                ExpatEndCdataSectionHandler handler);

  void ExpatReader_SetIgnorableWhitespaceHandler(
                                ExpatReader *reader,
                                ExpatIgnorableWhitespaceHandler handler);

  void ExpatReader_SetNotationDeclHandler(
                                ExpatReader *reader,
                                ExpatNotationDeclHandler handler);

  void ExpatReader_SetElementDeclHandler(
                                ExpatReader *reader,
                                ExpatElementDeclHandler handler);

  void ExpatReader_SetAttributeDeclHandler(
                                ExpatReader *reader,
                                ExpatAttributeDeclHandler handler);

  void ExpatReader_SetInternalEntityDeclHandler(
                                ExpatReader *reader,
                                ExpatInternalEntityDeclHandler handler);

  void ExpatReader_SetExternalEntityDeclHandler(
                                ExpatReader *reader,
                                ExpatExternalEntityDeclHandler handler);

  void ExpatReader_SetResolveEntityHandler(
                                ExpatReader *reader,
                                ExpatResolveEntityHandler handler);

  void ExpatReader_SetWarningHandler(
                                ExpatReader *reader,
                                ExpatNotificationHandler handler);

  void ExpatReader_SetErrorHandler(
                                ExpatReader *reader,
                                ExpatNotificationHandler handler);

  void ExpatReader_SetFatalErrorHandler(
                                ExpatReader *reader,
                                ExpatNotificationHandler handler);

#else /* !Expat_BUILDING_MODULE */

/* --- C API ----------------------------------------------------*/

  static Expat_APIObject *Expat_API;

#define Expat_IMPORT (Expat_API = (Expat_APIObject *)       \
  PyCObject_Import(EXPAT_MODULE_NAME, "CAPI"))

#define Expat_EXPORT(name) Expat_API->name

#define ExpatReader_New         Expat_EXPORT(Reader_New)
#define ExpatReader_Del         Expat_EXPORT(Reader_Del)
#define ExpatReader_Parse       Expat_EXPORT(Reader_Parse)
#define ExpatReader_ParseEntity Expat_EXPORT(Reader_ParseEntity)
#define ExpatReader_Suspend     Expat_EXPORT(Reader_Suspend)
#define ExpatReader_Resume      Expat_EXPORT(Reader_Resume)

#define Expat_GetBase \
  Expat_API->GetBase
#define Expat_GetLineNumber \
  Expat_API->GetLineNumber
#define Expat_GetColumnNumber \
  Expat_API->GetColumnNumber
#define Expat_SetStartDocumentHandler \
  Expat_API->SetStartDocumentHandler
#define Expat_SetEndDocumentHandler \
  Expat_API->SetEndDocumentHandler
#define Expat_SetStartElementHandler \
  Expat_API->SetStartElementHandler
#define Expat_SetEndElementHandler \
  Expat_API->SetEndElementHandler
#define Expat_SetCharacterDataHandler \
  Expat_API->SetCharacterDataHandler
#define Expat_SetProcessingInstructionHandler \
  Expat_API->SetProcessingInstructionHandler
#define Expat_SetCommentHandler \
  Expat_API->SetCommentHandler
#define Expat_SetStartNamespaceDeclHandler \
  Expat_API->SetStartNamespaceDeclHandler
#define Expat_SetEndNamespaceDeclHandler \
  Expat_API->SetEndNamespaceDeclHandler
#define Expat_SetStartDoctypeDeclHandler \
  Expat_API->SetStartDoctypeDeclHandler
#define Expat_SetEndDoctypeDeclHandler \
  Expat_API->SeEndDoctypeDeclHandler
#define Expat_SetStartCdataSectionHandler \
  Expat_API->SetStartCdataSectionHandler
#define Expat_SetEndCdataSectionHandler \
  Expat_API->SetEndCdataSectionHandler
#define Expat_SetIgnorableWhitespaceHandler \
  Expat_API->SetIgnorableWhitespaceHandler

#define Expat_SetWarningHandler \
  Expat_API->SetWarningHandler
#define Expat_SetErrorHandler \
  Expat_API->SetErrorHandler
#define Expat_SetFatalErrorHandler \
  Expat_API->SetFatalErrorHandler

#define Expat_SetNotationDeclHandler \
  Expat_API->SetNotationDeclHandler
#define Expat_SetUnparsedEntityDeclHandler \
  Expat_API->SetUnparsedEntityDeclHandler

#define Expat_SetElementDeclHandler \
  Expat_API->SetElementDeclHandler
#define Expat_SetAttributeDeclHandler \
  Expat_API->SetAttributeDeclHandler
#define Expat_SetInternalEntityDeclHandler \
  Expat_API->SetInternalEntityDeclHandler
#define Expat_SetExternalEntityDeclHandler \
  Expat_API->SetExternalEntityDeclHandler

#define Expat_SetResolveEntityHandler \
  Expat_API->SetResolveEntityHandler

#define Expat_SetValidation \
  Expat_API->SetValidation
#define Expat_SetParamEntityParsing \
  Expat_API->SetParamEntityParsing

#endif /* Expat_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* EXPAT_INTERFACE_H */
