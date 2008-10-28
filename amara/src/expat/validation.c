#include "Python.h"
#include "structmember.h"
#include "validation.h"
#include "content_model.h"
#include "debug.h"

typedef struct Context {
  struct Context *next;
  PyObject *element;    /* ElementTypeObject */
  PyObject *state;      /* last valid state */
} Context;

struct ValidatorStruct {
  PyObject_HEAD
  PyObject *elements;   /* mapping of tagName -> ElementType */
  Context *context;
  Context *free_context;
};

/** Complete Content Model ********************************************/

/** AttribueTypeObject ********************************************/

static PyTypeObject AttributeType_Type;
#define AttributeType_Check(op) \
  ((op) && ((op)->ob_type == &AttributeType_Type))

static PyObject *AttributeType_New(PyObject *name, AttributeType type,
                                   AttributeDecl decl,
                                   PyObject *allowedValues,
                                   PyObject *defaultValue)
{
  AttributeTypeObject *self;

  self = PyObject_New(AttributeTypeObject, &AttributeType_Type);
  if (self) {
    Py_INCREF(name);
    self->name = name;
    self->type = type;
    self->decl = decl;
    Py_XINCREF(allowedValues);
    self->allowed_values = allowedValues;
    Py_XINCREF(defaultValue);
    self->value = defaultValue;
  }
  return (PyObject *) self;
}

static void AttributeType_Del(AttributeTypeObject *self)
{
  Py_DECREF(self->name);
  Py_XDECREF(self->allowed_values);
  Py_XDECREF(self->value);
  PyObject_Del(self);
}

static PyTypeObject AttributeType_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "AttributeType",
  /* tp_basicsize      */ sizeof(AttributeTypeObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) AttributeType_Del,
};

/** ElementTypeObject *********************************************/

static PyTypeObject ElementType_Type;
#define ElementType_Check(op) ((op) && ((op)->ob_type == &ElementType_Type))

#define ElementType_SET_ATTRIBUTE(op, name, attr) \
  PyDict_SetItem(ElementType_GET_ATTRIBUTES(op), (name), (attr))

PyObject *ElementType_New(PyObject *name, PyObject *model)
{
  ElementTypeObject *self;

  self = PyObject_New(ElementTypeObject, &ElementType_Type);
  if (self) {
    Py_INCREF(name);
    self->name = name;

    self->attributes = PyDict_New();
    if (self->attributes == NULL) {
      Py_DECREF(self->name);
      PyObject_Del(self);
      return NULL;
    }

    if (model == NULL) {
      self->content_model = NULL;
    } else {
      self->content_model = ContentModel_Compile(model);
      if (self->content_model == NULL) {
        Py_DECREF(self->name);
        Py_DECREF(self->attributes);
        PyObject_Del(self);
        return NULL;
      }
    }
  }
  return (PyObject *) self;
}


static void ElementType_Del(ElementTypeObject *self)
{
  Py_DECREF(self->name);
  Py_DECREF(self->attributes);
  Py_XDECREF(self->content_model);
  PyObject_Del(self);
}


int ElementType_SetContentModel(PyObject *self, PyObject *model)
{
  PyObject *dfa, *tmp;

  if (!ElementType_Check(self)) {
    PyErr_BadInternalCall();
    return -1;
  }

  if (model == NULL) {
    dfa = NULL;
  } else {
    dfa = ContentModel_Compile(model);
    if (dfa == NULL) {
      return -1;
    }
  }

  tmp = ((ElementTypeObject *)self)->content_model;
  ((ElementTypeObject *)self)->content_model = dfa;
  Py_XDECREF(tmp);

  return 0;
}


