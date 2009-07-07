#include "Python.h"
#include "structmember.h"
#include "content_model.h"
#include "debug.h"

static PyObject *epsilon_event;
PyObject *ContentModel_FinalEvent;

#define State_New() PyDict_New()

#define ContentModel_Size(cm) PyList_GET_SIZE(cm)
#define ContentModel_AddState(cm, state) PyList_Append((cm), (state))
#define ContentModel_GetState(cm, statenum) PyList_GET_ITEM((cm), (statenum))

#define DFA_New() PyList_New(0)
#define DFA_Size(dfa) PyList_GET_SIZE(dfa)
#define DFA_NewState(dfa) PyDict_New()
#define DFA_AddState(dfa, state) PyList_Append((dfa), (state))
#define DFA_GetInitialState(dfa) PyList_GET_ITEM((dfa), 0)
#define DFA_GetState(dfa, statenum) PyList_GET_ITEM((dfa), (statenum))

/** Non-Deterministic Finite Automaton ********************************/

PyObject *ContentModel_New(void)
{
  PyObject *self;

  self = PyList_New((Py_ssize_t)0);
  if (self) {
    /* add the initial state */
    if (ContentModel_NewState(self) < 0) {
      Py_DECREF(self);
      return NULL;
    }
    /* add the final state */
    if (ContentModel_NewState(self) < 0) {
      Py_DECREF(self);
      return NULL;
    }
  }
  return self;
}


Py_ssize_t ContentModel_NewState(PyObject *self)
{
  PyObject *state;
  Py_ssize_t state_number;

  /* a "state" is nothing more than a dictionary of transitions */
  state = PyDict_New();
  if (state == NULL)
    return -1;

  state_number = ContentModel_Size(self);
  if (ContentModel_AddState(self, state) < 0) {
    Py_DECREF(state);
    return -1;
  }

  /* let the list own the reference */
  Py_DECREF(state);

  return state_number;
}


int ContentModel_AddTransition(PyObject *self,
                               PyObject *event,
                               Py_ssize_t from_state,
                               Py_ssize_t to_state)
{
  PyObject *state;
  PyObject *transitions;
  PyObject *state_number;

  if (from_state > ContentModel_Size(self)) {
    PyErr_Format(PyExc_SystemError, "state %zd out of bounds", from_state);
    return -1;
  }

  state_number = PyInt_FromSsize_t(to_state);
  if (state_number == NULL) {
    return -1;
  }

  state = ContentModel_GetState(self, from_state);
  transitions = PyDict_GetItem(state, event);
  if (transitions == NULL) {
    transitions = PyList_New((Py_ssize_t)1);
    if (transitions == NULL) {
      Py_DECREF(state_number);
      return -1;
    }
    PyList_SET_ITEM(transitions, 0, state_number);

    if (PyDict_SetItem(state, event, transitions) < 0) {
      Py_DECREF(transitions);
      return -1;
    }
    Py_DECREF(transitions);
  } else {
    if (PyList_Append(transitions, state_number) < 0) {
      Py_DECREF(state_number);
      return -1;
    }
    Py_DECREF(state_number);
  }

  return 0; /* success */
}


int ContentModel_AddEpsilonMove(PyObject *self,
                                Py_ssize_t from_state,
                                Py_ssize_t to_state)
{
  return ContentModel_AddTransition(self, epsilon_event, from_state,
                                    to_state);
}

/** Deterministic Finite Automaton ************************************/


/* Recursively add the states reachable from the given state by
 * epsilon moves.
 */
static int add_to_epsilon_closure(PyObject *model, PyObject *state_set,
                                  PyObject *state_num)
{
  PyObject *state, *transitions;
  Py_ssize_t i;

  if (PyDict_GetItem(state_set, state_num) == NULL) {
    if (PyDict_SetItem(state_set, state_num, Py_True) < 0) {
      return -1;
    }
    state = ContentModel_GetState(model, PyInt_AS_LONG(state_num));
    transitions = PyDict_GetItem(state, epsilon_event);
    if (transitions) {
      for (i = 0; i < PyList_GET_SIZE(transitions); i++) {
        state_num = PyList_GET_ITEM(transitions, i);
        if (add_to_epsilon_closure(model, state_set, state_num) < 0) {
          return -1;
        }
      }
    }
  }
  return 0; /* success */
}

