/***********************************************************************
 * amara/writers/src/xmlstream.c
 ***********************************************************************/

static char module_doc[] = "\
Encoding character stream writer that makes substitutions of illegal\n\
and unencodable characters.";

#include "Python.h"
#include "structmember.h"
#include "cStringIO.h"

#if defined(_WIN32) || defined(__WIN32__) && !defined(__CYGWIN__)
#  define strcasecmp stricmp
#endif

#define MODULE_NAME "amara.writers._xmlstream"
#define MODULE_INITFUNC init_xmlstream

/* Set if ASCII can be written directly to the underlying stream */
#define XMLSTREAM_FLAGS_ASCII_SAFE  1L<<0

/* Set if the UTF-16 BOM needs to be written */
#define XMLSTREAM_FLAGS_BOM_LE      1L<<1
#define XMLSTREAM_FLAGS_BOM_BE      1L<<2
#define XMLSTREAM_FLAGS_BOM (XMLSTREAM_FLAGS_BOM_LE|XMLSTREAM_FLAGS_BOM_BE)

/* Printer type */
typedef struct XmlStreamObject {
  PyObject_HEAD

  PyObject *stream;
  PyObject *encoding;

  FILE *fp;
  PyObject *write;
  Py_ssize_t (*write_func)(struct XmlStreamObject *, const char *, Py_ssize_t);

  PyObject *encode;
  unsigned long flags;
} XmlStreamObject;

typedef struct {
  PyObject_HEAD

  PyObject **entity_table;
  Py_UNICODE max_entity;
} EntityMapObject;

static PyTypeObject EntityMap_Type;
static PyObject *ascii_string;

/** XmlStream internal functions **************************************/

static Py_ssize_t
write_none(XmlStreamObject *self, const char *s, Py_ssize_t n)
{
  return n;
}

static Py_ssize_t
write_file(XmlStreamObject *self, const char *s, Py_ssize_t n)
{
  size_t byteswritten;

  Py_BEGIN_ALLOW_THREADS
  byteswritten = fwrite(s, sizeof(char), n, self->fp);
  Py_END_ALLOW_THREADS

  if (byteswritten != n) {
    PyErr_SetFromErrno(PyExc_IOError);
    return -1;
  }

  return n;
}

static Py_ssize_t
write_cStringIO(XmlStreamObject *self, const char *s, Py_ssize_t n)
{
  if (PycStringIO->cwrite((PyObject *)self->stream, (char *)s, n) != n) {
    return -1;
  }

  return n;
}

static Py_ssize_t
write_other(XmlStreamObject *self, const char *s, Py_ssize_t n)
{
  PyObject *result;

  result = PyObject_CallFunction(self->write, "s#", s, n);
  if (!result) {
    return -1;
  }

  Py_DECREF(result);
  return n;
}

Py_LOCAL_INLINE(PyObject *)
encode_unicode(XmlStreamObject *self, PyObject *unicode)
{
  PyObject *args, *result, *data;

  /* create the arguments tuple */
  args = PyTuple_New((Py_ssize_t)1);
  if (!args) {
    Py_DECREF(unicode);
    return NULL;
  }
  Py_INCREF(unicode);
  PyTuple_SET_ITEM(args, 0, unicode);

  /* call the encoder */
  result = PyEval_CallObject(self->encode, args);
  Py_DECREF(args);
  if (!result) return NULL;

  if (!PyTuple_Check(result) || PyTuple_GET_SIZE(result) != 2) {
    PyErr_SetString(PyExc_TypeError,
                    "encoder must return a tuple (object,integer)");
  }

  /* borrowed reference */
  data = PyTuple_GET_ITEM(result, 0);
  if (!PyString_Check(data)) {
    PyErr_Format(PyExc_TypeError,
                 "encoder did not return a string object (type=%.400s)",
                 data->ob_type->tp_name);
    Py_DECREF(result);
    return NULL;
  }

  Py_INCREF(data);
  Py_DECREF(result);
  return data;
}

