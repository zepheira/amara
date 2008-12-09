/***********************************************************************
 * amara/xpath/src/datatypes.c
 ***********************************************************************/

static char module_doc[] = "\
Implementation of XPath data types\n\
";

#define MODULE_NAME "amara.xpath._datatypes"
#define MODULE_INITFUNC init_datatypes

#include "Python.h"
#include "structmember.h"
#include "domlette_interface.h"

/* Floating-point classification macros */
#if __STDC_VERSION__ < 199901L
#  if defined(_WIN32) || defined(__WIN32__)
#    ifdef __MINGW32__
#      include <math.h>
#    else
#      include <float.h>
#      define isnan(x) _isnan(x)
#      define isfinite(x) _finite(x)
#      define isinf(x) (!isfinite(x) && !isnan(x))
#    endif
#  elif (defined(__sun) || defined(__sgi) || defined(__svr4__) || \
         defined(__osf__))
#    include <ieeefp.h>
#    define isfinite(x) finite(x)
#    define isinf(x) (!isfinite(x) && !isnan(x))
#  else
#    ifndef isnan
#      define isnan(x) ((x) != (x))
#    endif
#    ifndef isinf
#      define isinf(x) ((x) && (x)*0.5 == (x))
#    endif
#    ifndef isfinite
#      define isfinite(x) (isnan(x) == isinf(x))
#    endif
#  endif
#endif

typedef PyObject XPathObject;
static PyTypeObject XPathObject_Type;

typedef PyUnicodeObject XPathStringObject;
static PyTypeObject XPathString_Type;
#define String_Check(ob) ((ob)->ob_type == &XPathString_Type)
static PyObject *String_Empty;
static PyObject *String_True;
static PyObject *String_False;

typedef PyFloatObject XPathNumberObject;
static PyTypeObject XPathNumber_Type;
#define Number_Check(ob) ((ob)->ob_type == &XPathNumber_Type)
static PyObject *Number_One;
static PyObject *Number_Zero;
static PyObject *Number_NegZero;
static PyObject *Number_NaN;
static PyObject *Number_NegInf;
static PyObject *Number_PosInf;

typedef PyIntObject XPathBooleanObject;
static PyTypeObject XPathBoolean_Type;
#define Boolean_Check(ob) ((ob)->ob_type == &XPathBoolean_Type)
static PyObject *Boolean_False;
static PyObject *Boolean_True;

typedef PyListObject XPathNodeSetObject;
static PyTypeObject XPathNodeSet_Type;
#define NodeSet_Check(ob) PyObject_TypeCheck((ob), &XPathNodeSet_Type)

static int join_descendants(NodeObject *node, PyObject **result, 
                            Py_ssize_t *used)
{
  Py_ssize_t i, n;

  assert(Element_Check(node) || Entity_Check(node));
  n = Container_GET_COUNT(node);
  for (i = 0; i < n; i++) {
    NodeObject *child = Container_GET_CHILD(node, i);
    if (Element_Check(child)) {
      if (join_descendants(child, result, used) < 0)
        return -1;
    } else if (Text_Check(child)) {
      Py_ssize_t count, new_used, allocated;
      PyObject *value = Text_GET_VALUE(child);
      assert(PyUnicode_Check(value));

      count = PyUnicode_GET_SIZE(value);
      new_used = *used + count;
      if (new_used < 0)
        goto overflow;
      allocated = PyUnicode_GET_SIZE(*result);
      if (new_used > allocated) {
        /* double allocated size until it's big enough */
        do {
            allocated <<= 1;
            if (allocated <= 0)
              goto overflow;
        } while (new_used > allocated);
        if (PyUnicode_Resize(result, allocated) < 0)
          goto error;
      }
      Py_UNICODE_COPY(PyUnicode_AS_UNICODE(*result) + *used,
                      PyUnicode_AS_UNICODE(value), count);
      *used = new_used;
    }
  }
  return 0;

 overflow:
  PyErr_NoMemory();
 error:
  return -1;
}

static PyObject *node_to_string(PyObject *node)
{
  PyObject *result;

  /* convert amara.tree node to string */
  if (Element_Check(node) || Entity_Check(node)) {
    /* The concatenation of all text descendants in document order */
    Py_ssize_t used = 0;
    PyObject *result = PyUnicode_FromUnicode(NULL, 100);
    if (result == NULL)
      return NULL;
    if (join_descendants((NodeObject *)node, &result, &used) < 0) {
      Py_DECREF(result);
      return NULL;
    }
    if (PyUnicode_Resize(&result, used) < 0) {
      Py_DECREF(result);
      return NULL;
    }
    return result;
  }
  if (Attr_Check(node)) {
    result = Attr_GET_VALUE(node);
    Py_INCREF(result);
    return result;
  }
  if (Text_Check(node) || Comment_Check(node)) {
    result = CharacterData_GET_VALUE(node);
    Py_INCREF(result);
    return result;
  }
  if (ProcessingInstruction_Check(node)) {
    result = ProcessingInstruction_GET_DATA(node);
    Py_INCREF(result);
    return result;
  }
  if (Namespace_Check(node)) {
    result = Namespace_GET_VALUE(node);
    Py_INCREF(result);
    return result;
  }
  return PyUnicode_FromUnicode(NULL, 0);
}

static PyObject *String_New(PyObject *value)
{
  XPathStringObject *self;
  Py_ssize_t length;

  if (String_Check(value)) {
    Py_INCREF(value);
    return value;
  }

  if (Boolean_Check(value)) {
    value = (value == Boolean_True) ? String_True : String_False;
    Py_INCREF(value);
    return value;
  }

  if (Number_Check(value)) {
    if (value == Number_NaN) {
      value = PyUnicode_DecodeASCII("NaN", 3, NULL);
    } else if (value == Number_PosInf) {
      value = PyUnicode_DecodeASCII("Infinity", 8, NULL);
    } else if (value == Number_NegInf) {
      value = PyUnicode_DecodeASCII("-Infinity", 9, NULL);
    } else {
      double d = PyFloat_AS_DOUBLE(value);
      if (floor(d) == d) {
        /* format as integer */
        value = PyLong_FromDouble(d);
      } else {
        /* worst case length calc to ensure no buffer overrun:
           fmt = %#.<prec>g
           buf = '-' + [0-9]*prec + '.' + 'e+' + (longest exp for
                                                  any double rep.)
           len = 1 + prec + 1 + 2 + 5 = 9 + prec
           If prec=0 the effective precision is 1 (the leading digit is
           always given), therefore increase by one to 10+prec.
        */
        char buf[32]; /* only 10 + 12 + '\0' is needed, more than enough */
        int len;
        len = PyOS_snprintf(buf, 32, "%0.12g", d);
        value = PyUnicode_DecodeASCII(buf, len, "strict");
      }
    }
    if (value == NULL) return NULL;
  } else if (NodeSet_Check(value)) {
    if (PyList_GET_SIZE(value) == 0) {
      Py_INCREF(String_Empty);
      return String_Empty;
    }
    value = PyList_GET_ITEM(value, 0);
    Py_INCREF(value);
  } else {
    Py_INCREF(value);
  }

  if (Node_Check(value)) {
    /* we know that `value` has been incref'ed */
    Py_DECREF(value);
    value = node_to_string(value);
  }

  /* Python object */
  if (!PyUnicode_Check(value)) {
    PyObject *tmp = PyObject_Unicode(value);
    Py_DECREF(value);
    if (tmp == NULL) return NULL;
    value = tmp;
  }
  assert(PyUnicode_Check(value));
  length = PyUnicode_GET_SIZE(value);
  if (length == 0) {
    Py_DECREF(value);
    Py_INCREF(String_Empty);
    return String_Empty;
  }
  /* Inline unicode_subtype_new() */
  self = (XPathStringObject *) XPathString_Type.tp_alloc(&XPathString_Type, 0);
  if (self != NULL) {
    self->str = PyMem_New(Py_UNICODE, length + 1);
    if (self->str == NULL) {
      _Py_ForgetReference((PyObject *)self);
      PyObject_Del(self);
      Py_DECREF(value);
      return PyErr_NoMemory();
    }
    Py_UNICODE_COPY(self->str, PyUnicode_AS_UNICODE(value), length + 1);
    self->length = length;
    self->hash = -1;
  }
  Py_DECREF(value);
  return (PyObject *)self;

}

