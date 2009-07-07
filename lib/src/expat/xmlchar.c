#include "xmlchar.h"

#ifndef HAVE_USABLE_WCHAR_T
/* Return length of string S. */
size_t XMLChar_Len(register const XML_Char *s)
{
  register size_t len = 0;

  while (s[len] != '\0') {
    if (s[++len] == '\0')
      return len;
    if (s[++len] == '\0')
      return len;
    if (s[++len] == '\0')
      return len;
    ++len;
  }

  return len;
}

/* Compare S1 and S2, returning less than, equal to or
   greater than zero if S1 is lexicographically less than,
   equal to or greater than S2.  */
int XMLChar_Cmp(register const XML_Char *s1, register const XML_Char *s2)
{
  Py_UCS4 c1, c2;

  do {
    c1 = (Py_UCS4) *s1++;
    c2 = (Py_UCS4) *s2++;
    if (c1 == '\0')
      return c1 - c2;
  } while (c1 == c2);

  return c1 - c2;
}

/* Compare no more than N characters of S1 and S2,
   returning less than, equal to or greater than zero
   if S1 is lexicographically less than, equal to or
   greater than S2.  */
int XMLChar_NCmp(register const XML_Char *s1, register const XML_Char *s2,
                 size_t n)
{
  Py_UCS4 c1 = '\0';
  Py_UCS4 c2 = '\0';

  if (n >= 4) {
    size_t n4 = n >> 2;
    do {
      c1 = (Py_UCS4) *s1++;
      c2 = (Py_UCS4) *s2++;
      if (c1 == '\0' || c1 != c2)
        return c1 - c2;
      c1 = (Py_UCS4) *s1++;
      c2 = (Py_UCS4) *s2++;
      if (c1 == '\0' || c1 != c2)
        return c1 - c2;
      c1 = (Py_UCS4) *s1++;
      c2 = (Py_UCS4) *s2++;
      if (c1 == '\0' || c1 != c2)
        return c1 - c2;
      c1 = (Py_UCS4) *s1++;
      c2 = (Py_UCS4) *s2++;
      if (c1 == '\0' || c1 != c2)
        return c1 - c2;
    } while (--n4 > 0);
    n &= 3;
  }

  while (n > 0) {
    c1 = (Py_UCS4) *s1++;
    c2 = (Py_UCS4) *s2++;
    if (c1 == '\0' || c1 != c2)
      return c1 - c2;
    n--;
  }

  return c1 - c2;
}
#endif

XML_Char *XMLChar_FromObject(PyObject *obj)
{
  PyObject *unistr;
  XML_Char *result;
  size_t nbytes;

  assert(sizeof(XML_Char) == sizeof(Py_UNICODE));

  unistr = PyUnicode_FromObject(obj);
  if (unistr == NULL) return NULL;

  nbytes = (PyUnicode_GET_SIZE(unistr) + 1) * sizeof(XML_Char);
  result = (XML_Char *) malloc(nbytes);
  if (result == NULL) {
    PyErr_NoMemory();
  } else {
    /* Simple one-to-one copy of the Py_UNICODE data w/zero-terminator */
    memcpy(result, PyUnicode_AS_UNICODE(unistr), nbytes);
  }

  Py_DECREF(unistr);
  return result;
}

XML_Char *XMLChar_FromUnicode(const Py_UNICODE *u, Py_ssize_t size)
{
  XML_Char *result;

  result = (XML_Char *) malloc((size + 1) * sizeof(XML_Char));
  if (result == NULL) {
    PyErr_NoMemory();
  } else {
    /* Simple one-to-one copy of the Py_UNICODE data */
    memcpy(result, u, size * sizeof(XML_Char));
    /* Add the zero-terminator */
    result[size] = 0;
  }
  return result;
}

void _XMLChar_Print(FILE *fp, const XML_Char *s, size_t n, int flag)
{
  if (s == NULL) {
    fprintf(fp, "<nil>");
    return;
  }
  if (flag) fputc('"', fp);
  while (n-- > 0 && *s != '\0') {
    XML_Char ch = *s++;
    if (ch == '"' || ch == '\\')
      fprintf(fp, "\\%c", (char) ch);

#ifdef XML_UNICODE_WIDE
    /* Map 21-bit characters to '\U00xxxxxx' */
    else if (ch >= 0x10000)
      fprintf(fp, "\\U%08lx", (unsigned long) ch);
#endif

    /* Map UTF-16 surrogate pairs to Unicode \UXXXXXXXX escapes */
    else if (ch >= 0xD800 && ch < 0xDC00 && (*s && n > 0)) {
      XML_Char ch2 = *s;
      /* Valgrind reports this as an error, but it is not, due to the
       * "n > 0" guard above.
       */
      if (ch2 >= 0xDC00 && ch2 < 0xE000) {
        s++;
        n--;
        fprintf(fp, "\\U%08lx", (unsigned long)
                (((ch & 0x03FF) << 10) | (ch2 & 0x03FF)) + 0x10000);
      }
    }

    /* Map 16-bit characters (and isolated surrogates) to '\uxxxx' */
    else if (ch >= 256)
      fprintf(fp, "\\u%04x", (unsigned int) ch);

    /* Map special characters to escapes */
    else if (ch == '\t')
      fprintf(fp, "\\t");
    else if (ch == '\n')
      fprintf(fp, "\\n");
    else if (ch == '\r')
      fprintf(fp, "\\r");

    /* Map non-printable US ASCII to '\xhh' */
    else if (ch < ' ' || ch >= 0x7F)
      fprintf(fp, "\\x%02x", (unsigned int) ch);

    /* Copy everything else as-is */
    else
      fputc((char) ch, fp);
  }
  if (flag) fputc('"', fp);
}