/* Return the set of states reachable from the given state by epsilon moves. */
static PyObject *epsilon_closure(PyObject *model, PyObject *state_num)
{
  PyObject *state_set;

  state_set = PyDict_New();
  if (state_set) {
    if (add_to_epsilon_closure(model, state_set, state_num) < 0) {
      Py_DECREF(state_set);
      return NULL;
    }
  }
  return state_set;
}

/* Given a list of states, return the union of the epsilon closures for each
 * of its member states.
 */
static int set_epsilon_closure(PyObject *model, PyObject *state_set,
                               PyObject *states)
{
  PyObject *epsilon_set;
  Py_ssize_t i;

  for (i = 0; i < PyList_GET_SIZE(states); i++) {
    epsilon_set = epsilon_closure(model, PyList_GET_ITEM(states, i));
    if (epsilon_set == NULL) {
      return -1;
    }
    if (PyDict_Merge(state_set, epsilon_set, 1) < 0) {
      Py_DECREF(epsilon_set);
      return -1;
    }
    Py_DECREF(epsilon_set);
  }
  return 0;
}

/* Convert the set of state numbers into a sorted tuple for use as a
 * dictionary key.
 */
static PyObject *make_key(PyObject *state_set)
{
  PyObject *states, *key;

  states = PyDict_Keys(state_set);
  if (states == NULL) {
    return NULL;
  }
  if (PyList_Sort(states) < 0) {
    Py_DECREF(states);
    return NULL;
  }
  key = PySequence_Tuple(states);
  Py_DECREF(states);
  if (key == NULL) {
    return NULL;
  }
  return key;
}

/* Return the state of the new machine corresponding to the set of NFA states
 * represented by 'state_set'.  A new state will be created if needed.
 */
static PyObject *map_old_to_new(PyObject *dfa,
                                PyObject *old_to_new_map,
                                PyObject *new_to_old_map,
                                PyObject *state_set)
{
  PyObject *key;
  PyObject *new_state;

  key = make_key(state_set);
  if (key == NULL) {
    return NULL;
  }

  new_state = PyDict_GetItem(old_to_new_map, key);
  if (new_state == NULL) {
    /* Create a new state in the DFA machine */
    new_state = DFA_NewState(dfa);
    if (new_state == NULL) {
      Py_DECREF(key);
      return NULL;
    }
    if (PyDict_SetItem(old_to_new_map, key, new_state) < 0) {
      Py_DECREF(key);
      Py_DECREF(new_state);
      return NULL;
    }
    Py_DECREF(key);
    Py_DECREF(new_state);

    key = PyInt_FromSsize_t(DFA_Size(dfa));
    if (PyDict_SetItem(new_to_old_map, key, state_set) < 0) {
      Py_DECREF(key);
      return NULL;
    }

    if (DFA_AddState(dfa, new_state) < 0) {
      return NULL;
    }

#if defined(DEBUG_VALIDATION)
    /* Add the state number to the new state for debugging */
    if (PyDict_SetItemString(new_state, "number", key) < 0) {
      Py_DECREF(key);
      return NULL;
    }
#endif
  }

  Py_DECREF(key);

  return new_state;
}



/* Given a non-deterministic machine, return a new equivalent machine
 * which is deterministic.
 */
