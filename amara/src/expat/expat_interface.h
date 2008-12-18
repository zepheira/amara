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

#define Expat_MODULE_NAME "amara._expat"

#include "Python.h"
#include "structmember.h"
#include "validation.h"
#include "input_source.h"

  struct ExpatFilterStruct;
  typedef struct ExpatFilterStruct ExpatFilter;

#include "filter.h"

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

  /* name is a PyUnicodeObject, atts is a PyDictObject */
  typedef ExpatStatus (*ExpatStartFilterHandler)(
                                    void *arg,
                                    ExpatName *name);

  /* name is a PyUnicodeObject */
  typedef ExpatStatus (*ExpatEndFilterHandler)(
                                    void *arg,
                                    ExpatName *name);

  typedef ExpatStatus (*ExpatStartDocumentHandler)(void *arg);

  typedef ExpatStatus (*ExpatEndDocumentHandler)(void *arg);

  /* name is a PyUnicodeObject, atts is a PyDictObject */
  typedef ExpatStatus (*ExpatStartElementHandler)(
                                    void *arg,
                                    ExpatName *name,
                                    ExpatAttribute atts[],
                                    size_t natts);

  /* name is a PyUnicodeObject */
  typedef ExpatStatus (*ExpatEndElementHandler)(
                                    void *arg,
                                    ExpatName *name);

  typedef ExpatStatus (*ExpatAttributeHandler)(
                                    void *arg,
                                    ExpatName *name,
                                    PyObject *value,
                                    AttributeType type);

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
    ExpatStartFilterHandler start_filter;
    ExpatEndFilterHandler end_filter;
    ExpatStartDocumentHandler start_document;
    ExpatEndDocumentHandler end_document;
    ExpatStartElementHandler start_element;
    ExpatEndElementHandler end_element;
    ExpatAttributeHandler attribute;
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

#define ExpatFilter_HANDLER_TYPE (1L<<0)

#define ExpatFilter_HasFlag(filter, flag) \
  ((((ExpatFilter *)(filter))->flags & (flag)) == (flag))

  typedef struct {
    ExpatFilter *(*Filter_New)(void *arg, ExpatHandlers *handlers,
                               unsigned long flags, FilterCriterion *criteria);
    void (*Filter_Del)(ExpatFilter *filter);

    ExpatReader *(*Reader_New)(ExpatFilter *filters[], size_t nfilters);
    void (*Reader_Del)(ExpatReader *reader);

    void (*Reader_SetValidation)(ExpatReader *reader, int doValidation);
    void (*Reader_SetParamEntityParsing)(ExpatReader *reader, int doParsing);

    ExpatStatus (*Reader_Parse)(ExpatReader *reader, PyObject *source);
    ExpatStatus (*Reader_ParseEntity)(ExpatReader *reader, PyObject *source,
                                      PyObject *namespaces);
    ExpatStatus (*Reader_Suspend)(ExpatReader *reader);
    ExpatStatus (*Reader_Resume)(ExpatReader *reader);

    PyObject *(*Reader_GetBase)(ExpatReader *reader);
    unsigned long (*Reader_GetLineNumber)(ExpatReader *reader);
    unsigned long (*Reader_GetColumnNumber)(ExpatReader *reader);

  } Expat_APIObject;

#ifdef Expat_BUILDING_MODULE

#ifndef XmlString_EXPORT
#define XmlString_EXPORT extern
#include "xmlstring.h"
#endif
#include "util.h"
#include "debug.h"

  ExpatFilter *ExpatFilter_New(void *arg, ExpatHandlers *handlers,
                               unsigned long flags, FilterCriterion *criteria);
  void ExpatFilter_Del(ExpatFilter *filter);

  ExpatReader *ExpatReader_New(ExpatFilter *filters[], size_t nfilters);
  void ExpatReader_Del(ExpatReader *reader);

  int ExpatReader_GetValidation(ExpatReader *reader);
  void ExpatReader_SetValidation(ExpatReader *reader, int validate);

  int ExpatReader_GetParamEntityParsing(ExpatReader *reader);
  void ExpatReader_SetParamEntityParsing(ExpatReader *reader, int parsing);

  PyObject *ExpatReader_GetWhitespaceStripping(ExpatReader *reader);
  ExpatStatus ExpatReader_SetWhitespaceStripping(ExpatReader *reader,
                                                 PyObject *sequence);

  PyObject *ExpatReader_GetBase(ExpatReader *reader);
  unsigned long ExpatReader_GetLineNumber(ExpatReader *reader);
  unsigned long ExpatReader_GetColumnNumber(ExpatReader *reader);

  ExpatStatus ExpatReader_Parse(ExpatReader *reader, PyObject *source);
  ExpatStatus ExpatReader_ParseEntity(ExpatReader *reader, PyObject *source,
                                      PyObject *namespaces);
  ExpatStatus ExpatReader_Suspend(ExpatReader *reader);
  ExpatStatus ExpatReader_Resume(ExpatReader *reader);
  int ExpatReader_GetParsingStatus(ExpatReader *reader);


#else /* !Expat_BUILDING_MODULE */

/* --- C API ----------------------------------------------------*/

  static Expat_APIObject *Expat_API;

#define Expat_IMPORT (Expat_API = (Expat_APIObject *)       \
  PyCObject_Import(Expat_MODULE_NAME, "CAPI"))

#define Expat_EXPORT(name) Expat_API->name

#define ExpatFilter_New         Expat_EXPORT(Filter_New)
#define ExpatFilter_Del         Expat_EXPORT(Filter_Del)
#define ExpatReader_New         Expat_EXPORT(Reader_New)
#define ExpatReader_Del         Expat_EXPORT(Reader_Del)

#define Expat_SetValidation         Expat_EXPORT(Reader_SetValidation)
#define Expat_SetParamEntityParsing Expat_EXPORT(Reader_SetParamEntityParsing)

#define ExpatReader_Parse       Expat_EXPORT(Reader_Parse)
#define ExpatReader_ParseEntity Expat_EXPORT(Reader_ParseEntity)
#define ExpatReader_Suspend     Expat_EXPORT(Reader_Suspend)
#define ExpatReader_Resume      Expat_EXPORT(Reader_Resume)

#define ExpatReader_GetBase         Expat_EXPORT(Reader_GetBase)
#define ExpatReader_GetLineNumber   Expat_EXPORT(Reader_GetLineNumber)
#define ExpatReader_GetColumnNumber Expat_EXPORT(Reader_GetColumnNumber)

#endif /* Expat_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* EXPAT_INTERFACE_H */