static PyObject *_Number_New(double fval)
{
  XPathNumberObject *self;
  if (fval == 0.0) {
    Py_INCREF(Number_Zero);
    return Number_Zero;
  }
  else if (fval == 1.0) {
    Py_INCREF(Number_One);
    return Number_One;
  }
  self = (XPathNumberObject *) XPathNumber_Type.tp_alloc(&XPathNumber_Type, 0);
  if (self != NULL) {
    self->ob_fval = fval;
  }
  return (PyObject *)self;
}

#define FROM_STRING(ctype, buffer) do {                                \
  /* validate "Number" format, with optional surrounding whitespace    \
   * and optional leading '-':                                         \
   * Number := [0-9]+ ('.' [0-9]*)?                                    \
   *         | '.' [0-9]+                                              \
   */                                                                  \
  const ctype *p = buffer;                                             \
  while (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') p++;     \
  if (*p == '-') p++;                                                  \
  while (*p >= '0' && *p <= '9') p++;                                  \
  if (*p == '.') {                                                     \
    p++;                                                               \
    while (*p >= '0' && *p <= '9') p++;                                \
  }                                                                    \
  /* ignore trailing whitespace */                                     \
  while (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') p++;     \
  /* If we're not at the end of the string, it is not a valid Number,  \
   * otherwise it is a *probable* Number, let Python do the remaining  \
   * validation and conversion. */                                     \
  if (*p || p == buffer) {                                             \
    Py_INCREF(Number_NaN);                                             \
    return Number_NaN;                                                 \
  }                                                                    \
  value = PyNumber_Float(value);                                       \
  if (value == NULL) return NULL;                                      \
  result = _Number_New(PyFloat_AS_DOUBLE(value));                      \
  Py_DECREF(value);                                                    \
  return result;                                                       \
} while(0)

static PyObject *Number_New(PyObject *value)
{
  PyObject *result;

  /* Numeric (XPath and Python) types */
  if (Number_Check(value)) {
    Py_INCREF(value);
    return value;
  }
  if (PyFloat_Check(value)) {
    return _Number_New(PyFloat_AS_DOUBLE(value));
  }
  if (PyInt_Check(value)) {
    long ival = PyInt_AS_LONG(value);
    return _Number_New((double)ival);
  }
  if (PyLong_Check(value)) {
    double d = PyLong_AsDouble(value);
    if (d == -1.0 && PyErr_Occurred()) {
      return NULL;
    }
    return _Number_New(d);
  }

  /* XPath Boolean type */
  if (Boolean_Check(value)) {
    value = (value == Boolean_True) ? Number_One : Number_Zero;
    Py_INCREF(value);
    return value;
  }

  /* String (XPath and Python) types */
  if (PyUnicode_Check(value)) {
    FROM_STRING(Py_UNICODE, PyUnicode_AS_UNICODE(value));
  }
  else if (PyString_Check(value)) {
    FROM_STRING(char, PyString_AS_STRING(value));
  }
  else if (value->ob_type->tp_as_buffer) {
    const char *buffer;
    Py_ssize_t len;
    if (PyObject_AsCharBuffer(value, &buffer, &len)) return NULL;
    /* FIXME: update FROM_STRING() to use `len` instead of assuming 0-term */
    FROM_STRING(char, buffer);
  }

  /* XPath NodeSet type */
  if (NodeSet_Check(value)) {
    if (PyList_GET_SIZE(value) == 0) {
      Py_INCREF(Number_NaN);
      return Number_NaN;
    }
    value = PyList_GET_ITEM(value, 0);
  }
  if (Node_Check(value)) {
    value = node_to_string(value);
    if (value == NULL) return NULL;
    result = Number_New(value);
    Py_DECREF(value);
    return result;
  }

  value = PyNumber_Float(value);
  if (value == NULL) return NULL;

  /* Inline float_subtype_new() */
  assert(PyFloat_Check(value));
  result = _Number_New(PyFloat_AS_DOUBLE(value));
  Py_DECREF(value);
  return result;
}

static PyObject *Boolean_New(PyObject *value)
{
  int nonzero;

  if (Boolean_Check(value)) {
    Py_INCREF(value);
    return value;
  }

  if (PyFloat_Check(value)) {
    double dval = PyFloat_AS_DOUBLE(value);
    nonzero = dval != 0.0 && dval == dval;
  } else {
    nonzero = PyObject_IsTrue(value);
  }
  switch (nonzero) {
  case 1:
    Py_INCREF(Boolean_True);
    return Boolean_True;
  case 0:
    Py_INCREF(Boolean_False);
    return Boolean_False;
  default:
    assert(PyErr_Occurred());
    return NULL;
  }
}

/** XPathObject ******************************************************/

static PyObject *object_as_self(PyObject *self, PyObject *noarg)
{
  Py_INCREF(self);
  return self;
}

static PyObject *object_as_string(PyObject *self, PyObject *noarg)
{
  return String_New(self);
}

static PyObject *object_as_number(PyObject *self, PyObject *noarg)
{
  return Number_New(self);
}

static PyObject *object_as_boolean(PyObject *self, PyObject *noarg)
{
  return Boolean_New(self);
}

static PyObject *object_as_nodeset(PyObject *self, PyObject *noarg)
{
  PyErr_SetString(PyExc_TypeError, "cannot convert to node-set");
  return NULL;
}

static PyMethodDef object_methods[] = {
  { "asString", object_as_string, METH_NOARGS, NULL },
  { "asNumber", object_as_number, METH_NOARGS, NULL },
  { "asBoolean", object_as_boolean, METH_NOARGS, NULL },
  { "asNodeSet", object_as_nodeset, METH_NOARGS, NULL },
  { NULL }
};

