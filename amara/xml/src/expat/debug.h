#ifndef EXPAT_DEBUG_H
#define EXPAT_DEBUG_H

#ifdef __cplusplus
extern "C" {
#endif

/* Use these defines to control different aspects of debugging */

/* Debug/trace the ExpatReader calls */
/*#define DEBUG_READER */

/* Debug/trace Expat callbacks */
/*#define DEBUG_CALLBACKS */

/* Debug/trace ExpatFilter routines */
/*#define DEBUG_FILTER */

/* Debug the state table routines */
/*#define DEBUG_STATE_TABLE */

/* Debug DTD validation routines */
/*#define DEBUG_VALIDATION */

/* Debug the memory (de)allocations */
/*#define DEBUG_MEMORY */

/* Enable all debugging flags */
#define DEBUG_ALL */

#ifdef DEBUG_ALL
#define DEBUG_READER
#define DEBUG_CALLBACKS
#define DEBUG_FILTER
#define DEBUG_STATE_TABLE
#define DEBUG_VALIDATION
#define DEBUG_MEMORY
#endif

#if defined(Py_DEBUG) || defined(DEBUG_MEMORY)
#define PyType_CLEAR(op)                                          \
  do {                                                            \
    PyObject_ClearWeakRefs((PyObject *)(op));                     \
    Py_XDECREF(((PyTypeObject *)(op))->tp_dict);                  \
    Py_XDECREF(((PyTypeObject *)(op))->tp_bases);                 \
    Py_XDECREF(((PyTypeObject *)(op))->tp_mro);                   \
    Py_XDECREF(((PyTypeObject *)(op))->tp_cache);                 \
    Py_XDECREF(((PyTypeObject *)(op))->tp_subclasses);            \
    Py_XDECREF(((PyTypeObject *)(op))->tp_weaklist);              \
  } while(0)
#else
#define PyType_CLEAR(op)
#endif

#ifdef DEBUG_READER
#ifdef __STDC__
#define Debug_Print(...) PySys_WriteStderr(__VA_ARGS__)
#else
#define Debug_Print PySys_WriteStderr
#endif

#define Debug_FunctionCall(name, ptr)           \
  Debug_Print("### %s(%p)\n", #name, ptr)

#define Debug_Return(name, fmt, arg)                    \
  Debug_Print("### %s() => " fmt "\n", #name, arg)

#define Debug_ParserFunctionCall(name, parser)  \
  Debug_FunctionCall(name, parser->context)

#define Debug_ReturnStatus(name, status)                                \
  Debug_Return(name, "%s",                                              \
               (status == EXPAT_STATUS_ERROR ? "ERROR" :                \
                status == EXPAT_STATUS_OK ? "OK" :                      \
                status == EXPAT_STATUS_SUSPENDED ? "SUSPENDED" :        \
                "UNKNOWN"))
#else
#ifdef __STDC__ /* C99 conformance macro */
#define Debug_Print(...)
#else
/* Decent compilers will optimize this out, hopefully */
Py_LOCAL_INLINE(void) Debug_Print(const char *format, ...) { }
#endif
#define Debug_FunctionCall(name, ptr)
#define Debug_Return(name, fmt, arg)
#define Debug_ParserFunctionCall(name, parser)
#define Debug_ReturnStatus(name, status)
#endif

#ifdef __cplusplus
}
#endif

#endif /* EXPAT_DEBUG_H */