Py_LOCAL_INLINE(Py_ssize_t)
write_encode(XmlStreamObject *self, PyObject *string, PyObject *where)
{
  PyObject *data;
  Py_ssize_t result;

  data = encode_unicode(self, string);
  if (!data) {
    if (PyErr_ExceptionMatches(PyExc_ValueError)) {
      /* assume encoding error */
      PyObject *repr, *str;

      repr = PyObject_Repr(string);
      if (!repr) return -1;

      if (where)
        str = PyObject_Str(where);
      else
        str = PyString_FromString("output");

      if (!str) {
        Py_DECREF(repr);
        return -1;
      }

      PyErr_Format(PyExc_ValueError, "Invalid character in %s %s",
                   PyString_AS_STRING(str), PyString_AS_STRING(repr));
      Py_DECREF(str);
      Py_DECREF(repr);
    }
    return -1;
  }

  result = self->write_func(self, PyString_AS_STRING(data),
                            PyString_GET_SIZE(data));
  Py_DECREF(data);
  return result;
}

Py_LOCAL_INLINE(int)
write_escaped(XmlStreamObject *self, PyObject *unicode)
{
  PyObject *data;
  Py_UNICODE *unistr;
  Py_ssize_t size;
  char charref[14]; /* charref: 10 digits (32-bits) plus '&#' and ';\0' */

  data = encode_unicode(self, unicode);
  if (!data) {
    /* Replace any characters not representable in this encoding with
     * their numerical character entity.
     */
    PyErr_Clear();
    size = PyUnicode_GET_SIZE(unicode);
    unistr = PyUnicode_AS_UNICODE(unicode);
    while (size-- > 0) {
      PyObject *unichar = PyUnicode_FromUnicode(unistr, (Py_ssize_t)1);
      data = encode_unicode(self, unichar);
      Py_DECREF(unichar);
      if (!data) {
        /* Found an offending character */
        PyErr_Clear();
        /* Note: use decimal form due to some broken browsers. */
        sprintf(charref, "&#%ld;", (long) *unistr);
        data = PyString_FromString(charref);
        if (!data) {
          return -1;
        }
      }
      if (self->write_func(self, PyString_AS_STRING(data),
                           PyString_GET_SIZE(data)) < 0) {
        Py_DECREF(data);
        return -1;
      }
      Py_DECREF(data);
      unistr++;
    }
  } else {
    if (self->write_func(self, PyString_AS_STRING(data),
                         PyString_GET_SIZE(data)) < 0) {
      Py_DECREF(data);
      return -1;
    }
    Py_DECREF(data);
  }

  return 0;
}

Py_LOCAL_INLINE(Py_ssize_t)
write_ascii(XmlStreamObject *self, PyObject *string)
{
  PyObject *unicode;
  Py_ssize_t result;

  if (self->flags & XMLSTREAM_FLAGS_ASCII_SAFE)
    /* shortcut, write it directly */
    return self->write_func(self, PyString_AS_STRING(string),
                            PyString_GET_SIZE(string));

  /* ASCII must be encoded before writing it to the stream */
  unicode = PyUnicode_DecodeASCII(PyString_AS_STRING(string),
                                  PyString_GET_SIZE(string),
                                  "strict");
  if (unicode == NULL)
    return -1;
  result = write_encode(self, unicode, NULL);
  Py_DECREF(unicode);
  return result;
}

/** XmlStream Object *************************************************/

static char xmlstream_doc[] = \
"xmlstream(stream, encoding)\n\
\n\
`stream` must be a file-like object open for writing (binary) data.\n\
`encoding` specifies the encoding which is to be used for the stream.\n\
";