static long object_hash(PyObject *v)
{
  return v->ob_type->tp_base->tp_hash(v);
}

static PyObject *object_richcompare(PyObject *v, PyObject *w, int op)
{
  PyObject *result;

  if (NodeSet_Check(w)) {
    Py_INCREF(Py_NotImplemented);
    return Py_NotImplemented;
  }

  if (op == Py_EQ || op == Py_NE) {
    if (Boolean_Check(v)) {
      if (!Boolean_Check(w)) {
        if ((w = Boolean_New(w)) == NULL) return NULL;
      } else {
        Py_INCREF(w);
      }
      Py_INCREF(v);
    } else if (Boolean_Check(w)) {
      if (!Boolean_Check(v)) {
        if ((v = Boolean_New(v)) == NULL) return NULL;
      } else {
        Py_INCREF(v);
      }
      Py_INCREF(w);
    } else if (Number_Check(v)) {
      if (!Number_Check(w)) {
        if ((w = Number_New(w)) == NULL) return NULL;
      } else {
        Py_INCREF(w);
      }
      Py_INCREF(v);
    } else if (Number_Check(w)) {
      if (!Number_Check(v)) {
        if ((v = Number_New(v)) == NULL) return NULL;
      } else {
        Py_INCREF(v);
      }
      Py_INCREF(w);
    } else {
      if (!String_Check(v)) {
        if ((v = String_New(v)) == NULL) return NULL;
      } else {
        Py_INCREF(v);
      }
      if (!String_Check(w)) {
        if ((w = String_New(w)) == NULL) return NULL;
      } else {
        Py_INCREF(w);
      }
    }
  } else {
    if (!Number_Check(v)) {
      if ((v = Number_New(v)) == NULL) return NULL;
    } else {
      Py_INCREF(v);
    }
    if (!Number_Check(w)) {
      if ((w = Number_New(w)) == NULL) return NULL;
    } else {
      Py_INCREF(w);
    }
  }
  assert(v->ob_type == w->ob_type);
  if (v->ob_type->tp_base->tp_compare) {
    int cmp = v->ob_type->tp_base->tp_compare(v, w);
    switch (op) {
    case Py_EQ: cmp = (cmp == 0); break;
    case Py_NE: cmp = (cmp != 0); break;
    case Py_LE: cmp = (cmp <= 0); break;
    case Py_GE: cmp = (cmp >= 0); break;
    case Py_LT: cmp = (cmp == -1); break;
    case Py_GT: cmp = (cmp == 1); break;
    }
    result = cmp ? Boolean_True : Boolean_False;
    Py_INCREF(result);
  } else {
    assert(v->ob_type->tp_base->tp_richcompare);
    result = v->ob_type->tp_base->tp_richcompare(v, w, op);
    if (result == Py_True) {
      Py_DECREF(result);
      Py_INCREF(Boolean_True);
      result = Boolean_True;
    } else if (result == Py_False) {
      Py_DECREF(result);
      Py_INCREF(Boolean_False);
      result = Boolean_False;
    }
  }
  Py_DECREF(v);
  Py_DECREF(w);
  return result;
}

static PyTypeObject XPathObject_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".xpathobject",
  /* tp_basicsize      */ sizeof(XPathObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) 0,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) 0,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) 0,
  /* tp_as_mapping     */ (PyMappingMethods *) 0,
  /* tp_hash           */ (hashfunc) object_hash,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) 0,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ (Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE),
  /* tp_doc            */ (char *) 0,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) object_richcompare,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) object_methods,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) 0,
  /* tp_free           */ 0,
};

/** XPathString ******************************************************/

static PyObject *string_repr(PyObject *v)
{
  PyObject *repr = PyUnicode_Type.tp_repr(v);
  if (repr) {
    v = PyString_FromFormat("String(%s)", PyString_AS_STRING(repr));
    Py_DECREF(repr);
    return v;
  }
  return NULL;
}

static PyObject *string_str(PyObject *v)
{
  return  PyUnicode_Type.tp_str(v);
}

static PyMethodDef string_methods[] = {
  { "asString", object_as_self, METH_NOARGS, NULL },
  { NULL }
};

static PyObject *string_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = { "value", NULL };
  PyObject *x = NULL;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O:String", kwlist, &x))
    return NULL;

  if (x == NULL) {
    Py_INCREF(String_Empty);
    return String_Empty;
  }
  return String_New(x);
}

static char string_doc[] = "Represents the XPath String data type.";

static PyTypeObject XPathString_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".string",
  /* tp_basicsize      */ sizeof(XPathStringObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) 0,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) string_repr,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) 0,
  /* tp_as_mapping     */ (PyMappingMethods *) 0,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) string_str,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ Py_TPFLAGS_DEFAULT,
  /* tp_doc            */ (char *) string_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) string_methods,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) string_new,
  /* tp_free           */ 0,
};

#define STATIC_LENGTH(x) ((sizeof(x) / sizeof(Py_UNICODE)) - 1)
#define STATIC_STRING(x) \
  { PyObject_HEAD_INIT(&XPathString_Type) STATIC_LENGTH(x), x, -1 }

static Py_UNICODE unicode_empty[] = { '\0' };
static Py_UNICODE unicode_true[] = { 't', 'r', 'u', 'e', '\0' };
static Py_UNICODE unicode_false[] = { 'f', 'a', 'l', 's', 'e', '\0' };

static PyUnicodeObject _String_Constants[] = {
  STATIC_STRING(unicode_empty), /* String_Empty */
  STATIC_STRING(unicode_false), /* String_False */
  STATIC_STRING(unicode_true),  /* String_True */
};


/** XPathNumber ******************************************************/

static void number_dealloc(PyObject *v)
{
  v->ob_type->tp_free(v);
}

Py_LOCAL_INLINE(void)
format_number(char *buf, size_t size, PyObject *v, int flags)
{
  if (v == Number_NaN)
    strncpy(buf, "Number.NaN", size);
  else if (v == Number_PosInf)
    strncpy(buf, "Number.POSITIVE_INFINITY", size);
  else if (v == Number_NegInf)
    strncpy(buf, "Number.NEGATIVE_INFINITY", size);
  else if (flags & Py_PRINT_RAW)
    PyOS_snprintf(buf, size, "%0.12g", PyFloat_AS_DOUBLE(v));
  else
    PyOS_snprintf(buf, size, "Number(%0.12g)", PyFloat_AS_DOUBLE(v));
}

static int number_print(PyObject *v, FILE *fp, int flags)
{
  char buf[100];
  format_number(buf, sizeof(buf), v, flags);
  Py_BEGIN_ALLOW_THREADS
  fputs(buf, fp);
  Py_END_ALLOW_THREADS
  return 0;
}

static PyObject *number_repr(PyObject *v)
{
  char buf[100];
  format_number(buf, sizeof(buf), v, 0);
  return PyString_FromString(buf);
}

static PyObject *number_str(PyObject *v)
{
  char buf[100];
  format_number(buf, sizeof(buf), v, Py_PRINT_RAW);
  return PyString_FromString(buf);
}