PyObject *ContentModel_Compile(PyObject *model)
{
  PyObject *dfa;
  PyObject *old_to_new_map;
  PyObject *new_to_old_map;
  PyObject *transitions;
  PyObject *initial_state;
  PyObject *state_set;
  PyObject *new_state;
  Py_ssize_t final_state, dfa_state;

  final_state = ContentModel_NewState(model);
  if (final_state < 0)
    return NULL;

  if (ContentModel_AddTransition(model, ContentModel_FinalEvent,
                                 1, final_state) < 0)
    return NULL;

  dfa = DFA_New();
  old_to_new_map = PyDict_New();
  new_to_old_map = PyDict_New();
  transitions = PyDict_New();
  if (dfa == NULL
      || old_to_new_map == NULL
      || new_to_old_map == NULL
      || transitions == NULL) {
    Py_XDECREF(old_to_new_map);
    Py_XDECREF(new_to_old_map);
    Py_XDECREF(transitions);
    Py_XDECREF(dfa);
    return NULL;
  }

  /* Seed the process using the initial states of the old machines. */
  initial_state = PyInt_FromLong(0L);
  if (initial_state == NULL) goto error;

  state_set = epsilon_closure(model, initial_state);
  Py_DECREF(initial_state);
  if (state_set == NULL) goto error;

  new_state = map_old_to_new(dfa, old_to_new_map, new_to_old_map, state_set);
  Py_DECREF(state_set);
  if (new_state == NULL) goto error;

  /* Tricky bit here; we add things to the end of this list while
   * iterating over it.  The iteration stops when closure is achieved.
   */
  for (dfa_state = 0; dfa_state < DFA_Size(dfa); dfa_state++) {
    PyObject *state_num;
    PyObject *event;
    PyObject *temp;
    Py_ssize_t i;

    new_state = PyInt_FromSsize_t(dfa_state);
    if (new_state == NULL) goto error;

    state_set = PyDict_GetItem(new_to_old_map, new_state);
    Py_DECREF(new_state);
    if (state_set == NULL) {
      /* this should not happen, but just in case... */
      PyErr_Format(PyExc_SystemError, "state %zd not mapped to old states", i);
      goto error;
    }

    PyDict_Clear(transitions);

    i = 0;
    while (PyDict_Next(state_set, &i, &state_num, &temp)) {
      PyObject *old_transitions, *target_states;
      int nfa_state;
      Py_ssize_t n;

      nfa_state = PyInt_AS_LONG(state_num);
      if (nfa_state >= ContentModel_Size(model)) {
        PyErr_Format(PyExc_SystemError, "state %d not a valid NFA state",
                     nfa_state);
        goto error;
      }
      old_transitions = ContentModel_GetState(model, nfa_state);
      n = 0;
      while (PyDict_Next(old_transitions, &n, &event, &target_states)) {
        if (event != epsilon_event) {
          PyObject *old_state_set = PyDict_GetItem(transitions, event);
          if (old_state_set == NULL) {
            old_state_set = PyDict_New();
            if (old_state_set == NULL) goto error;

            if (PyDict_SetItem(transitions, event, old_state_set) < 0) {
              Py_DECREF(old_state_set);
              goto error;
            }
            Py_DECREF(old_state_set);
          }
          if (set_epsilon_closure(model, old_state_set, target_states) < 0) {
            goto error;
          }
        }
      }
    }

    i = 0;
    while (PyDict_Next(transitions, &i, &event, &state_set)) {
      PyObject *new_transitions;
      new_state = map_old_to_new(dfa, old_to_new_map, new_to_old_map,
                                 state_set);
      if (new_state == NULL) goto error;

      new_transitions = DFA_GetState(dfa, dfa_state);
      if (PyDict_SetItem(new_transitions, event, new_state) < 0) goto error;
    }
  }

  Py_DECREF(old_to_new_map);
  Py_DECREF(new_to_old_map);
  Py_DECREF(transitions);

  model = DFA_GetInitialState(dfa);
  Py_INCREF(model);
  Py_DECREF(dfa);
  return model;

 error:
  Py_DECREF(old_to_new_map);
  Py_DECREF(new_to_old_map);
  Py_DECREF(transitions);
  Py_DECREF(dfa);
  return NULL;
}

/** Python Interface **************************************************/

typedef enum {
  CONTENT_TYPE_NAME,
  CONTENT_TYPE_SEQ,
  CONTENT_TYPE_ALT,
} ContentType;

typedef enum {
  CONTENT_QUANT_NONE,
  CONTENT_QUANT_OPT,
  CONTENT_QUANT_REP,
  CONTENT_QUANT_PLUS,
} ContentQuant;

typedef struct {
  PyObject_HEAD
  PyObject *content;
  ContentType type;
  ContentQuant quant;
  PyObject *label;
  PyObject *doc;
} ContentModelObject;

static PyTypeObject ContentModel_Type;

/* helper functions for compiling an object-based ndfa */

Py_LOCAL(int)
compile_content(PyObject *model, ContentModelObject *content,
                Py_ssize_t initial_state, Py_ssize_t final_state);

Py_LOCAL_INLINE(int)
compile_name(PyObject *model, ContentModelObject *content,
             Py_ssize_t initial_state, Py_ssize_t final_state)
{
  return ContentModel_AddTransition(model, content->content, initial_state,
                                    final_state);
}

