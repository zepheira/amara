#ifndef XMLSTRING_H
#define XMLSTRING_H

#ifdef __cplusplus
extern "C" {
#endif

#define XmlString_MODULE_NAME "amara._xmlstring"

#include "Python.h"

  typedef struct {
    int (*IsSpace)(PyObject *str);
    int (*IsName)(PyObject *str);
    int (*IsNames)(PyObject *str);
    int (*IsNmtoken)(PyObject *str);
    int (*IsNmtokens)(PyObject *str);
    int (*IsQName)(PyObject *str);
    int (*IsNCName)(PyObject *str);
    int (*SplitQName)(PyObject *qualifiedName, PyObject **prefix,
                      PyObject **localName);
    PyObject *(*MakeQName)(PyObject *prefix, PyObject *localName);
    PyObject *(*NormalizeSpace)(PyObject *str);
    PyObject *(*FromObject)(PyObject *obj);
    PyObject *(*FromObjectInPlace)(PyObject *obj);
    PyObject *(*ConvertArgument)(PyObject *arg, char *name, int nullable);
  } XmlString_APIObject;

#define XmlString_Check PyUnicode_CheckExact
#define XmlString_NullCheck(op) ((op) == Py_None || XmlString_Check(op))

#define XmlString_FromASCII(s) PyUnicode_DecodeASCII((s), strlen(s), NULL)

#ifndef XmlString_BUILDING_MODULE

/* --- C API ----------------------------------------------------*/
#ifndef XmlString_EXPORT
#ifdef XmlString_SHARED
#define XmlString_EXPORT
#else
#define XmlString_EXPORT static
#endif
#endif
  XmlString_EXPORT XmlString_APIObject *XmlString_API;

#define XmlString_IMPORT XmlString_API = (XmlString_APIObject *) \
  PyCObject_Import(XmlString_MODULE_NAME, "CAPI")

#define XmlString_IsSpace XmlString_API->IsSpace
#define XmlString_IsName XmlString_API->IsName
#define XmlString_IsNames XmlString_API->IsNames
#define XmlString_IsNmtoken XmlString_API->IsNmtoken
#define XmlString_IsNmtokens XmlString_API->IsNmtokens
#define XmlString_IsQName XmlString_API->IsQName
#define XmlString_IsNCName XmlString_API->IsNCName
#define XmlString_SplitQName XmlString_API->SplitQName
#define XmlString_MakeQName XmlString_API->MakeQName
#define XmlString_NormalizeSpace XmlString_API->NormalizeSpace
#define XmlString_FromObject XmlString_API->FromObject
#define XmlString_FromObjectInPlace XmlString_API->FromObjectInPlace
#define XmlString_ConvertArgument XmlString_API->ConvertArgument

#endif /* XmlString_BUILDING_MODULE */

#ifdef __cplusplus
}
#endif

#endif /* XMLSTRING_H */