static PyObject *
xmlstream_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  XmlStreamObject *self;
  PyObject *stream, *encoding;
  static char *kwlist[] = { "stream", "encoding", NULL };
  PyObject *test;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "OS:xmlstream", kwlist,
                                   &stream, &encoding))
    return NULL;

  self = (XmlStreamObject *)type->tp_alloc(type, 1);
  if (self == NULL)
    return NULL;

  if (PyFile_Check(stream)) {
    self->fp = PyFile_AsFile(stream);
    if (self->fp == NULL) {
      PyErr_SetString(PyExc_ValueError, "I/O operation on closed file");
      Py_DECREF(self);
      return NULL;
    }
    self->write_func = write_file;
  }
  else if (PycStringIO_OutputCheck(stream)) {
    self->write_func = write_cStringIO;
  }
  else if (stream == Py_None) {
    self->write_func = write_none;
  }
  else {
    self->write_func = write_other;
    self->write = PyObject_GetAttrString(stream, "write");
    if (self->write == NULL) {
      PyErr_SetString(PyExc_TypeError,
                      "stream argument must have a 'write' attribute");
      Py_DECREF(self);
      return NULL;
    }
  }

  if (strcasecmp(PyString_AS_STRING(encoding), "utf-16") == 0) {
    /* use either utf-16le or utf-16be to prevent BOM on every encode */
    /* this test is taken from Python's sysmodule for sys.byteorder */
    unsigned long number = 1;
    char *s = (char *) &number;
    if (s[0] == 0) {
      /* big endian */
      self->flags |= XMLSTREAM_FLAGS_BOM_BE;
      self->encode = PyCodec_Encoder("utf-16be");
    } else {
      /* little endian */
      self->flags |= XMLSTREAM_FLAGS_BOM_BE;
      self->encode = PyCodec_Encoder("utf-16le");
    }
  } else {
    self->encode = PyCodec_Encoder(PyString_AsString(encoding));
  }
  if (self->encode == NULL) {
    Py_DECREF(self);
    return NULL;
  }

  Py_INCREF(stream);
  self->stream = stream;

  Py_INCREF(encoding);
  self->encoding = encoding;

  /* Determine if we can write ASCII directly to the stream */
  test = encode_unicode(self, ascii_string);
  if (test == NULL)
    PyErr_Clear();
  else {
    if (PyString_Check(test) && PyString_GET_SIZE(test) == 128)
      self->flags |= XMLSTREAM_FLAGS_ASCII_SAFE;
    Py_DECREF(test);
  }

  return (PyObject *)self;
}

static char write_ascii_doc[] =
"write_ascii(string)\n\
\n\
Writes the ASCII string as is to the stream.";

