#ifndef EXPAT_XMLCHAR_H
#define EXPAT_XMLCHAR_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "lib/expat_external.h"

#ifndef XML_UNICODE
#error ExpatReader requires a Unicode-enabled Expat
#endif

  /* Use the platform optimized wide-char functions whenver possible */
#ifdef HAVE_USABLE_WCHAR_T
# define XMLChar_Len wcslen
# define XMLChar_Cmp wcscmp
# define XMLChar_NCmp wcsncmp
#else
  /* Calculates the length of the string s. */
  extern size_t XMLChar_Len(const XML_Char *s);

  /* Compares the two XML_Char strings s1 and s2. */
  extern int XMLChar_Cmp(const XML_Char *s1, const XML_Char *s2);

  /* Compares the first (at most) n characters of s1 and s2. */
  extern int XMLChar_NCmp(const XML_Char *s1, const XML_Char *s2, size_t n);
#endif

  /* Converts the unicode value of the PyObject to a new XML_Char buffer.
     It is the responsibility of the caller to free the result when done.
  */
  extern XML_Char* XMLChar_FromObject(PyObject *ob);
  extern XML_Char *XMLChar_FromUnicode(const Py_UNICODE *u, Py_ssize_t size);

#define XMLChar_DecodeSized(s, n) PyUnicode_FromUnicode((Py_UNICODE *)(s), (n))
#define XMLChar_Decode(s) XMLChar_DecodeSized((s), XMLChar_Len(s))


  extern void _XMLChar_Print(FILE *fp, const XML_Char *s, size_t n, int flag);
#define XMLChar_NPrint(fp, s, n) _XMLChar_Print((fp), (s), (n), 1)
#define XMLChar_Print(fp, s) _XMLChar_Print((fp), (s), INT_MAX, 1)
#define XMLChar_PrintRaw(fp, s) _XMLChar_Print((fp), (s), INT_MAX, 0)

#ifdef __cplusplus
}
#endif

#endif /* EXPAT_XMLCHAR_H */