int ElementType_AddAttribute(PyObject *self, PyObject *name,
                             AttributeType type, AttributeDecl decl,
                             PyObject *allowedValues, PyObject *defaultValue)
{
  PyObject *attr;

  if (!ElementType_Check(self)) {
    PyErr_BadInternalCall();
    return -1;
  }

  /* already defined, keep first decl */
  if (ElementType_GET_ATTRIBUTE(self, name))
    return 0;

  /* create the attribute type object */
  attr = AttributeType_New(name, type, decl, allowedValues, defaultValue);
  if (attr == NULL) {
    return -1;
  }

  /* add it to the declared attributes mapping */
  if (ElementType_SET_ATTRIBUTE(self, name, attr) < 0) {
    Py_DECREF(attr);
    return -1;
  }
  Py_DECREF(attr);

  return 1;
}


static PyTypeObject ElementType_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "ElementType",
  /* tp_basicsize      */ sizeof(ElementTypeObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) ElementType_Del,
};

/** ValidatorObject ***********************************************/

static PyTypeObject Validator_Type;
#define Validator_Check(op) ((op) && ((op)->ob_type == &Validator_Type))
#define Validator_Elements(op) (((ValidatorObject *)(op))->elements)
#define Validator_Context(op) (((ValidatorObject *)(op))->context)
#define Validator_FreeContext(op) (((ValidatorObject *)(op))->free_context)

static Context *Context_New(PyObject *elementType)
{
  Context *self;

  self = (Context *) PyObject_MALLOC(sizeof(Context));
  if (self == NULL) {
    PyErr_NoMemory();
    return NULL;
  }
  memset(self, 0, sizeof(Context));

  self->element = elementType;
  return self;
}


static void Context_Del(Context *self)
{
  if (self->next) {
    Context_Del(self->next);
  }
  PyObject_FREE(self);
}


PyObject *Validator_New(void)
{
  ValidatorObject *self;

  self = PyObject_New(ValidatorObject, &Validator_Type);
  if (self) {
    self->elements = PyDict_New();
    if (self->elements == NULL) {
      PyObject_Del(self);
      return NULL;
    }

    self->context = NULL;

    self->free_context = NULL;
  }
  return (PyObject *) self;
}


int Validator_AddElementType(PyObject *self, PyObject *element)
{
  if (!Validator_Check(self) && !ElementType_Check(element)) {
    PyErr_BadInternalCall();
    return -1;
  }

  /* already defined, keep first decl */
  if (PyDict_GetItem(Validator_Elements(self), ElementType_GET_NAME(element)))
    return 0;

  /* add the ElementType to our set of legal elements */
  if (PyDict_SetItem(Validator_Elements(self), ElementType_GET_NAME(element),
                     element) < 0) {
    return -1;
  }

  return 1;
}


PyObject *Validator_GetElementType(PyObject *self, PyObject *name)
{
  if (!Validator_Check(self)) {
    PyErr_BadInternalCall();
    return NULL;
  }

  return PyDict_GetItem(Validator_Elements(self), name);
}


PyObject *Validator_GetCurrentElementType(PyObject *self)
{
  if (!Validator_Check(self)) {
    PyErr_BadInternalCall();
    return NULL;
  }

  /* context may be NULL if we never encounter a declared element */
  ;
  if (Validator_Context(self) != NULL) {
    return Validator_Context(self)->element;
  }

  return NULL;
}

Py_LOCAL_INLINE(int)
transit_event(PyObject *self, PyObject *event, int save)
{
  Context *context;
  PyObject *state;

  if (!Validator_Check(self)) {
    PyErr_BadInternalCall();
    return -1;
  }

#ifdef DEBUG_VALIDATION
  fprintf(stderr, "Validator_ValidateEvent(event=");
  PyObject_Print(event, stderr, 0);
  fprintf(stderr, ")\n");
#endif

  context = Validator_Context(self);
  /* context may be NULL if we never encounter a declared element */
  if (context != NULL) {
    /* check that this element is allowed here */
    /* context->state will be NULL for an ANY content model */
    if (context->state != NULL) {
      state = PyDict_GetItem(context->state, event);
      if (state == NULL) {
        /* element not allowed here */
#ifdef DEBUG_VALIDATION
        fprintf(stderr, "  Event not allowed on ");
        if (context->element) {
          PyObject_Print(ElementType_GET_NAME(context->element), stderr, 0);
        } else {
          fprintf(stderr, " undeclared");
        }
        fprintf(stderr, " element.\n");
#endif
        return 0;
      }
      if (save) {
        /* save the state for next time */
        context->state = state;
      }
    }
  }

  return 1;
}


