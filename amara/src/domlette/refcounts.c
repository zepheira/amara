#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/* Reference counting scheme *****************************************
 *
 * Domlette Nodes save a reference to their ownerDocument but use a
 * borrowed reference to their parentNode.
 *
 *********************************************************************/

static int do_test(PyObject *tester, char *title, Py_ssize_t expected,
                   Py_ssize_t actual)
{
  PyObject *rv;

  rv = PyObject_CallMethod(tester, "startTest", "s", title);
  if (rv == NULL)
    return 0;
  Py_DECREF(rv);

  rv = PyObject_CallMethod(tester, "compare", "nn", expected, actual);
  if (rv == NULL)
    return 0;
  Py_DECREF(rv);

  rv = PyObject_CallMethod(tester, "testDone", NULL);
  if (rv == NULL)
    return 0;
  Py_DECREF(rv);

  return 1;
}

static int node_refcounts(PyObject *tester, NodeObject *node,
                          Py_ssize_t *counter)
{
  Py_ssize_t expected;
  char buf[256];

  /* increment total node count */
  (*counter)++;

  if (Element_Check(node)) {
    Py_ssize_t i;
    NodeObject *child;
    NamespaceObject *ns;
    AttrObject *attr;

    /* test element's children */
    for (i = 0; i < Container_GET_COUNT(node); i++) {
      child = Container_GET_CHILD(node, i);
      if (node_refcounts(tester, child, counter) == 0) return 0;
    }

    /* test element's attributes */
    i = 0;
    while ((ns = NamespaceMap_Next(Element_NAMESPACES(node), &i))) {
      if (node_refcounts(tester, (NodeObject *)ns, counter) == 0) return 0;
    }

    /* test element's attributes */
    i = 0;
    while ((attr = AttributeMap_Next(Element_ATTRIBUTES(node), &i))) {
      if (node_refcounts(tester, (NodeObject *)attr, counter) == 0) return 0;
    }

    /* refcount = this */
    expected = 1;
  }
  else if (Text_Check(node)) {
    /* refcount = this */
    expected = 1;
  }
  else if (Comment_Check(node)) {
    /* refcount = this */
    expected = 1;
  }
  else if (Attr_Check(node)) {
    /* refcount = this */
    expected = 1;
  }
  else if (ProcessingInstruction_Check(node)) {
    /* refcount = this */
    expected = 1;
  }
  else {
    sprintf(buf, "Unexpected object type '%.200s'", node->ob_type->tp_name);
    Py_XDECREF(PyObject_CallMethod(tester, "error", "s", buf));
    return 0;
  }

  sprintf(buf, "%.200s refcounts", node->ob_type->tp_name);
  return do_test(tester, buf, expected, node->ob_refcnt);
}

int test_refcounts(PyObject *tester, PyObject *doc)
{
  Py_ssize_t expected;
  int i;
  char buf[256];

  /* refcount = 2  + counter (ownerDocument) */
  expected = 2;

  for (i = 0; i < Container_GET_COUNT(doc); i++) {
    NodeObject *node = Container_GET_CHILD(doc, i);
    if (node_refcounts(tester, node, &expected) == 0) return 0;
  }

  sprintf(buf, "%.200s refcounts", doc->ob_type->tp_name);
  return do_test(tester, buf, expected, doc->ob_refcnt);
}
