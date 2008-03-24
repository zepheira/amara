#include "util.h"
#include "frameobject.h"

/** Private Routines *************************************************/

static PyObject *empty_string;
static PyObject *empty_tuple;

/** Tracing **/

static int call_trace(Py_tracefunc func, PyObject *obj, PyFrameObject *frame,
                      int what, PyObject *arg)
{
  register PyThreadState *tstate = frame->f_tstate;
  int result;

  if (tstate->tracing)
    return 0;

  tstate->tracing++;
  tstate->use_tracing = 0;
  result = func(obj, frame, what, arg);
  tstate->use_tracing = ((tstate->c_tracefunc != NULL)
                         || (tstate->c_profilefunc != NULL));
  tstate->tracing--;
  return result;
}

static void call_trace_exc(Py_tracefunc func, PyObject *obj,
                           PyFrameObject *frame)
{
  PyObject *type, *value, *traceback, *arg;
  int err;
  PyErr_Fetch(&type, &value, &traceback);
  if (value == NULL) {
    value = Py_None;
    Py_INCREF(value);
  }
  arg = PyTuple_Pack(3, type, value, traceback);
  if (arg == NULL) {
    PyErr_Restore(type, value, traceback);
    return;
  }
  err = call_trace(func, obj, frame, PyTrace_EXCEPTION, arg);
  Py_DECREF(arg);
  if (err == 0)
    PyErr_Restore(type, value, traceback);
  else {
    Py_XDECREF(type);
    Py_XDECREF(value);
    Py_XDECREF(traceback);
  }
}

PyObject *PyTrace_CallObject(PyCodeObject *code, PyObject *func, PyObject *args)
{
  register PyThreadState *tstate = PyThreadState_GET();
  PyFrameObject *frame;
  PyObject *retval = NULL;

  if (code == NULL || args == NULL) {
    return NULL;
  }

  frame = PyFrame_New(tstate, code, PyEval_GetGlobals(), NULL);
  if (frame == NULL) {
    return NULL;
  }
  tstate->frame = frame;

  if (tstate->use_tracing) {
    if (tstate->c_tracefunc != NULL) {
      if (call_trace(tstate->c_tracefunc, tstate->c_traceobj,
                     frame, PyTrace_CALL, Py_None)) {
        goto finally;
      }
    }
    if (tstate->c_profilefunc != NULL) {
      if (call_trace(tstate->c_profilefunc, tstate->c_profileobj,
                     frame, PyTrace_CALL, Py_None)) {
        goto finally;
      }
    }
  }

  retval = PyObject_Call(func, args, NULL);
  if (retval == NULL) {
    PyTraceBack_Here(frame);
  }

  if (tstate->use_tracing) {
    if (tstate->c_tracefunc != NULL) {
      if (retval != NULL) {
        if (call_trace(tstate->c_tracefunc, tstate->c_traceobj,
                       frame, PyTrace_RETURN, retval)) {
          Py_CLEAR(retval);
        }
      } else {
        call_trace_exc(tstate->c_tracefunc, tstate->c_traceobj, frame);
      }
    }
    if (tstate->c_profilefunc != NULL) {
      if (retval == NULL) {
        call_trace_exc(tstate->c_profilefunc, tstate->c_profileobj, frame);
      } else {
        if (call_trace(tstate->c_profilefunc, tstate->c_profileobj,
                       frame, PyTrace_RETURN, retval)) {
          Py_CLEAR(retval);
        }
      }
    }
  }

finally:
  tstate->frame = frame->f_back;
  Py_DECREF(frame);
  return retval;
}

PyCodeObject *_PyCode_Here(char *name, char *file, int line)
{
  PyObject *co_name, *co_filename;
  PyCodeObject *code;

  co_name = PyString_FromString(name);
  co_filename = PyString_FromString(file);
  if (co_name == NULL || co_filename == NULL) {
    Py_XDECREF(co_name);
    Py_XDECREF(co_filename);
    return NULL;
  }

  code = PyCode_New(0, 0, 0, 0, /* argcount, nlocals, stacksize, flags */
                    /* code, consts, names, varnames */
                    empty_string, empty_tuple, empty_tuple, empty_tuple,
#if PYTHON_API_VERSION >= 1010
                    /* freevars, cellvars */
                    empty_tuple, empty_tuple,
#endif
                    /* filename, name, firstlineno, lnotab */
                    co_filename, co_name, line, empty_string);
  Py_DECREF(co_name);
  Py_DECREF(co_filename);
  return code;
}

/** (extension) PyModule_AddType **************************************/

int PyModule_AddType(PyObject *module, PyTypeObject *type)
{
  PyObject *dict;
  const char *tp_name;

  if (!PyModule_Check(module)) {
    PyErr_SetString(PyExc_TypeError,
                    "PyModule_AddType() needs module as first arg");
    return -1;
  }
  dict = PyModule_GetDict(module);
  if (dict == NULL) {
    /* Internal error -- modules must have a dict! */
    PyErr_Format(PyExc_SystemError, "module '%s' has no __dict__",
                 PyModule_GetName(module));
    return -1;
  }

  if (!type) {
    if (!PyErr_Occurred())
      PyErr_SetString(PyExc_TypeError,
                      "PyModule_AddType() needs non-NULL value");
    return -1;
  }
  if (PyType_Ready(type) < 0)
    return -1;

  tp_name = strrchr(type->tp_name, '.');
  if (tp_name == NULL)
    tp_name = type->tp_name;
  else
    tp_name++;

  return PyDict_SetItemString(PyModule_GetDict(module), tp_name,
                              (PyObject *)type);
}

/** Module Interface *************************************************/

int _Expat_Util_Init(PyObject *module)
{
  empty_string = PyString_FromStringAndSize(NULL, 0);
  if (empty_string == NULL) return -1;

  empty_tuple = PyTuple_New(0);
  if (empty_tuple == NULL) return -1;

  return 0;
}

void _Expat_Util_Fini(void)
{
  Py_CLEAR(empty_string);
  Py_CLEAR(empty_tuple);
}