static PyObject *xmlstream_write_ascii(XmlStreamObject *self, PyObject *args)
{
  PyObject *data;

  if (!PyArg_ParseTuple(args, "S:write_ascii", &data))
    return NULL;

  if (self->flags & XMLSTREAM_FLAGS_BOM) {
    char *bom = (self->flags & XMLSTREAM_FLAGS_BOM_LE)
                ? "\xFF\xFE" : "\xFE\xFF";
    if (self->write_func(self, bom, 2) < 0)
      return NULL;
    /* clear the flag */
    self->flags &= ~XMLSTREAM_FLAGS_BOM;
  }

  if (write_ascii(self, data) < 0)
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char write_encode_doc[] =
"write_encode(unicode[, where])\n\
\n\
Writes the unicode string encoded to the stream.\n\
\n\
Raises ValueError if the string cannot be encoded with `where` specifying\n\
the place of the error.  If not given the string 'output' is used.";

static PyObject *xmlstream_write_encode(XmlStreamObject *self, PyObject *args)
{
  PyObject *string, *where=NULL;

  if (!PyArg_ParseTuple(args, "U|O:writeEncode", &string, &where))
    return NULL;

  if (self->flags & XMLSTREAM_FLAGS_BOM) {
    char *bom = (self->flags & XMLSTREAM_FLAGS_BOM_LE)
                ? "\xFF\xFE" : "\xFE\xFF";
    if (self->write_func(self, bom, 2) < 0)
      return NULL;
    /* clear the flag */
    self->flags &= ~XMLSTREAM_FLAGS_BOM;
  }

  if (write_encode(self, string, where) < 0)
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static char write_escape_doc[] =
"write_escape(unicode, entitymap])\n\
\n\
Writes the unicode string encoded to the stream.\n\
\n\
`entitymap` contains the characters which will be escaped by charrefs.\n\
Additional, any character that cannot be encoded is replaced with its\n\
numerical character entity.  Illegal XML characters are replaced by '?'.";

/* Legal XML characters are:
 *   0x09 0x0A 0x0D 0x20-0xD7FF 0xE000-0xFFFD 0x10000-0x10FFFF */
#define LEGAL_UCS2(c) ((c) == 0x09 || (c) == 0x0A || (c) == 0x0D || \
                       (((c) >= 0x20) && ((c) <= 0xD7FF)) || \
                       (((c) >= 0xE000) && ((c) <= 0xFFFD)))
#define LEGAL_UCS4(c) (((c) >= 0x10000) && ((c) <= 0x10FFFF))

#ifdef Py_UNICODE_WIDE
#define LEGAL_XML_CHAR(c) (LEGAL_UCS2(c) || LEGAL_UCS4(c))
#else
#define LEGAL_XML_CHAR LEGAL_UCS2
#endif

static PyObject *xmlstream_write_escape(XmlStreamObject *self, PyObject *args)
{
  PyObject *string;
  EntityMapObject *entities;
  PyObject *newstr = NULL;
  Py_UNICODE *p, *chunk_start;
  Py_ssize_t size;
  Py_ssize_t chunk_size;

  if (!PyArg_ParseTuple(args, "UO!:writeEscape", &string,
                        &EntityMap_Type, &entities))
    return NULL;

  if (self->flags & XMLSTREAM_FLAGS_BOM) {
    char *bom = (self->flags & XMLSTREAM_FLAGS_BOM_LE)
                ? "\xFF\xFE" : "\xFE\xFF";
    if (self->write_func(self, bom, 2) < 0)
      return NULL;
    /* clear the flag */
    self->flags &= ~XMLSTREAM_FLAGS_BOM;
  }

  /* this might get replaced */
  Py_INCREF(string);

  /* Replace any illegal characters with '?' */
  size = PyUnicode_GET_SIZE(string);
  p = PyUnicode_AS_UNICODE(string);
  while (size-- > 0) {
    if (!LEGAL_XML_CHAR(*p)) {
      /* replace it */
      if (newstr == NULL) {
        /* create a copy to work with */
        newstr = PyUnicode_FromUnicode(PyUnicode_AS_UNICODE(string),
                                       PyUnicode_GET_SIZE(string));
        if (newstr == NULL) return NULL;

        /* move pointer to the correct location in the copy */
        p = PyUnicode_AS_UNICODE(newstr) + (p - PyUnicode_AS_UNICODE(string));

        /* replaced passed in unicode object with the copy */
        Py_DECREF(string);
        string = newstr;
      }
      *p = '?';
    }
    p++;
  }

  /* Write out the string replacing the entities given by EntityMap as we go */
  size = PyUnicode_GET_SIZE(string);
  p = chunk_start = PyUnicode_AS_UNICODE(string);
  while (size-- > 0) {
    if (*p <= entities->max_entity && entities->entity_table[*p]) {
      PyObject *repl = entities->entity_table[*p];

      /* write out everything up to the character to replace */
      chunk_size = p - chunk_start;
      if (chunk_size > 0) {
        newstr = PyUnicode_FromUnicode(chunk_start, chunk_size);
        if (write_escaped(self, newstr) < 0) {
          Py_DECREF(newstr);
          Py_DECREF(string);
          return NULL;
        }
        Py_DECREF(newstr);
      }

      /* the entities are stored as PyStrings or callable objects */
      if (PyString_Check(repl)) {
        /* a direct string replacement */
        Py_INCREF(repl);
      } else {
        /* a callable that generates the replacement string */
        repl = PyObject_CallFunction(repl, "Oi", string,
                                     (p - PyUnicode_AS_UNICODE(string)));
        if (repl == NULL) {
          Py_DECREF(string);
          return NULL;
        } else if (!PyString_Check(repl)) {
          PyErr_Format(PyExc_TypeError,
                       "expected string, but %.200s found",
                       repl->ob_type->tp_name);
          Py_DECREF(repl);
          Py_DECREF(string);
          return NULL;
        }
      }

      /* write the replacement string */
      if (write_ascii(self, repl) < 0) {
        Py_DECREF(string);
        Py_DECREF(repl);
        return NULL;
      }
      Py_DECREF(repl);

      /* skip over the replaced character */
      chunk_start = p + 1;
    }
    p++;
  }

  chunk_size = p - chunk_start;
  /* write out remaining text */
  if (chunk_size > 0) {
    newstr = PyUnicode_FromUnicode(chunk_start, chunk_size);
    if (write_escaped(self, newstr) < 0) {
      Py_DECREF(newstr);
      Py_DECREF(string);
      return NULL;
    }
    Py_DECREF(newstr);
  }

  Py_DECREF(string);
  Py_INCREF(Py_None);
  return Py_None;
}

static void xmlstream_dealloc(XmlStreamObject *self)
{
  Py_XDECREF(self->write);
  Py_XDECREF(self->encode);
  Py_XDECREF(self->stream);
  Py_XDECREF(self->encoding);

  ((PyObject *)self)->ob_type->tp_free((PyObject *)self);
}

static PyObject *xmlstream_repr(XmlStreamObject *self)
{
  char buf[512];
  PyObject *repr = PyObject_Repr(self->stream);
  if (repr == NULL)
    return NULL;

  sprintf(buf, "<%s at %p, stream=%.256s, encoding='%.128s'>",
          self->ob_type->tp_name, self, PyString_AsString(repr),
          PyString_AsString(self->encoding));
  Py_DECREF(repr);

  return PyString_FromString(buf);
}

/** Python Methods ****************************************************/

static PyMethodDef xmlstream_methods[] = {
  { "write_ascii",  (PyCFunction)xmlstream_write_ascii, METH_VARARGS,
    write_ascii_doc },
  { "write_encode", (PyCFunction)xmlstream_write_encode, METH_VARARGS,
    write_encode_doc },
  { "write_escape", (PyCFunction)xmlstream_write_escape, METH_VARARGS,
    write_escape_doc },
  { NULL }
};

/** Python Members ****************************************************/

static PyMemberDef xmlstream_members[] = {
  { "stream",   T_OBJECT, offsetof(XmlStreamObject, stream),   RO },
  { "encoding", T_OBJECT, offsetof(XmlStreamObject, encoding), RO },
  { NULL }
};

/** Python Computed Members *******************************************/

static PyGetSetDef xmlstream_getsets[] = {
  { NULL }
};

static PyTypeObject XmlStream_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".xmlstream",
  /* tp_basicsize      */ sizeof(XmlStreamObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) xmlstream_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) xmlstream_repr,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) 0,
  /* tp_as_mapping     */ (PyMappingMethods *) 0,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) 0,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ Py_TPFLAGS_DEFAULT,
  /* tp_doc            */ (char *) xmlstream_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) xmlstream_methods,
  /* tp_members        */ (PyMemberDef *) xmlstream_members,
  /* tp_getset         */ (PyGetSetDef *) xmlstream_getsets,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) xmlstream_new,
  /* tp_free           */ 0,
};

