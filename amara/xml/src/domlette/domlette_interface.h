#ifndef DOMLETTE_INTERFACE_H
#define DOMLETTE_INTERFACE_H

#ifdef __cplusplus
extern "C" {
#endif

#define Domlette_MODULE_NAME  "amara.xml._domlette"

#include "Python.h"
#include "structmember.h"

#include "node.h"
#include "document.h"
#include "element.h"
#include "text.h"
#include "comment.h"
#include "processinginstruction.h"

/*

  This header provides access to Domlette's interface from C.

  Before calling any of the functions or macros, you must initialize
  the routines with:

    Domlette_IMPORT

  This would typically be done in your init function.

*/
  typedef struct {
    /* Domlette Node C Types */
    PyTypeObject *DOMImplementation_Type;
    PyTypeObject *Node_Type;
    PyTypeObject *Document_Type;
    PyTypeObject *Element_Type;
    PyTypeObject *Attr_Type;
    PyTypeObject *Text_Type;
    PyTypeObject *Comment_Type;
    PyTypeObject *ProcessingInstruction_Type;
    PyTypeObject *XPathNamespace_Type;

    /* Node Methods */
    int (*Node_RemoveChild)(NodeObject *parent, NodeObject *oldChild);
    int (*Node_AppendChild)(NodeObject *parent, NodeObject *newChild);
    int (*Node_InsertBefore)(NodeObject *parent, NodeObject *newChild,
                             NodeObject *refChild);
    int (*Node_ReplaceChild)(NodeObject *parent, NodeObject *newChild,
                             NodeObject *oldChild);

    /* Document Methods */
    DocumentObject *(*Document_New)(PyObject *documentURI);

    /* Element Methods */
    ElementObject *(*Element_New)(PyObject *namespaceURI,
                                  PyObject *qualifiedName,
                                  PyObject *localName);
    AttrObject *(*Element_SetAttributeNS)(ElementObject *element,
                                          PyObject *namespaceURI,
                                          PyObject *qualifiedName,
                                          PyObject *localName,
                                          PyObject *value);

    /* CharacterData Methods */
    PyObject *(*CharacterData_SubstringData)(CharacterDataObject *node,
                                             Py_ssize_t offset,
                                             Py_ssize_t count);
    int (*CharacterData_AppendData)(CharacterDataObject *node,
                                    PyObject *data);
    int (*CharacterData_InsertData)(CharacterDataObject *node,
                                    Py_ssize_t offset, PyObject *data);
    int (*CharacterData_DeleteData)(CharacterDataObject *node,
                                    Py_ssize_t offset, Py_ssize_t count);
    int (*CharacterData_ReplaceData)(CharacterDataObject *node,
                                     Py_ssize_t offset, Py_ssize_t count,
                                     PyObject *data);

    /* Text Methods */
    TextObject *(*Text_New)(PyObject *data);

    /* Comment Methods */
    CommentObject *(*Comment_New)(PyObject *data);

    /* ProcessingInstruction Methods */
    ProcessingInstructionObject *(*ProcessingInstruction_New)(PyObject *target,
                                                              PyObject *data);

  } Domlette_APIObject;

#ifdef Domlette_BUILDING_MODULE

#define XmlString_SHARED
#include "xmlstring.h"
#include "debug.h"
#include "nss.h"
#include "exceptions.h"
#include "domimplementation.h"
#include "namednodemap.h"
#include "xpathnamespace.h"

  /* namespace constants */
  extern PyObject *g_xmlNamespace;
  extern PyObject *g_xmlnsNamespace;

#else /* !defined(Domlette_BUILDING_MODULE) */

/* --- C API ----------------------------------------------------*/

  static Domlette_APIObject *Domlette;

#define Domlette_IMPORT Domlette = (Domlette_APIObject *) \
     PyCObject_Import(Domlette_MODULE_NAME, "CAPI")

#define DomletteDOMImplementation_Type Domlette->DOMImplementation_Type
#define DomletteNode_Type Domlette->Node_Type
#define DomletteDocument_Type Domlette->Document_Type
#define DomletteElement_Type Domlette->Element_Type
#define DomletteAttr_Type Domlette->Attr_Type
#define DomletteText_Type Domlette->Text_Type
#define DomletteComment_Type Domlette->Comment_Type
#define DomletteProcessingInstruction_Type Domlette->ProcessingInstruction_Type
#define DomletteXPathNamespace_Type Domlette->XPathNamespace_Type

#define Node_Check(op) PyObject_TypeCheck((op), DomletteNode_Type)
#define Node_CheckExact(op) ((op)->ob_type == DomletteNode_Type)
#define Node_RemoveChild Domlette->Node_RemoveChild
#define Node_AppendChild Domlette->Node_AppendChild
#define Node_InsertBefore Domlette->Node_InsertBefore
#define Node_ReplaceChild Domlette->Node_ReplaceChild

#define Document_Check(op) PyObject_TypeCheck((op), DomletteDocument_Type)
#define Document_CheckExact(op) ((op)->ob_type == DomletteDocument_Type)
#define Document_New Domlette->Document_New

#define Element_Check(op) PyObject_TypeCheck((op), DomletteElement_Type)
#define Element_CheckExact(op) ((op)->ob_type == DomletteElement_Type)
#define Element_New Domlette->Element_New
#define Element_SetAttributeNS Domlette->Element_SetAttributeNS

#define CharacterData_SubstringData Domlette->CharacterData_SubstringData
#define CharacterData_AppendData Domlette->CharacterData_AppendData
#define CharacterData_InsertData Domlette->CharacterData_InsertData
#define CharacterData_DeleteData Domlette->CharacterData_DeleteData
#define CharacterData_ReplaceData Domlette->CharacterData_ReplaceData

#define Text_Check(op) PyObject_TypeCheck((op), DomletteText_Type)
#define Text_CheckExact(op) ((op)->ob_type == DomletteText_Type)
#define Text_New Domlette->Text_New

#define Comment_Check(op) PyObject_TypeCheck((op), DomletteComment_Type)
#define Comment_CheckExact(op) ((op)->ob_type == DomletteComment_Type)
#define Comment_New Domlette->Comment_New

#define ProcessingInstruction_Check(op) \
  PyObject_TypeCheck((op), DomletteProcessingInstruction_Type)
#define ProcessingInstruction_CheckExact(op) \
  ((op)->ob_type == DomletteProcessingInstruction_Type)
#define ProcessingInstruction_New Domlette->ProcessingInstruction_New

#endif /* !Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_INTERFACE_H */
