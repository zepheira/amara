#ifndef DOMLETTE_INTERFACE_H
#define DOMLETTE_INTERFACE_H

#ifdef __cplusplus
extern "C" {
#endif

#define Domlette_MODULE_NAME  "amara.tree"

#include "Python.h"
#include "structmember.h"

#include "node.h"
#include "entity.h"
#include "element.h"
#include "attr.h"
#include "text.h"
#include "comment.h"
#include "processinginstruction.h"
#include "namespace.h"

/*

  This header provides access to Domlette's interface from C.

  Before calling any of the functions or macros, you must initialize
  the routines with:

    Domlette_IMPORT

  This would typically be done in your init function.

*/
  typedef struct {
    /* Domlette Node C Types */
    PyTypeObject *Node_Type;
    PyTypeObject *Entity_Type;
    PyTypeObject *Element_Type;
    PyTypeObject *Attr_Type;
    PyTypeObject *Text_Type;
    PyTypeObject *Comment_Type;
    PyTypeObject *ProcessingInstruction_Type;
    PyTypeObject *Namespace_Type;

    /* Node Methods */
    int (*Container_Remove)(NodeObject *parent, NodeObject *child);
    int (*Container_Append)(NodeObject *parent, NodeObject *child);
    int (*Container_Insert)(NodeObject *parent, Py_ssize_t where,
                            NodeObject *child);
    int (*Container_Replace)(NodeObject *parent, NodeObject *oldChild,
                             NodeObject *newChild);

    /* Document Methods */
    EntityObject *(*Entity_New)(PyObject *documentURI);

    /* Element Methods */
    ElementObject *(*Element_New)(PyObject *namespaceURI,
                                  PyObject *qualifiedName,
                                  PyObject *localName);
    NamespaceObject *(*Element_AddNamespace)(ElementObject *element,
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

    NamespaceObject *(*Namespace_New)(PyObject *prefix, PyObject *uri);

    /* NamespaceMap Methods */
    NamespaceObject *(*NamespaceMap_Next)(PyObject *nodemap, Py_ssize_t *ppos);

    /* AttributeMap Methods */
    AttrObject *(*AttributeMap_Next)(PyObject *nodemap, Py_ssize_t *ppos);

  } Domlette_APIObject;

#ifdef Domlette_BUILDING_MODULE

#ifndef XmlString_EXPORT
#define XmlString_EXPORT extern
#include "xmlstring.h"
#endif
#include "debug.h"
#include "exceptions.h"
#include "attributemap.h"
#include "namespacemap.h"

#else /* !defined(Domlette_BUILDING_MODULE) */

/* --- C API ----------------------------------------------------*/

  static Domlette_APIObject *Domlette;

#define Domlette_IMPORT Domlette = (Domlette_APIObject *) \
     PyCObject_Import(Domlette_MODULE_NAME, "CAPI")

#define DomletteNode_Type Domlette->Node_Type
#define DomletteEntity_Type Domlette->Entity_Type
#define DomletteElement_Type Domlette->Element_Type
#define DomletteAttr_Type Domlette->Attr_Type
#define DomletteText_Type Domlette->Text_Type
#define DomletteComment_Type Domlette->Comment_Type
#define DomletteProcessingInstruction_Type Domlette->ProcessingInstruction_Type
#define DomletteNamespace_Type Domlette->Namespace_Type

#define Node_Check(op) PyObject_TypeCheck((op), DomletteNode_Type)
#define Node_CheckExact(op) ((op)->ob_type == DomletteNode_Type)

#define Container_Remove Domlette->Container_Remove
#define Container_Append Domlette->Container_Append
#define Container_Insert Domlette->Container_Insert
#define Container_Replace Domlette->Container_Replace

#define Entity_Check(op) PyObject_TypeCheck((op), DomletteEntity_Type)
#define Entity_CheckExact(op) ((op)->ob_type == DomletteEntity_Type)
#define Entity_New Domlette->Entity_New

#define Element_Check(op) PyObject_TypeCheck((op), DomletteElement_Type)
#define Element_CheckExact(op) ((op)->ob_type == DomletteElement_Type)
#define Element_New Domlette->Element_New
#define Element_AddNamespace Domlette->Element_AddNamespace
#define Element_AddAttribute Domlette->Element_AddAttribute
#define Element_InscopeNamespaces Domlette->Element_InscopeNamespaces

#define Attr_Check(op) PyObject_TypeCheck((op), DomletteAttr_Type)

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

#define Namespace_Check(op) PyObject_TypeCheck((op), DomletteNamespace_Type)

#define Namespace_New Domlette->Namespace_New

#define NamespaceMap_Next Domlette->NamespaceMap_Next

#define AttributeMap_Next Domlette->AttributeMap_Next

#endif /* !Domlette_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* DOMLETTE_INTERFACE_H */