static PyObject *handle_fpe(PyObject *v)
{
  assert(PyErr_Occurred());
  if (PyErr_ExceptionMatches(PyExc_ZeroDivisionError)) {
    double dval;
    PyErr_Clear();
    if (PyFloat_Check(v)) {
      dval = PyFloat_AS_DOUBLE(v);
    } else if (PyInt_Check(v)) {
      dval = (double) PyInt_AS_LONG(v);
    } else if (PyLong_Check(v)) {
      dval = PyLong_AsDouble(v);
    } else {
      dval = 0.0;
    }
    if (dval < 0.0) {
      Py_INCREF(Number_NegInf);
      return Number_NegInf;
    } else if (dval > 0.0) {
      Py_INCREF(Number_PosInf);
      return Number_PosInf;
    } else {
      Py_INCREF(Number_NaN);
      return Number_NaN;
    }
  }
  return NULL;
}

static PyObject *number_add(PyObject *v, PyObject *w)
{
  PyObject *result = PyFloat_Type.tp_as_number->nb_add(v, w);
  if (result && PyFloat_Check(result)) {
    v = _Number_New(PyFloat_AS_DOUBLE(result));
    Py_DECREF(result);
    return v;
  }
  return result;
}

static PyObject *number_sub(PyObject *v, PyObject *w)
{
  PyObject *result = PyFloat_Type.tp_as_number->nb_subtract(v, w);
  if (result && PyFloat_Check(result)) {
    v = _Number_New(PyFloat_AS_DOUBLE(result));
    Py_DECREF(result);
    return v;
  }
  return result;
}

static PyObject *number_mul(PyObject *v, PyObject *w)
{
  PyObject *result = PyFloat_Type.tp_as_number->nb_multiply(v, w);
  if (result && PyFloat_Check(result)) {
    v = _Number_New(PyFloat_AS_DOUBLE(result));
    Py_DECREF(result);
    return v;
  }
  return result;
}

static PyObject *number_classic_div(PyObject *v, PyObject *w)
{
  PyObject *result = PyFloat_Type.tp_as_number->nb_divide(v, w);
  if (result == NULL) {
    result = handle_fpe(v);
  } else if (PyFloat_Check(result)) {
    v = _Number_New(PyFloat_AS_DOUBLE(result));
    Py_DECREF(result);
    return v;
  }
  return result;
}

static PyObject *number_rem(PyObject *v, PyObject *w)
{
  PyObject *result = PyFloat_Type.tp_as_number->nb_remainder(v, w);
  if (result == NULL) {
    if (PyErr_ExceptionMatches(PyExc_ZeroDivisionError)) {
      PyErr_Clear();
      Py_INCREF(Number_NaN);
      return Number_NaN;
    }
  } else if (PyFloat_Check(result)) {
    v = _Number_New(PyFloat_AS_DOUBLE(result));
    Py_DECREF(result);
    return v;
  }
  return result;
}

static PyObject *number_divmod(PyObject *v, PyObject *w)
{
  PyObject *result = PyFloat_Type.tp_as_number->nb_divmod(v, w);
  if (result == NULL) {
    if ((result = handle_fpe(v))) {
      result = Py_BuildValue("(NO)", result, Number_NaN);
    }
  } else {
    assert(PyTuple_CheckExact(result));
    v = PyTuple_GET_ITEM(result, 0);
    w = _Number_New(PyFloat_AS_DOUBLE(v));
    if (w == NULL) {
      Py_DECREF(result);
      return NULL;
    }
    PyTuple_SET_ITEM(result, 0, w);
    Py_DECREF(v);
    v = PyTuple_GET_ITEM(result, 1);
    w = _Number_New(PyFloat_AS_DOUBLE(v));
    if (w == NULL) {
      Py_DECREF(result);
      return NULL;
    }
    PyTuple_SET_ITEM(result, 1, w);
    Py_DECREF(v);
  }
  return result;
}

static PyObject *number_pow(PyObject *v, PyObject *w, PyObject *z)
{
  PyObject *result = PyFloat_Type.tp_as_number->nb_power(v, w, z);
  if (result == NULL) {
    /* 0.0 raised to a negative power; same as 1/0.0**(-w) */
    if (PyErr_ExceptionMatches(PyExc_ZeroDivisionError)) {
      PyErr_Clear();
      Py_INCREF(Number_PosInf);
      return Number_PosInf;
    }
  } else if (PyFloat_Check(result)) {
    v = _Number_New(PyFloat_AS_DOUBLE(result));
    Py_DECREF(result);
    return v;
  }
  return result;
}

static PyObject *number_neg(PyObject *v)
{
  double dval = PyFloat_AS_DOUBLE(v);
  if (dval == 0.0) {
    if (v == Number_NegZero) {
      Py_INCREF(Number_Zero);
      return Number_Zero;
    } else {
      Py_INCREF(Number_NegZero);
      return Number_NegZero;
    }
  }
  return _Number_New(-dval);
}

static PyObject *number_pos(PyObject *v)
{
  if (Number_Check(v)) {
    Py_INCREF(v);
    return v;
  }
  return _Number_New(PyFloat_AS_DOUBLE(v));
}

static PyObject *number_abs(PyObject *v)
{
  return _Number_New(fabs(PyFloat_AS_DOUBLE(v)));
}

static int number_nonzero(PyObject *v)
{
  double fval = PyFloat_AS_DOUBLE(v);
  return fval != 0.0 && fval == fval;
}

static int number_coerce(PyObject **pv, PyObject **pw)
{
  if (PyInt_Check(*pw)) {
    long x = PyInt_AS_LONG(*pw);
    *pw = _Number_New((double) x);
    Py_INCREF(*pv);
    return 0;
  }
  if (PyLong_Check(*pw)) {
    double x = PyLong_AsDouble(*pw);
    if (x == -1.0 && PyErr_Occurred()) return -1;
    *pw = _Number_New(x);
    Py_INCREF(*pv);
    return 0;
  }
  if (PyFloat_Check(*pw)) {
    *pw = _Number_New(PyFloat_AS_DOUBLE(*pw));
    Py_INCREF(*pv);
    return 0;
  }
  if (Number_Check(*pw)) {
    Py_INCREF(*pw);
    Py_INCREF(*pv);
    return 0;
  }
  return 1;
}

static PyObject *number_floor_div(PyObject *v, PyObject *w)
{
  PyObject *t, *r;

  t = number_divmod(v, w);
  if (t == NULL || t == Py_NotImplemented)
    return t;
  assert(PyTuple_CheckExact(t));
  r = PyTuple_GET_ITEM(t, 0);
  Py_INCREF(r);
  Py_DECREF(t);
  return r;
}

static PyObject *number_div(PyObject *v, PyObject *w)
{
  PyObject *result = PyFloat_Type.tp_as_number->nb_true_divide(v, w);
  if (result == NULL) {
    result = handle_fpe(v);
  } else if (PyFloat_Check(result)) {
    v = _Number_New(PyFloat_AS_DOUBLE(result));
    Py_DECREF(result);
    return v;
  }
  return result;
}