/** EntityMap Object **************************************************/

static char entitymap_doc[] = \
"entitymap(entities)\n\
\n\
Creates an `entitymap` used for writing escaped characters.  The key in the\n\
mapping represents the character to escape and the value is the replacement.";

/* EntityMap Python interface */

/* EntityMap methods */

static PyObject *
entitymap_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  EntityMapObject *self;
  static char *kwlist[] = { "entities", NULL };
  PyObject *entities, *keys, *seq, *key, *value;
  Py_ssize_t size, i;
  Py_UNICODE ord;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "O!:entitymap", kwlist,
                                   &PyDict_Type, &entities))
    return NULL;

  /* create a copy of the mapping (doesn't need to be a dictionary) */
  keys = PyMapping_Keys(entities);
  if (keys == NULL)
    return NULL;
  seq = PySequence_Fast(keys, "keys() returned non-iterable");
  Py_DECREF(keys);
  if (seq == NULL)
    return NULL;

  self = (EntityMapObject *)type->tp_alloc(type, 1);
  if (self == NULL) {
    Py_DECREF(seq);
    return NULL;
  }

  /* find the largest character ordinal also do validation */
  for (i = 0, size = PySequence_Fast_GET_SIZE(seq); i < size; i++) {
    key = PySequence_Fast_GET_ITEM(seq, i);
    if (PyString_Check(key)) {
      if (PyString_GET_SIZE(key) == 1) {
        ord = (Py_UNICODE)((unsigned char)*PyString_AS_STRING(key));
      } else {
        PyErr_Format(PyExc_TypeError,
                     "expected a character, but string of length %zd found",
                     PyString_GET_SIZE(key));
        Py_DECREF(self);
        return NULL;
      }
    } else if (PyUnicode_Check(key)) {
      if (PyUnicode_GET_SIZE(key) == 1) {
        ord = *PyUnicode_AS_UNICODE(key);
      } else {
        PyErr_Format(PyExc_TypeError,
                     "expected a character, but string of length %zd found",
                     PyUnicode_GET_SIZE(key));
        Py_DECREF(self);
        return NULL;
      }
    } else {
      PyErr_Format(PyExc_TypeError,
                   "expected string of length 1, but %.200s found",
                   key->ob_type->tp_name);
      Py_DECREF(self);
      return NULL;
    }

    if (ord > self->max_entity) self->max_entity = ord;

    value = PyObject_GetItem(entities, key);
    if (value == NULL) {
      Py_DECREF(seq);
      Py_DECREF(self);
      return NULL;
    } else if (!(PyString_Check(value) || PyCallable_Check(value))) {
      PyErr_Format(PyExc_TypeError,
                   "expected string or callable object, but %.200s found",
                   value->ob_type->tp_name);
      Py_DECREF(value);
      Py_DECREF(seq);
      Py_DECREF(self);
      return NULL;
    }

    Py_DECREF(value);
  }

  /* create the access table */
  self->entity_table = (PyObject **)calloc(self->max_entity + 1,
                                           sizeof(PyObject *));
  if (self->entity_table == NULL) {
    Py_DECREF(seq);
    Py_DECREF(self);
    PyErr_NoMemory();
    return NULL;
  }

  for (i = 0; i < size; i++) {
    key = PySequence_Fast_GET_ITEM(seq, i);

    if (PyString_Check(key)) {
      ord = (Py_UNICODE)((unsigned char)*PyString_AS_STRING(key));
    } else {
      ord = *PyUnicode_AS_UNICODE(key);
    }

    value = PyObject_GetItem(entities, key);
    if (value == NULL) {
      Py_DECREF(seq);
      Py_DECREF(self);
      return NULL;
    }

    self->entity_table[ord] = value;
  }
  Py_DECREF(seq);

  return (PyObject *)self;
}