Py_LOCAL_INLINE(int)
compile_seq(PyObject *model, ContentModelObject *content,
            Py_ssize_t initial_state, Py_ssize_t final_state)
{
  PyObject *seq;
  ContentModelObject *item;
  Py_ssize_t i, size, next_state;

  seq = content->content;
  size = PyTuple_GET_SIZE(seq);
  if (size == 0) {
    return 0;
  }
  for (i = 0, size--; i < size; i++) {
    item = (ContentModelObject *) PyTuple_GET_ITEM(seq, i);
    next_state = ContentModel_NewState(model);
    if (next_state < 0) {
      return -1;
    }
    if (compile_content(model, item, initial_state, next_state) < 0) {
      return -1;
    }
    initial_state = next_state;
  }
  item = (ContentModelObject *) PyTuple_GET_ITEM(seq, i);
  if (compile_content(model, item, initial_state, final_state) < 0) {
    return -1;
  }
  return 0; /* success */
}

Py_LOCAL_INLINE(int)
compile_alt(PyObject *model, ContentModelObject *content,
            Py_ssize_t initial_state, Py_ssize_t final_state)
{
  PyObject *seq;
  ContentModelObject *item;
  Py_ssize_t i, size;

  seq = content->content;
  size = PyTuple_GET_SIZE(seq);
  for (i = 0; i < size; i++) {
    item = (ContentModelObject *) PyTuple_GET_ITEM(seq, i);
    if (compile_content(model, item, initial_state, final_state) < 0) {
      return -1;
    }
  }
  return 0; /* success */
}

Py_LOCAL(int)
compile_content(PyObject *model, ContentModelObject *content,
                Py_ssize_t initial_state, Py_ssize_t final_state)
{
  Py_ssize_t s1, s2;

  switch (content->quant) {
  case CONTENT_QUANT_OPT:
    if (ContentModel_AddEpsilonMove(model, initial_state, final_state) < 0) {
      return -1;
    }
    /* fall through */
  case CONTENT_QUANT_NONE:
    switch (content->type) {
    case CONTENT_TYPE_NAME:
      return compile_name(model, content, initial_state, final_state);
    case CONTENT_TYPE_SEQ:
      return compile_seq(model, content, initial_state, final_state);
    case CONTENT_TYPE_ALT:
      return compile_alt(model, content, initial_state, final_state);
    default:
      PyErr_Format(PyExc_SystemError, "invalid type %d", content->type);
      return -1;
    }
  case CONTENT_QUANT_REP:
    if (ContentModel_AddEpsilonMove(model, initial_state, final_state) < 0) {
      return -1;
    }
    /* fall through */
  case CONTENT_QUANT_PLUS:
    s1 = ContentModel_NewState(model);
    s2 = ContentModel_NewState(model);
    if (s1 < 0 || s2 < 0) {
      return -1;
    }
    if (ContentModel_AddEpsilonMove(model, initial_state, s1) < 0) {
      return -1;
    }
    switch (content->type) {
    case CONTENT_TYPE_NAME:
      if (compile_name(model, content, s1, s2) < 0)
      	return -1;
      break;
    case CONTENT_TYPE_SEQ:
      if (compile_seq(model, content, s1, s2) < 0)
      	return -1;
      break;
    case CONTENT_TYPE_ALT:
      if (compile_alt(model, content, s1, s2) < 0)
      	return -1;
      break;
    default:
      PyErr_Format(PyExc_SystemError, "invalid type %d", content->type);
      return -1;
    }
    if (ContentModel_AddEpsilonMove(model, s2, s1) < 0) {
      return -1;
    }
    return ContentModel_AddEpsilonMove(model, s2, final_state);
  default:
    PyErr_Format(PyExc_SystemError, "invalid quantity %d", content->quant);
    return -1;
  }
}

static char model_doc[] = "\
ContentModel(type, content[, quant[, label[, doc]]])\n\
\n\
Creates a new ContentModel object.";