static PyNumberMethods number_as_number = {
  /* nb_add                  */ number_add,
  /* nb_subtract             */ number_sub,
  /* nb_multiply             */ number_mul,
  /* nb_divide               */ number_classic_div,
  /* nb_remainder            */ number_rem,
  /* nb_divmod               */ number_divmod,
  /* nb_power                */ number_pow,
  /* nb_negative             */ number_neg,
  /* nb_positive             */ number_pos,
  /* nb_absolute             */ number_abs,
  /* nb_nonzero              */ number_nonzero,
  /* nb_invert               */ 0,
  /* nb_lshift               */ 0,
  /* nb_rshift               */ 0,
  /* nb_and                  */ 0,
  /* nb_xor                  */ 0,
  /* nb_or                   */ 0,
  /* nb_coerce               */ number_coerce,
  /* nb_int                  */ 0,
  /* nb_long                 */ 0,
  /* nb_float                */ 0,
  /* nb_oct                  */ 0,
  /* nb_hex                  */ 0,
  /* nb_inplace_add          */ 0,
  /* nb_inplace_subtract     */ 0,
  /* nb_inplace_multiply     */ 0,
  /* nb_inplace_divide       */ 0,
  /* nb_inplace_remainder    */ 0,
  /* nb_inplace_power        */ 0,
  /* nb_inplace_lshift       */ 0,
  /* nb_inplace_rshift       */ 0,
  /* nb_inplace_and          */ 0,
  /* nb_inplace_xor          */ 0,
  /* nb_inplace_or           */ 0,
  /* nb_floor_divide         */ number_floor_div,
  /* nb_true_divide          */ number_div,
  /* nb_inplace_floor_divide */ 0,
  /* nb_inplace_true_divide  */ 0,
};

static PyObject *number_richcompare(PyObject *v, PyObject *w, int op)
{
  assert(Number_Check(v));
  if (PyInt_CheckExact(w) || PyLong_CheckExact(w) || PyFloat_CheckExact(w))
    return PyFloat_Type.tp_richcompare(v, w, op);
  return object_richcompare(v, w, op);
}

static PyObject *number_isfinite(PyObject *self, PyObject *noarg)
{
  PyObject *result = isfinite(PyFloat_AS_DOUBLE(self)) ? Py_True : Py_False;
  Py_INCREF(result);
  return result;
}

static PyObject *number_isnormal(PyObject *self, PyObject *noarg)
{
  double dval = PyFloat_AS_DOUBLE(self);
  PyObject *result = (isfinite(dval) && dval != 0.0) ? Py_True : Py_False;
  Py_INCREF(result);
  return result;
}

static PyObject *number_isinf(PyObject *self, PyObject *noarg)
{
  PyObject *result = isinf(PyFloat_AS_DOUBLE(self)) ? Py_True : Py_False;
  Py_INCREF(result);
  return result;
}

static PyObject *number_isnan(PyObject *self, PyObject *noarg)
{
  PyObject *result = isnan(PyFloat_AS_DOUBLE(self)) ? Py_True : Py_False;
  Py_INCREF(result);
  return result;
}

static PyMethodDef number_methods[] = {
  { "asNumber", object_as_self, METH_NOARGS, NULL },
  /* number-specific methods */
  { "isfinite", number_isfinite, METH_NOARGS, NULL },
  { "isnormal", number_isnormal, METH_NOARGS, NULL },
  { "isinf", number_isinf, METH_NOARGS, NULL },
  { "isnan", number_isnan, METH_NOARGS, NULL },
  { NULL }
};

static PyObject *number_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = { "value", NULL };
  PyObject *x = NULL;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O:Number", kwlist, &x))
    return NULL;

  if (x == NULL) {
    Py_INCREF(Number_Zero);
    return Number_Zero;
  }
  return Number_New(x);
}

static char number_doc[] = "Represents the XPath Number data type.";

static PyTypeObject XPathNumber_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".number",
  /* tp_basicsize      */ sizeof(XPathNumberObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) number_dealloc,
  /* tp_print          */ (printfunc) number_print,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) number_repr,
  /* tp_as_number      */ (PyNumberMethods *) &number_as_number,
  /* tp_as_sequence    */ (PySequenceMethods *) 0,
  /* tp_as_mapping     */ (PyMappingMethods *) 0,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) number_str,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ Py_TPFLAGS_DEFAULT,
  /* tp_doc            */ (char *) number_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) number_richcompare,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) number_methods,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) number_new,
  /* tp_free           */ 0,
};

/* These values will be fixed up later, regardless of compiler support. */
#ifndef NAN
#define NAN (Py_HUGE_VAL - Py_HUGE_VAL)
#endif
#ifndef INFINITY
#define INFINITY Py_HUGE_VAL
#endif
#define STATIC_NUMBER(v) \
  { PyObject_HEAD_INIT(&XPathNumber_Type) v }
static PyFloatObject _Number_Constants[] = {
  STATIC_NUMBER(1.0), /* Number_One */
  STATIC_NUMBER(0.0), /* Number_Zero */
  STATIC_NUMBER(-0.0), /* Number_NegZero */
  STATIC_NUMBER(0.0), /* Number_NaN */
  STATIC_NUMBER(0.0), /* Number_NegInf */
  STATIC_NUMBER(0.0), /* Number_PosInf */
};

/** XPathBoolean *****************************************************/

Py_LOCAL_INLINE(char *)
format_boolean(PyObject *v, int flags)
{
  if (PyInt_AS_LONG(v)) {
    return (flags & Py_PRINT_RAW) ? "True" : "boolean.TRUE";
  } else {
    return (flags & Py_PRINT_RAW) ? "False" : "boolean.FALSE";
  }
}

static int boolean_print(PyObject *self, FILE *fp, int flags)
{
  char *str = format_boolean(self, flags);
  Py_BEGIN_ALLOW_THREADS
  fputs(str, fp);
  Py_END_ALLOW_THREADS
  return 0;
}

static PyObject *boolean_repr(PyObject *self)
{
  return PyString_FromString(format_boolean(self, 0));
}

static PyObject *boolean_str(PyObject *self)
{
  return PyString_FromString(format_boolean(self, Py_PRINT_RAW));
}

/* Arithmetic methods -- only so we can override &, |, ^. */

static PyObject *boolean_and(PyObject *a, PyObject *b)
{
  PyObject *result;
  if (!Boolean_Check(a) || !Boolean_Check(b))
    return PyInt_Type.tp_as_number->nb_and(a, b);
  result = PyInt_AS_LONG(a) & PyInt_AS_LONG(b) ? Boolean_True : Boolean_False;
  Py_INCREF(result);
  return result;
}

static PyObject *boolean_or(PyObject *a, PyObject *b)
{
  PyObject *result;
  if (!Boolean_Check(a) || !Boolean_Check(b))
    return PyInt_Type.tp_as_number->nb_or(a, b);
  result = PyInt_AS_LONG(a) | PyInt_AS_LONG(b) ? Boolean_True : Boolean_False;
  Py_INCREF(result);
  return result;
}

