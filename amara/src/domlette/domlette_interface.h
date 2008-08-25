#ifndef DOMLETTE_INTERFACE_H
#define DOMLETTE_INTERFACE_H

#ifdef __cplusplus
extern "C" {
#endif

#define Domlette_MODULE_NAME  "amara._domlette"

#include "Python.h"
#include "structmember.h"

#include "node.h"
#include "document.h"
#include "element.h"
#include "attr.h"
#include "text.h"
#include "comment.h"
#include "processinginstruction.h"
#include "xpathnamespace.h"

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
    XPathNamespaceObject *(*Element_AddNamespace)(ElementObject *element,
                                                  PyObject *prefix,
                                                  PyObject *namespaceURI);
    AttrObject *(*Element_AddAttribute)(ElementObject *element,
                                        PyObject *namespaceURI,
                                        PyObject *qualifiedName,
                                        PyObject *localName,
                                        PyObject *value);
    PyObject *(*Element_InscopeNamespaces)(ElementObject *self);

    /* Text Methods */
    TextObject *(*Text_New)(PyObject *data);

    /* Comment Methods */
    CommentObject *(*Comment_New)(PyObject *data);

    /* ProcessingInstruction Methods */
    ProcessingInstructionObject *(*ProcessingInstruction_New)(PyObject *target,
                                                              PyObject *data);

    XPathNamespaceObject *(*XPathNamespace_New)(ElementObject *parent,
                                                PyObject *prefix, 
                                                PyObject *uri);

    /* NamespaceMap Methods */
    XPathNamespaceObject *(*NamespaceMap_Next)(PyObject *nodemap, 
                                               Py_ssize_t *pos);

    /* AttributeMap Methods */
    AttrObject *(*AttributeMap_Next)(PyObject *nodemap, Py_ssize_t *pos);

  } Domlette_APIObject;

#ifdef Domlette_BUILDING_MODULE

#ifndef XmlString_EXPORT
#define XmlString_EXPORT extern
#include "xmlstring.h"
#endif
#include "debug.h"
#include "exceptions.h"
#include "domimplementation.h"
#include "attributemap.h"
#include "namespacemap.h"

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
#define Element_AddNamespace Domlette->Element_AddNamespace
#define Element_AddAttribute Domlette->Element_AddAttribute
#define Element_InscopeNamespaces Domlette->Element_InscopeNamespaces

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

#define XPathNamespace_New Domlette->XPathNamespace_New

#define NamespaceMap_Next Domlette->NamespaceMap_Next

#define AttributeMap_Next Domlette->AttributeMap_Next

#endif /* !Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_INTERFACE_H */
