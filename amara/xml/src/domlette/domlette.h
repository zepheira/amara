#ifndef DOMLETTE_H
#define DOMLETTE_H

#ifdef __cplusplus
extern "C" {
#endif

#if defined(_WIN32) || defined(__WIN32__)
#  define strcasecmp stricmp
#endif

#include "Python.h"
#include "structmember.h"
#include "../common.h"

#define XmlString_SHARED
#include "xmlstring.h"

#include "debug.h"

#include "exceptions.h"
#include "node.h"
#include "namednodemap.h"
#include "document.h"
#include "element.h"
#include "attr.h"
#include "domimplementation.h"
#include "text.h"
#include "processinginstruction.h"
#include "comment.h"
#include "xpathnamespace.h"

  /* namespace constants */
  extern PyObject *g_xmlNamespace;
  extern PyObject *g_xmlnsNamespace;

#define DOMLETTE_PACKAGE  "Ft.Xml.cDomlette."

#ifdef __cplusplus
}
#endif
#endif /* !DOMLETTEOBJECT_H */