static PyObject *boolean_xor(PyObject *a, PyObject *b)
{
  PyObject *result;
  if (!Boolean_Check(a) || !Boolean_Check(b))
    return PyInt_Type.tp_as_number->nb_xor(a, b);
  result = PyInt_AS_LONG(a) ^ PyInt_AS_LONG(b) ? Boolean_True : Boolean_False;
  Py_INCREF(result);
  return result;
}

static PyNumberMethods boolean_as_number = {
  /* nb_add */ 0,
  /* nb_subtract */ 0,
  /* nb_multiply */ 0,
  /* nb_divide */ 0,
  /* nb_remainder */ 0,
  /* nb_divmod */ 0,
  /* nb_power */ 0,
  /* nb_negative */ 0,
  /* nb_positive */ 0,
  /* nb_absolute */ 0,
  /* nb_nonzero */ 0,
  /* nb_invert */ 0,
  /* nb_lshift */ 0,
  /* nb_rshift */ 0,
  /* nb_and */ boolean_and,
  /* nb_xor */ boolean_xor,
  /* nb_or */ boolean_or,
  /* nb_coerce */ 0,
  /* nb_int */ 0,
  /* nb_long */ 0,
  /* nb_float */ 0,
  /* nb_oct */ 0,
  /* nb_hex */ 0,
  /* nb_inplace_add */ 0,
  /* nb_inplace_subtract */ 0,
  /* nb_inplace_multiply */ 0,
  /* nb_inplace_divide */ 0,
  /* nb_inplace_remainder */ 0,
  /* nb_inplace_power */ 0,
  /* nb_inplace_lshift */ 0,
  /* nb_inplace_rshift */ 0,
  /* nb_inplace_and */ 0,
  /* nb_inplace_xor */ 0,
  /* nb_inplace_or */ 0,
  /* nb_floor_divide */ 0,
  /* nb_true_divide */ 0,
  /* nb_inplace_floor_divide */ 0,
  /* nb_inplace_true_divide */ 0,
};

/* Python methods */

static PyMethodDef boolean_methods[] = {
  { "asBoolean", object_as_self, METH_NOARGS, NULL },
  { NULL }
};

static PyObject *boolean_new(PyTypeObject *type, PyObject *args,
                             PyObject *kwds)
{
  static char *kwlist[] = { "value", NULL };
  PyObject *x = NULL;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O:Boolean", kwlist, &x))
    return NULL;

  if (x == NULL) {
    Py_INCREF(Boolean_False);
    return Boolean_False;
  }
  return Boolean_New(x);
}

static char boolean_doc[] = "Represents the XPath Boolean data type.";

static PyTypeObject XPathBoolean_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".boolean",
  /* tp_basicsize      */ sizeof(XPathBooleanObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) 0,
  /* tp_print          */ (printfunc) boolean_print,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) boolean_repr,
  /* tp_as_number      */ (PyNumberMethods *) &boolean_as_number,
  /* tp_as_sequence    */ (PySequenceMethods *) 0,
  /* tp_as_mapping     */ (PyMappingMethods *) 0,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) boolean_str,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES,
  /* tp_doc            */ (char *) boolean_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) boolean_methods,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) 0,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) boolean_new,
  /* tp_free           */ 0,
};

static PyIntObject _Boolean_Constants[] = {
  { PyObject_HEAD_INIT(&XPathBoolean_Type) 0 }, /* Boolean_False */
  { PyObject_HEAD_INIT(&XPathBoolean_Type) 1 }, /* Boolean_True */
};

/** node-set type ****************************************************/

static char nodeset_doc[] = "Represents the XPath node-set data type.";

static PyObject *NodeSet_New(Py_ssize_t size)
{
  PyObject *op = PyList_New(size);
  if (op) {
    /* Swap `PyList_Type` for `XPathNodeSet_Type` */
    _Py_ForgetReference(op);
    PyObject_INIT(op, &XPathNodeSet_Type);
  }
  return op;
}

static PyObject *nodeset_new(PyTypeObject *type, PyObject *args,
                             PyObject *kwds)
{
  static char *kwlist[] = { "sequence", NULL };
  PyObject *arg = NULL;
  PyObject *self;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O:nodeset", kwlist, &arg))
    return NULL;

  if (arg) {
    if (NodeSet_Check(arg)) {
      Py_INCREF(arg);
      return arg;
    }
    if (Node_Check(arg)) {
      PyErr_Format(PyExc_TypeError, "cannot convert '%s' object to nodeset",
                   arg->ob_type->tp_name);
      return NULL;
    }
  }

  self = type->tp_alloc(type, 0);
  if (self != NULL) {
    if (PyList_Type.tp_init(self, args, kwds) < 0 ||
        PyList_Sort(self) < 0) {
      Py_DECREF(self);
      self = NULL;
    }
  }
  return self;
}

static int nodeset_init(PyObject *self, PyObject *args, PyObject *kwds)
{
  /* Prevent list.__init__ from creating a copy of the input. */
  return 0;
}

/* Both `tp_print` and `tp_repr` need to be defined because `PyList_Type`
 * has them defined. */
static int nodeset_print(PyObject *self, FILE *fp, int flags)
{
  int rc;
  fputs("nodeset(", fp);
  rc = PyList_Type.tp_print(self, fp, flags);
  if (rc != 0) return rc;
  fputs(")", fp);
  return 0;
}

static PyObject *nodeset_repr(PyObject *self)
{
  PyObject *repr;
  if (PyList_GET_SIZE(self) == 0) {
    repr = PyString_FromString("nodeset()");
  } else {
    repr = PyString_FromString("nodeset(");
    if (repr) {
      PyObject *tmp = PyList_Type.tp_repr(self);
      if (tmp == NULL) {
        Py_DECREF(repr);
        return NULL;
      }
      PyString_ConcatAndDel(&repr, tmp);
      tmp = PyString_FromString(")");
      if (tmp == NULL) {
        Py_DECREF(repr);
        return NULL;
      }
      PyString_ConcatAndDel(&repr, tmp);
    }
  }
  return repr;
}