static void entitymap_dealloc(EntityMapObject *self)
{
  if (self->entity_table != NULL) {
    /* destroy the entity lookup table */
    Py_UNICODE i;

    for (i = 0; i <= self->max_entity; i++) {
      Py_XDECREF(self->entity_table[i]);
    }
    free(self->entity_table);
  }

  ((PyObject *)self)->ob_type->tp_free((PyObject *)self);
}

static PyObject *entitymap_repr(EntityMapObject *self)
{
  return PyString_FromFormat("<%.200s at %p>", self->ob_type->tp_name, self);
}

/** Python Methods ****************************************************/

static PyMethodDef entitymap_methods[] = {
  { NULL }
};

/** Python Members ****************************************************/

static PyMemberDef entitymap_members[] = {
  { NULL }
};

/** Python Computed Members *******************************************/

static PyObject *entitymap_entities(EntityMapObject *self, void *arg)
{
  /* build a dictionary from the entity lookup table */
  PyObject *entities = PyDict_New();
  Py_UNICODE i;

  if (entities != NULL) {
    for (i = 0; i <= self->max_entity; i++) {
      PyObject *value = self->entity_table[i];
      if (value != NULL) {
        PyObject *key = PyInt_FromLong(i);
        if (key == NULL) {
          Py_DECREF(entities);
          return NULL;
        }
        if (PyDict_SetItem(entities, key, value) < 0) {
          Py_DECREF(key);
          Py_DECREF(entities);
          return NULL;
        }
        Py_DECREF(key);
      }
    }
  }
  return entities;
}

static PyGetSetDef entitymap_getsets[] = {
  { "entities", (getter) entitymap_entities },
  { NULL }
};

static PyTypeObject EntityMap_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".entitymap",
  /* tp_basicsize      */ sizeof(EntityMapObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) entitymap_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) entitymap_repr,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) 0,
  /* tp_as_mapping     */ (PyMappingMethods *) 0,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) 0,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ Py_TPFLAGS_DEFAULT,
  /* tp_doc            */ (char *) entitymap_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) entitymap_methods,
  /* tp_members        */ (PyMemberDef *) entitymap_members,
  /* tp_getset         */ (PyGetSetDef *) entitymap_getsets,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) entitymap_new,
  /* tp_free           */ 0,
};

/** Module Interface **************************************************/

static PyMethodDef module_methods[] = {
  { NULL }
};

PyMODINIT_FUNC MODULE_INITFUNC(void)
{
  PyObject *module, *dict;

  PycString_IMPORT;

  if (PyType_Ready(&XmlStream_Type) < 0)
    return;
  if (PyType_Ready(&EntityMap_Type) < 0)
    return;

  module = Py_InitModule3(MODULE_NAME, module_methods, module_doc);
  if (module == NULL)
    return;
  dict = PyModule_GetDict(module);
  if (PyDict_SetItemString(dict, "xmlstream", (PyObject *)&XmlStream_Type) < 0)
    return;
  if (PyDict_SetItemString(dict, "entitymap", (PyObject *)&EntityMap_Type) < 0)
    return;

  ascii_string =
    PyUnicode_DecodeASCII("\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09"
                          "\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13"
                          "\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d"
                          "\x1e\x1f !\"#$%&\'()*+,-./0123456789:;<="
                          ">?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcd"
                          "efghijklmnopqrstuvwxyz{|}~\x7f",
                          128, "strict");
  if (ascii_string == NULL)
    return;

  return;
}