static int model_init(ContentModelObject *self, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = { "type", "content", "quant", "label", "doc", NULL };
  PyObject *seq, *content, *label=NULL, *doc=NULL;
  ContentType type;
  ContentQuant quant=CONTENT_QUANT_NONE;
  int i;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "iO|iOO:ContentModel", kwlist,
                                   &type, &content, &quant, &label, &doc))
    return -1;

  switch (type) {
  case CONTENT_TYPE_NAME:
    Py_INCREF(content);
    break;
  case CONTENT_TYPE_SEQ:
  case CONTENT_TYPE_ALT:
    seq = PySequence_Tuple(content);
    if (seq == NULL) {
      if (PyErr_ExceptionMatches(PyExc_TypeError)) {
        PyErr_Format(PyExc_TypeError, "sequence expected, %.80s found",
                     content == Py_None ? "None" : content->ob_type->tp_name);
      }
      return -1;
    }
    content = seq;
    for (i = 0; i < PyTuple_GET_SIZE(content); i++) {
      PyObject *item = PyTuple_GET_ITEM(content, i);
      if (item->ob_type != &ContentModel_Type) {
        PyErr_Format(PyExc_TypeError,
                     "sequence of ContentModel expected, %.80s found at %d",
                     item == Py_None ? "None" : item->ob_type->tp_name, i);
        Py_DECREF(content);
        return -1;
      }
    }
    break;
  default:
    PyErr_Format(PyExc_ValueError, "type must be in range %d to %d",
                 CONTENT_TYPE_NAME, CONTENT_TYPE_ALT);
    return -1;
  }
  self->type = type;
  self->content = content;

  if (quant < CONTENT_QUANT_NONE || quant > CONTENT_QUANT_PLUS) {
    PyErr_Format(PyExc_ValueError, "quant must be in range %d to %d",
                 CONTENT_QUANT_NONE, CONTENT_QUANT_PLUS);
    return -1;
  } else {
    self->quant = quant;
  }

  Py_XINCREF(label);
  self->label = label;

  Py_XINCREF(doc);
  self->doc = doc;

  return 0;
}

static void model_dealloc(ContentModelObject *self)
{
  Py_XDECREF(self->content);
  Py_XDECREF(self->label);
  Py_XDECREF(self->doc);
  self->ob_type->tp_free((PyObject *) self);
}

static PyObject *model_str(ContentModelObject *self)
{
  if (self->label != NULL) {
    Py_INCREF(self->label);
    return self->label;
  }
  return PyObject_Repr((PyObject *) self);
}

static char compile_doc[] = "\
compile() -> mapping\n\
\n\
Compile a non-deterministic content model into a deterministic one\n\
represented by nested dictionaries.";

static PyObject *model_compile(ContentModelObject *self, PyObject *args)
{
  PyObject *model, *dfa;

  model = ContentModel_New();
  if (model == NULL) {
    return NULL;
  }
  if (compile_content(model, self, 0, 1) < 0) {
    Py_DECREF(model);
    return NULL;
  }
  dfa = ContentModel_Compile(model);
  Py_DECREF(model);
  return dfa;
}

static PyMethodDef model_methods[] = {
  { "compile", (PyCFunction) model_compile, METH_NOARGS, compile_doc },
  { NULL }
};

static PyObject *model_get_quant(ContentModelObject *self, void *arg)
{
  return PyInt_FromLong(self->quant);
}

static int model_set_quant(ContentModelObject *self, PyObject *v, void *arg)
{
  long quant;

  quant = PyInt_AsLong(v);
  if (quant < 0 && PyErr_Occurred())
    return -1;

  if (quant < CONTENT_QUANT_NONE || quant > CONTENT_QUANT_PLUS) {
    PyErr_Format(PyExc_ValueError, "value must be in range %d to %d",
                 CONTENT_QUANT_NONE, CONTENT_QUANT_PLUS);
    return -1;
  }

  self->quant = (int) quant;
  return 0;
}

static PyObject *model_get_doc(ContentModelObject *self, void *arg)
{
  if (self->doc) {
    Py_INCREF(self->doc);
    return self->doc;
  }
  return PyObject_GetAttrString((PyObject *) self->ob_type, "__doc__");
}

static PyGetSetDef model_getset[] = {
  { "quant",   (getter) model_get_quant, (setter) model_set_quant },
  { "__doc__", (getter) model_get_doc,   (setter) 0 },
  { NULL }
};