int Validator_ValidateEvent(PyObject *self, PyObject *event)
{
  return transit_event(self, event, 1);
}


int Validator_CheckEvent(PyObject *self, PyObject *event)
{
  return transit_event(self, event, 0);
}


int Validator_StartElement(PyObject *self, PyObject *name)
{
  PyObject *element_type;
  Context *context;

  if (!Validator_Check(self)) {
    PyErr_BadInternalCall();
    return -1;
  }

#ifdef DEBUG_VALIDATION
  fprintf(stderr, "Validator_StartElement(name=");
  PyObject_Print(name, stderr, 0);
  fprintf(stderr, ")\n");
#endif

  /* Switch to this element's content model.  element_type will be NULL
   * if not found, following code will just consider that as an ANY content
   * model to allow for continued  processing if error reporting doesn't
   * raise an exception. */
  element_type = PyDict_GetItem(Validator_Elements(self), name);
  context = Validator_FreeContext(self);
  if (context == NULL) {
    /* create a new context */
    context = Context_New(element_type);
    if (context == NULL) {
      return -1;
    }
  } else {
    /* reuse an existing context */
    Validator_FreeContext(self) = context->next;
    context->element = element_type;
  }

  /* setup initial state */
  if (element_type != NULL) {
    context->state = ElementType_GET_MODEL(element_type);
  }

  /* make it the active context */
  context->next = Validator_Context(self);
  Validator_Context(self) = context;

  return element_type != NULL;
}


int Validator_EndElement(PyObject *self)
{
  Context *context;
  int valid;

  if (!Validator_Check(self)) {
    PyErr_BadInternalCall();
    return -1;
  }

#ifdef DEBUG_VALIDATION
  fprintf(stderr, "Validator_EndElement()");
#endif

  context = Validator_Context(self);
  /* context may be NULL if we never encounter a declared element */
  if (context != NULL) {
#ifdef DEBUG_VALIDATION
    fprintf(stderr, " for ");
    if (context->element) {
      PyObject_Print(ElementType_GET_NAME(context->element), stderr, 0);
    } else {
      fprintf(stderr, "undeclared");
    }
    fprintf(stderr, " element\n");
#endif

    /* make sure that we are in the final state */
    valid = Validator_ValidateEvent(self, ContentModel_FinalEvent);

    /* switch the active context to the following one */
    Validator_Context(self) = context->next;

    /* move this one to the free list */
    context->next = Validator_FreeContext(self);
    Validator_FreeContext(self) = context;
  } else {
    valid = 1;
  }

  return valid;
}


static void validator_dealloc(ValidatorObject *self)
{
  Py_DECREF(self->elements);

  if (self->context) {
    Context_Del(self->context);
  }

  if (self->free_context) {
    Context_Del(self->free_context);
  }

  PyObject_Del(self);
}

static PyTypeObject Validator_Type = {
  /* PyObject_HEAD     */ PyObject_HEAD_INIT(NULL)
  /* ob_size           */ 0,
  /* tp_name           */ "Validator",
  /* tp_basicsize      */ sizeof(ValidatorObject),
  /* tp_itemsize       */ 0,
  /* tp_dealloc        */ (destructor) validator_dealloc,
};

/** Module Interface **************************************************/

int _Expat_Validation_Init(PyObject *module)
{
  if (PyType_Ready(&AttributeType_Type) < 0)
    return -1;

  if (PyType_Ready(&ElementType_Type) < 0)
    return -1;

  if (PyType_Ready(&Validator_Type) < 0)
    return -1;

  return 0;
}

void _Expat_Validation_Fini(void)
{
  PyType_CLEAR(&AttributeType_Type);
  PyType_CLEAR(&ElementType_Type);
  PyType_CLEAR(&Validator_Type);
}