static PyObject *nodeset_richcompare(PyObject *v, PyObject *w, int op)
{
  Py_ssize_t i, lhs_size = PyList_GET_SIZE(v);
  PyObject *a, *b, *result;

  /* From XPath 1.0 Section 3.4:
   * If both objects to be compared are node-sets, then the comparison
   * will be true if and only if there is a node in the first node-set
   * and a node in the second node-set such that the result of
   * performing the comparison on the string-values of the two nodes
   * is true. */
  if (NodeSet_Check(w)) {
    Py_ssize_t j, rhs_size = PyList_GET_SIZE(w);
    PyObject *rhs;
    /* One of the two node-sets is empty.  In this case, according to
     * section 3.4 of the XPath rec, no node exists in one of the two
     * sets to compare, so *any* comparison must be false. */
    if (lhs_size == 0 || rhs_size == 0) {
      Py_INCREF(Boolean_False);
      return Boolean_False;
    }
    /* If it is a relational comparison, the actual comparison is
     * done on the string value of each of the nodes. This means
     * that the values are then converted to numbers for comparison. */
    if (op == Py_EQ) {
      /* Check for a node in `w` that has the same string value as a
       * node in `v`. */
      rhs = PyDict_New();
      if (rhs == NULL) return NULL;
      for (j = 0; j < rhs_size; j++) {
        b = String_New(PyList_GET_ITEM(w, j));
        if (b == NULL) {
          Py_DECREF(rhs);
          return NULL;
        }
        if (PyDict_SetItem(rhs, b, Py_True) < 0) {
          Py_DECREF(b);
          Py_DECREF(rhs);
          return NULL;
        }
      }
      for (i = 0; i < lhs_size; i++) {
        a = String_New(PyList_GET_ITEM(v, i));
        if (a == NULL) {
          Py_DECREF(rhs);
          return NULL;
        }
        if (PyDict_GetItem(rhs, a)) {
          Py_DECREF(a);
          Py_DECREF(rhs);
          Py_INCREF(Boolean_True);
          return Boolean_True;
        }
        Py_DECREF(a);
      }
      Py_DECREF(rhs);
    } else if (op == Py_NE) {
      /* Check for a node in `w` that has a different string value as a
       * node in `v`. */
      for (i = 0; i < lhs_size; i++) {
        a = String_New(PyList_GET_ITEM(v, i));
        if (a == NULL) return NULL;
        for (j = 0; j < rhs_size; j++) {
          b = String_New(PyList_GET_ITEM(w, j));
          if (b == NULL) {
            Py_DECREF(a);
            return NULL;
          }
          result = object_richcompare(a, b, Py_NE);
          if (result != Boolean_False) {
            assert(result == NULL || result == Boolean_True);
            Py_DECREF(a);
            Py_DECREF(b);
            return result;
          }
          Py_DECREF(b);
        }
        Py_DECREF(a);
      }
    } else {
      rhs = PyTuple_New(rhs_size);
      if (rhs == NULL) return NULL;
      for (i = 0; i < lhs_size; i++) {
        a = Number_New(PyList_GET_ITEM(v, i));
        if (a == NULL) {
          Py_DECREF(rhs);
          return NULL;
        }
        for (j = 0; j < rhs_size; j++) {
          b = PyTuple_GET_ITEM(rhs, i);
          if (b == NULL) {
            b = Number_New(PyList_GET_ITEM(w, i));
            if (b == NULL) {
              Py_DECREF(a);
              Py_DECREF(rhs);
              return NULL;
            }
            /* `rhs` now owns the reference */
            PyTuple_SET_ITEM(rhs, i, b);
          }
          result = object_richcompare(a, b, op);
          if (result != Boolean_False) {
            assert(result == NULL || result == Boolean_True);
            Py_DECREF(a);
            Py_DECREF(rhs);
            return result;
          }
        }
        Py_DECREF(a);
      }
      Py_DECREF(rhs);
    }
    Py_INCREF(Boolean_False);
    return Boolean_False;
  }
  else if (Boolean_Check(w)) {
    v = lhs_size ? Boolean_True : Boolean_False;
    return object_richcompare(v, w, op);
  }
  else if (Number_Check(w) || op < Py_EQ || op > Py_NE) {
    if (lhs_size) {
      if (Number_Check(w)) {
        Py_INCREF(w);
      } else {
        if ((w = Number_New(w)) == NULL) return NULL;
      }
      for (i = 0; i < lhs_size; i++) {
        a = Number_New(PyList_GET_ITEM(v, i));
        if (a == NULL) {
          Py_DECREF(w);
          return NULL;
        }
        result = object_richcompare(a, w, op);
        Py_DECREF(a);
        if (result == NULL || result == Boolean_True) {
          Py_DECREF(w);
          return result;
        }
      }
      Py_DECREF(w);
    }
    Py_INCREF(Boolean_False);
    return Boolean_False;
  }
  else {
    if (lhs_size) {
      if (String_Check(w)) {
        Py_INCREF(w);
      } else {
        if ((w = String_New(w)) == NULL) return NULL;
      }
      for (i = 0; i < lhs_size; i++) {
        a = String_New(PyList_GET_ITEM(v, i));
        if (a == NULL) {
          Py_DECREF(w);
          return NULL;
        }
        result = object_richcompare(a, w, op);
        Py_DECREF(a);
        if (result == NULL || result == Boolean_True) {
          Py_DECREF(w);
          return result;
        }
      }
      Py_DECREF(w);
    }
    Py_INCREF(Boolean_False);
    return Boolean_False;
  }
}

static PyObject *
nodeset_concat(PyObject *a, PyObject *b)
{
  XPathNodeSetObject *self=(XPathNodeSetObject *)a;
  XPathNodeSetObject *other=(XPathNodeSetObject *)b;
  XPathNodeSetObject *np;
  Py_ssize_t size, i;
  PyObject **src, **dst, *item;
  if (!NodeSet_Check(b)) {
    PyErr_Format(PyExc_TypeError,
                 "can only concatenate nodeset (not %s) to nodeset",
                 b == Py_None ? "None" : b->ob_type->tp_name);
    return NULL;
  }
  size = self->ob_size + other->ob_size;
  if (size < 0)
    return PyErr_NoMemory();
  np = (XPathNodeSetObject *)NodeSet_New(size);
  if (np == NULL)
    return NULL;
  src = self->ob_item;
  dst = np->ob_item;
  for (i = 0; i < self->ob_size; i++) {
    item = src[i];
    Py_INCREF(item);
    dst[i] = item;
  }
  src = other->ob_item;
  dst += i;
  for (i = 0; i < other->ob_size; i++) {
    item = src[i];
    Py_INCREF(item);
    dst[i] = item;
  }
  return (PyObject *)np;
}

static PyObject *
nodeset_repeat(PyObject *a, Py_ssize_t n)
{
  XPathNodeSetObject *self=(XPathNodeSetObject *)a;
  XPathNodeSetObject *np;
  Py_ssize_t size, i, j;
  PyObject **src, **dst;
  if (n < 0)
    n = 0;
  size = self->ob_size * n;
  if (n && size/n != self->ob_size)
    return PyErr_NoMemory();
  if (size == 0)
    return NodeSet_New(0);
  np = (XPathNodeSetObject *)NodeSet_New(size);
  if (np == NULL)
    return NULL;
  src = self->ob_item;
  dst = np->ob_item;
  if (self->ob_size == 1) {
    PyObject *item = src[0];
    for (i = 0; i < n; i++) {
      dst[i] = item;
      Py_INCREF(item);
    }
  } else {
    for (i = 0; i < n; i++) {
      for (j = 0; j < self->ob_size; j++) {
        *dst = src[j];
        Py_INCREF(*dst);
        dst++;
      }
    }
  }
  return (PyObject *)np;
}