static PyTypeObject ContentModel_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "ContentModel",
  /* tp_basicsize      */ sizeof(ContentModelObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) model_dealloc,
  /* tp_print          */ (printfunc) 0,
  /* tp_getattr        */ (getattrfunc) 0,
  /* tp_setattr        */ (setattrfunc) 0,
  /* tp_compare        */ (cmpfunc) 0,
  /* tp_repr           */ (reprfunc) 0,
  /* tp_as_number      */ (PyNumberMethods *) 0,
  /* tp_as_sequence    */ (PySequenceMethods *) 0,
  /* tp_as_mapping     */ (PyMappingMethods *) 0,
  /* tp_hash           */ (hashfunc) 0,
  /* tp_call           */ (ternaryfunc) 0,
  /* tp_str            */ (reprfunc) model_str,
  /* tp_getattro       */ (getattrofunc) 0,
  /* tp_setattro       */ (setattrofunc) 0,
  /* tp_as_buffer      */ (PyBufferProcs *) 0,
  /* tp_flags          */ Py_TPFLAGS_DEFAULT,
  /* tp_doc            */ (char *) model_doc,
  /* tp_traverse       */ (traverseproc) 0,
  /* tp_clear          */ (inquiry) 0,
  /* tp_richcompare    */ (richcmpfunc) 0,
  /* tp_weaklistoffset */ 0,
  /* tp_iter           */ (getiterfunc) 0,
  /* tp_iternext       */ (iternextfunc) 0,
  /* tp_methods        */ (PyMethodDef *) model_methods,
  /* tp_members        */ (PyMemberDef *) 0,
  /* tp_getset         */ (PyGetSetDef *) model_getset,
  /* tp_base           */ (PyTypeObject *) 0,
  /* tp_dict           */ (PyObject *) 0,
  /* tp_descr_get      */ (descrgetfunc) 0,
  /* tp_descr_set      */ (descrsetfunc) 0,
  /* tp_dictoffset     */ 0,
  /* tp_init           */ (initproc) model_init,
  /* tp_alloc          */ (allocfunc) 0,
  /* tp_new            */ (newfunc) 0,
  /* tp_free           */ 0,
};

/** Module Interface **************************************************/

int _Expat_ContentModel_Init(PyObject *module)
{
  PyObject *dict, *item;

  /* create a new unique token to represent an epsilon transition */
  epsilon_event = PyCObject_FromVoidPtr(NULL, NULL);
  if (epsilon_event == NULL) return -1;

  /* create a new unique token to represent the final transition */
  ContentModel_FinalEvent = PyCObject_FromVoidPtr(NULL, NULL);
  if (ContentModel_FinalEvent == NULL) return -1;

  ContentModel_Type.tp_new = PyType_GenericNew;
  if (PyType_Ready(&ContentModel_Type) < 0)
    return -1;

  dict = ContentModel_Type.tp_dict;
  if (PyDict_SetItemString(dict, "FINAL_EVENT", ContentModel_FinalEvent) < 0)
    return -1;

#define ContentModel_ADD_ENUM(NAME)                     \
  item = PyInt_FromLong(CONTENT_##NAME);                \
  if (item == NULL) return -1;                          \
  if (PyDict_SetItemString(dict, #NAME, item) < 0) {    \
    Py_DECREF(item);                                    \
    return -1;                                          \
  }                                                     \
  Py_DECREF(item)

  ContentModel_ADD_ENUM(QUANT_NONE);
  ContentModel_ADD_ENUM(QUANT_OPT);
  ContentModel_ADD_ENUM(QUANT_REP);
  ContentModel_ADD_ENUM(QUANT_PLUS);
  ContentModel_ADD_ENUM(TYPE_NAME);
  ContentModel_ADD_ENUM(TYPE_SEQ);
  ContentModel_ADD_ENUM(TYPE_ALT);
#undef ContentModel_ADD_ENUM

#define PyModule_ADD_TYPE(TYPE)                                         \
  Py_INCREF(&TYPE##_Type);                                              \
  if (PyModule_AddObject(module, #TYPE, (PyObject *) &TYPE##_Type) < 0) \
    return -1

  PyModule_ADD_TYPE(ContentModel);
#undef PyModule_ADD_TYPE

  return 0;
}

void _Expat_ContentModel_Fini(void)
{
  Py_DECREF(epsilon_event);
  Py_DECREF(ContentModel_FinalEvent);

  PyType_CLEAR(&ContentModel_Type);
}