static PyObject *
nodeset_slice(PyObject *op, Py_ssize_t ilow, Py_ssize_t ihigh)
{
  XPathNodeSetObject *self=(XPathNodeSetObject *)op;
  XPathNodeSetObject *np;
  PyObject **src, **dest, *item;
  Py_ssize_t i, len;

  if (ilow < 0)
    ilow = 0;
  else if (ilow > self->ob_size)
    ilow = self->ob_size;
  if (ihigh < ilow)
    ihigh = ilow;
  else if (ihigh > self->ob_size)
    ihigh = self->ob_size;
  len = ihigh - ilow;
  np = (XPathNodeSetObject *)NodeSet_New(len);
  if (np == NULL)
    return NULL;
  src = self->ob_item + ilow;
  dest = np->ob_item;
  for (i = 0; i < len; i++) {
    item = src[i];
    Py_INCREF(item);
    dest[i] = item;
  }
  return (PyObject *)np;
}

static PySequenceMethods nodeset_as_sequence = {
  /* sq_length         */ (lenfunc) 0,
  /* sq_concat         */ (binaryfunc) nodeset_concat,
  /* sq_repeat         */ (ssizeargfunc) nodeset_repeat,
  /* sq_item           */ (ssizeargfunc) 0,
  /* sq_slice          */ (ssizessizeargfunc) nodeset_slice,
  /* sq_ass_item       */ (ssizeobjargproc) 0,
  /* sq_ass_slice      */ (ssizessizeobjargproc) 0,
  /* sq_contains       */ (objobjproc) 0,
  /* sq_inplace_concat */ (binaryfunc) 0,
  /* sq_inplace_repeat */ (ssizeargfunc) 0,
};

static PyObject *
nodeset_subscript(PyObject *op, PyObject *item)
{
  XPathNodeSetObject *self=(XPathNodeSetObject *)op;

  if (PySlice_Check(item)) {
    Py_ssize_t start, stop, step, slicelength, cur, i;
    PyObject *result, **src, **dest;

    if (PySlice_GetIndicesEx((PySliceObject*)item, self->ob_size,
                             &start, &stop, &step, &slicelength) < 0)
      return NULL;

    if (slicelength <= 0)
      return NodeSet_New(0);

    result = NodeSet_New(slicelength);
    if (result) {
      src = self->ob_item;
      dest = ((XPathNodeSetObject *)result)->ob_item;
      for (cur = start, i = 0; i < slicelength; cur += step, i++) {
        item = src[cur];
        Py_INCREF(item);
        dest[i] = item;
      }
    }
    return result;
  } else {
    return PyList_Type.tp_as_mapping->mp_subscript(op, item);
  }
}

static PyMappingMethods nodeset_as_mapping = {
  /* mp_length        */ (lenfunc) 0,
  /* mp_subscript     */ (binaryfunc) nodeset_subscript,
  /* mp_ass_subscript */ (objobjargproc) 0,
};

static PyMethodDef nodeset_methods[] = {
  { NULL }
};

static PyTypeObject XPathNodeSet_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ MODULE_NAME ".nodeset",
  /* tp_basicsize      */ sizeof(XPathNodeSetObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) 0,
  /* tp_print          */ (printfunc) nodeset_print,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) nodeset_repr,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) &nodeset_as_sequence,
  /* tp_as_mapping     */ (PyMappingMethods *) &nodeset_as_mapping,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) nodeset_repr,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ Py_TPFLAGS_DEFAULT,
  /* tp_doc            */ (char *) nodeset_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) nodeset_richcompare,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) nodeset_methods,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) 0,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) nodeset_init,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) nodeset_new,
  /* tp_free           */ 0,
};

/** Module Initialization ********************************************/

static PyMethodDef module_methods[] = {
  { NULL }
};

static int add_type(PyObject *module, PyTypeObject *type, PyTypeObject *base)
{
  const char *name = type->tp_name + sizeof(MODULE_NAME);
  assert(strncmp(type->tp_name, MODULE_NAME, sizeof(MODULE_NAME)-1) == 0);
  type->tp_base = base;
  if (base) {
    type->tp_bases = Py_BuildValue("OO", &XPathObject_Type, base);
    if (type->tp_bases == NULL) return -1;
  }
  if (PyType_Ready(type) < 0) return -1;
  Py_INCREF(type);
  return PyModule_AddObject(module, name, (PyObject *)type);
}


PyMODINIT_FUNC MODULE_INITFUNC(void) {
  PyObject *module, *dict;

  module = Py_InitModule3(MODULE_NAME, module_methods, module_doc);
  if (module == NULL) return;

  Domlette_IMPORT;

  if (add_type(module, &XPathObject_Type, NULL) < 0) return;

  if (add_type(module, &XPathString_Type, &PyUnicode_Type) < 0) return;
  String_Empty = (PyObject *) &_String_Constants[0];
  String_False = (PyObject *) &_String_Constants[1];
  String_True = (PyObject *) &_String_Constants[2];
  dict = XPathString_Type.tp_dict;
  if (PyDict_SetItemString(dict, "EMPTY", String_Empty)) return;

  XPathNumber_Type.tp_hash = PyFloat_Type.tp_hash;
  if (add_type(module, &XPathNumber_Type, &PyFloat_Type) < 0) return;
  Number_One = (PyObject *) &_Number_Constants[0];
  Number_Zero = (PyObject *) &_Number_Constants[1];
  Number_NegZero = (PyObject *) &_Number_Constants[2];
  Number_NaN = (PyObject *) &_Number_Constants[3];
  Number_NegInf = (PyObject *) &_Number_Constants[4];
  Number_PosInf = (PyObject *) &_Number_Constants[5];
  /* Ensure the "specials" do indeed have their correct IEEE 754 values. */
  PyFloat_AS_DOUBLE(Number_PosInf) = INFINITY;
  PyFloat_AS_DOUBLE(Number_PosInf) += PyFloat_AS_DOUBLE(Number_PosInf);
  PyFloat_AS_DOUBLE(Number_NegInf) = -INFINITY;
  PyFloat_AS_DOUBLE(Number_NegInf) += PyFloat_AS_DOUBLE(Number_NegInf);
  PyFloat_AS_DOUBLE(Number_NaN) = (PyFloat_AS_DOUBLE(Number_PosInf) +
                                   PyFloat_AS_DOUBLE(Number_NegInf));
  dict = XPathNumber_Type.tp_dict;
  if (PyDict_SetItemString(dict, "NaN", Number_NaN)) return;
  if (PyDict_SetItemString(dict, "POSITIVE_INFINITY", Number_PosInf)) return;
  if (PyDict_SetItemString(dict, "NEGATIVE_INFINITY", Number_NegInf)) return;

  if (add_type(module, &XPathBoolean_Type, &PyInt_Type) < 0) return;
  Boolean_False = (PyObject *) &_Boolean_Constants[0];
  Boolean_True = (PyObject *) &_Boolean_Constants[1];
  dict = XPathBoolean_Type.tp_dict;
  if (PyDict_SetItemString(dict, "FALSE", Boolean_False)) return;
  if (PyDict_SetItemString(dict, "TRUE", Boolean_True)) return;

  if (add_type(module, &XPathNodeSet_Type, &PyList_Type) < 0) return;
}
