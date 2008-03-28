#define PY_SSIZE_T_CLEAN
#include "domlette_interface.h"

/** Domlette only implementation **************************************/

Py_LOCAL_INLINE(PyObject *)
get_prefix(PyObject *nodeName)
{
  Py_UNICODE *p;
  Py_ssize_t len, i;

  p = PyUnicode_AS_UNICODE(nodeName);
  len = PyUnicode_GET_SIZE(nodeName);
  for (i = 0; i < len; i++) {
    if (p[i] == ':') {
      return PyUnicode_FromUnicode(p, i);
    }
  }
  Py_INCREF(Py_None);
  return Py_None;
}

Py_LOCAL(int)
get_all_ns_domlette(NodeObject *node, PyObject *nss)
{
  int res = 0;

  if (Element_Check(node)) {
    PyObject *key, *attr;
    PyObject *namespaceURI, *prefix;
    Py_ssize_t i;

    /* get the prefix */
    prefix = get_prefix(Element_GET_NODE_NAME(node));
    if (prefix == NULL) return -1;

    /* add the declaration if prefix is not already defined */
    if (PyDict_GetItem(nss, prefix) == NULL) {
      if (PyDict_SetItem(nss, prefix, Element_GET_NAMESPACE_URI(node)) < 0) {
        Py_DECREF(prefix);
        return -1;
      }
    }
    Py_DECREF(prefix);

    /* now process this element's attributes */
    i = 0;
    while (PyDict_Next(Element_GET_ATTRIBUTES(node), &i, &key, &attr)) {
      namespaceURI = Attr_GET_NAMESPACE_URI(attr);
      /* get the prefix/namespaceURI pair to add */
      switch (PyObject_RichCompareBool(namespaceURI, g_xmlnsNamespace, Py_EQ)) {
      case 0:
        /* normal attribute */
        prefix = get_prefix(Attr_GET_NODE_NAME(attr));
        if (prefix == NULL) return -1;
        break;
      case 1:
        /* namespace attribute */
        namespaceURI = Attr_GET_NODE_VALUE(attr);
        if (PyUnicode_AS_UNICODE(Attr_GET_NODE_NAME(attr))[5] == ':') {
          /* xmlns:foo = 'namespaceURI' */
          prefix = Attr_GET_LOCAL_NAME(attr);
        } else {
          /* xmlns = 'namespaceURI' */
          prefix = Py_None;
        }
        Py_INCREF(prefix);

        if (PyUnicode_GET_SIZE(namespaceURI) == 0) {
          /* empty string; remove prefix binding */
          /* NOTE: in XML Namespaces 1.1 it would be possible to do this
             for all prefixes, for now just the default namespace */
          if (prefix == Py_None) {
            namespaceURI = Py_None;
          }
        }
        break;
      default:
        return -1;
      }

      /* add the declaration if prefix is not already defined */
      if (namespaceURI != Py_None && PyDict_GetItem(nss, prefix) == NULL) {
        if (PyDict_SetItem(nss, prefix, namespaceURI) < 0) {
          Py_DECREF(prefix);
          return -1;
        }
      }
      Py_DECREF(prefix);
    }
  }

  if (Node_GET_PARENT(node)) {
    res = get_all_ns_domlette(Node_GET_PARENT(node), nss);
  }

  return res;
}

Py_LOCAL(PyObject *)
seek_nss_domlette(NodeObject *node, PyObject *nss)
{
  Py_ssize_t i;
  PyObject *key, *attr;

  if (Element_Check(node)) {
    PyObject *prefix;

    /* get the prefix */
    prefix = get_prefix(Element_GET_NODE_NAME(node));
    if (prefix == NULL) return NULL;

    /* don't replace existing ns decls */
    if (PyDict_GetItem(nss, prefix) == NULL) {
      if (PyDict_SetItem(nss, prefix, Element_GET_NAMESPACE_URI(node)) < 0) {
        Py_DECREF(prefix);
        return NULL;
      }
    }
    Py_DECREF(prefix);

    /* now process this element's attributes */
    i = 0;
    while (PyDict_Next(Element_GET_ATTRIBUTES(node), &i, &key, &attr)) {
      PyObject *namespaceURI, *prefix;

      /* get the prefix/namespaceURI pair to add */
      namespaceURI = Attr_GET_NAMESPACE_URI(attr);
      switch (PyObject_RichCompareBool(namespaceURI, g_xmlnsNamespace, Py_EQ)) {
      case 0:
        /* normal attribute */
        prefix = get_prefix(Attr_GET_NODE_NAME(attr));
        if (prefix == NULL) return NULL;
        break;
      case 1:
        /* namespace attribute */
        namespaceURI = Attr_GET_NODE_VALUE(attr);
        if (PyUnicode_AS_UNICODE(Attr_GET_NODE_NAME(attr))[5] == ':') {
          /* xmlns:foo = 'namespaceURI' */
          prefix = Attr_GET_LOCAL_NAME(attr);
        } else {
          /* xmlns = 'namespaceURI' */
          prefix = Py_None;
        }
        Py_INCREF(prefix);

        if (PyUnicode_GET_SIZE(namespaceURI) == 0) {
          /* empty string; remove prefix binding */
          /* NOTE: in XML Namespaces 1.1 it would be possible to do this
             for all prefixes, for now just the default namespace */
          if (prefix == Py_None) {
            namespaceURI = Py_None;
          }
        }
        break;
      default:
        return NULL;
      }

      /* add the declaration if prefix is not already defined */
      if (PyDict_GetItem(nss, prefix) == NULL) {
        if (PyDict_SetItem(nss, prefix, namespaceURI) < 0) {
          Py_DECREF(prefix);
          return NULL;
        }
      }
      Py_DECREF(prefix);
    }
  } else if (!Document_Check(node)) {
    /* non-container node */
    return nss;
  }

  for (i = 0; i < ContainerNode_GET_COUNT(node); i++) {
    NodeObject *child = ContainerNode_GET_CHILD(node, i);
    if (Element_Check(child)) {
      if (seek_nss_domlette(child, nss) == NULL) {
        return NULL;
      }
    }
  }

  return nss;
}

/** DOM API implementation ********************************************/

Py_LOCAL(int)
get_all_ns_dom(PyObject *node, PyObject *nss)
{
  int res = 0;
  PyObject *obj;
  long nodeType;
  PyObject *tuple;

  obj = PyObject_GetAttrString(node, "nodeType");
  if (obj == NULL) {
    return -1;
  }
  nodeType = PyInt_AsLong(obj);
  Py_DECREF(obj);
  if (PyErr_Occurred()) {
    return -1;
  }

  if (nodeType == ELEMENT_NODE) {
    PyObject *namespaceURI, *prefix;
    PyObject *sequence;
    int i;

    /* add the element's namespace declaration */
    namespaceURI = PyObject_GetAttrString(node, "namespaceURI");
    namespaceURI = XmlString_FromObjectInPlace(namespaceURI);
    prefix = PyObject_GetAttrString(node, "prefix");
    prefix = XmlString_FromObjectInPlace(prefix);
    if (namespaceURI == NULL || prefix == NULL) {
      Py_XDECREF(namespaceURI);
      Py_XDECREF(prefix);
      return -1;
    }

    /* add the declaration if prefix is not already defined */
    if (PyDict_GetItem(nss, prefix) == NULL) {
      if (PyDict_SetItem(nss, prefix, namespaceURI) == -1) {
        Py_DECREF(namespaceURI);
        Py_DECREF(prefix);
        return -1;
      }
    }
    Py_DECREF(namespaceURI);
    Py_DECREF(prefix);

    /* now process this element's attributes */
    obj = PyObject_GetAttrString(node, "attributes");
    if (obj == NULL) {
      return -1;
    }

    sequence = PyObject_CallMethod(obj, "values", NULL);
    Py_DECREF(obj);
    if (sequence == NULL) {
      return -1;
    }

    tuple = PySequence_Tuple(sequence);
    Py_DECREF(sequence);
    if (tuple == NULL) {
      return -1;
    }

    for (i = 0; i < PyTuple_GET_SIZE(tuple); i++) {
      PyObject *attr = PyTuple_GET_ITEM(tuple, i);
      if (attr == NULL) {
        Py_DECREF(tuple);
        return -1;
      }

      namespaceURI = PyObject_GetAttrString(attr, "namespaceURI");
      namespaceURI = XmlString_FromObjectInPlace(namespaceURI);
      prefix = PyObject_GetAttrString(attr, "prefix");
      prefix = XmlString_FromObjectInPlace(prefix);
      if (namespaceURI == NULL || prefix == NULL) {
        Py_XDECREF(namespaceURI);
        Py_XDECREF(prefix);
        Py_DECREF(tuple);
        return -1;
      }

      /* get the prefix/namespaceURI pair to add */
      switch (PyObject_RichCompareBool(namespaceURI, g_xmlnsNamespace,
                                       Py_EQ)) {
      case 0:
        /* normal attribute */
        break;
      case 1:
        /* namespace attribute */
        Py_DECREF(namespaceURI);
        namespaceURI = PyObject_GetAttrString(attr, "value");
        namespaceURI = XmlString_FromObjectInPlace(namespaceURI);
        if (namespaceURI == NULL) {
          Py_DECREF(prefix);
          Py_DECREF(tuple);
          return -1;
        }
        if (prefix != Py_None) {
          /* xmlns:foo = 'namespaceURI'; prefix='xmlns' */
          Py_DECREF(prefix);
          prefix = PyObject_GetAttrString(attr, "localName");
          prefix = XmlString_FromObjectInPlace(prefix);
          if (prefix == NULL) {
            Py_DECREF(namespaceURI);
            Py_DECREF(tuple);
            return -1;
          }
        }
        if (PyUnicode_GET_SIZE(namespaceURI) == 0) {
          /* empty string; remove prefix binding */
          /* NOTE: in XML Namespaces 1.1 it would be possible to do this
             for all prefixes, for now just the default namespace */
          if (prefix == Py_None) {
            Py_DECREF(namespaceURI);
            Py_INCREF(Py_None);
            namespaceURI = Py_None;
          }
        }
        break;
      default:
        Py_DECREF(namespaceURI);
        Py_DECREF(prefix);
        Py_DECREF(tuple);
        return -1;
      }

      /* add the declaration if prefix is not already defined */
      if (namespaceURI != Py_None && PyDict_GetItem(nss, prefix) == NULL) {
        if (PyDict_SetItem(nss, prefix, namespaceURI) == -1) {
          Py_DECREF(namespaceURI);
          Py_DECREF(prefix);
          Py_DECREF(tuple);
          return -1;
        }
      }

      Py_DECREF(namespaceURI);
      Py_DECREF(prefix);
    }

    Py_DECREF(tuple);
  }

  if (nodeType == ATTRIBUTE_NODE)
    obj = PyObject_GetAttrString(node, "ownerElement");
  else
    obj = PyObject_GetAttrString(node, "parentNode");
  if (obj == NULL) {
    return -1;
  }
  else if (obj != Py_None) {
    res = get_all_ns_dom(obj, nss);
  }
  Py_DECREF(obj);

  return res;
}

Py_LOCAL(PyObject *)
seek_nss_dom(PyObject *node, PyObject *nss)
{
  PyObject *obj, *tuple;
  long nodeType;
  int i;

  obj = PyObject_GetAttrString(node, "nodeType");
  if (obj == NULL) {
    return NULL;
  }
  nodeType = PyInt_AsLong(obj);
  Py_DECREF(obj);
  if (PyErr_Occurred()) {
    return NULL;
  }

  if (nodeType == ELEMENT_NODE) {
    /* don't add ns decl for default namespace as it is initially defined */
    PyObject *namespaceURI, *prefix;
    PyObject *sequence;

    namespaceURI = PyObject_GetAttrString(node, "namespaceURI");
    namespaceURI = XmlString_FromObjectInPlace(namespaceURI);
    prefix = PyObject_GetAttrString(node, "prefix");
    prefix = XmlString_FromObjectInPlace(prefix);
    if (namespaceURI == NULL || prefix == NULL) {
      Py_XDECREF(namespaceURI);
      Py_XDECREF(prefix);
      return NULL;
    }

    /* don't replace existing ns decls */
    if (PyDict_GetItem(nss, prefix) == NULL) {
      if (PyDict_SetItem(nss, prefix, namespaceURI) == -1) {
        Py_DECREF(namespaceURI);
        Py_DECREF(prefix);
        return NULL;
      }
    }

    Py_DECREF(namespaceURI);
    Py_DECREF(prefix);

    /* now process this element's attributes */
    obj = PyObject_GetAttrString(node, "attributes");
    if (obj == NULL) {
      return NULL;
    }

    sequence = PyObject_CallMethod(obj, "values", NULL);
    Py_DECREF(obj);
    if (sequence == NULL) {
      return NULL;
    }

    tuple = PySequence_Tuple(sequence);
    Py_DECREF(sequence);
    if (tuple == NULL) {
      return NULL;
    }

    for (i = 0; i < PyTuple_GET_SIZE(tuple); i++) {
      PyObject *attr = PyTuple_GET_ITEM(tuple, i);
      if (attr == NULL) {
        Py_DECREF(tuple);
        return NULL;
      }

      namespaceURI = PyObject_GetAttrString(attr, "namespaceURI");
      namespaceURI = XmlString_FromObjectInPlace(namespaceURI);
      prefix = PyObject_GetAttrString(attr, "prefix");
      prefix = XmlString_FromObjectInPlace(prefix);
      if (namespaceURI == NULL || prefix == NULL) {
        Py_XDECREF(namespaceURI);
        Py_XDECREF(prefix);
        Py_DECREF(tuple);
        return NULL;
      }

      /* get the prefix/namespaceURI pair to add */
      switch (PyObject_RichCompareBool(namespaceURI, g_xmlnsNamespace,
                                       Py_EQ)) {
      case 0:
        /* normal attribute */
        break;
      case 1:
        /* namespace attribute */
        Py_DECREF(namespaceURI);
        namespaceURI = PyObject_GetAttrString(attr, "value");
        namespaceURI = XmlString_FromObjectInPlace(namespaceURI);
        if (namespaceURI == NULL) {
          Py_DECREF(prefix);
          Py_DECREF(tuple);
          return NULL;
        }
        if (prefix != Py_None) {
          /* xmlns:foo = 'namespaceURI'; prefix='xmlns' */
          Py_DECREF(prefix);
          prefix = PyObject_GetAttrString(attr, "localName");
          prefix = XmlString_FromObjectInPlace(prefix);
          if (prefix == NULL) {
            Py_DECREF(namespaceURI);
            Py_DECREF(tuple);
            return NULL;
          }
        }
        if (PyUnicode_GET_SIZE(namespaceURI) == 0) {
          /* empty string; remove prefix binding */
          /* NOTE: in XML Namespaces 1.1 it would be possible to do this
             for all prefixes, for now just the default namespace */
          if (prefix == Py_None) {
            Py_DECREF(namespaceURI);
            Py_INCREF(Py_None);
            namespaceURI = Py_None;
          }
        }
        break;
      default:
        Py_DECREF(namespaceURI);
        Py_DECREF(prefix);
        Py_DECREF(tuple);
        return NULL;
      }

      /* add the declaration if prefix is not already defined */
      if (PyDict_GetItem(nss, prefix) == NULL) {
        if (PyDict_SetItem(nss, prefix, namespaceURI) == -1) {
          Py_DECREF(namespaceURI);
          Py_DECREF(prefix);
          Py_DECREF(tuple);
          return NULL;
        }
      }

      Py_DECREF(namespaceURI);
      Py_DECREF(prefix);
    }
    Py_DECREF(tuple);
  }

  /* process the children of this node */
  obj = PyObject_GetAttrString(node, "childNodes");
  if (obj == NULL) {
    return NULL;
  }

  tuple = PySequence_Tuple(obj);
  Py_DECREF(obj);
  if (tuple == NULL) {
    return NULL;
  }

  for (i = 0; i < PyTuple_GET_SIZE(tuple); i++) {
    if (seek_nss_dom(PyTuple_GET_ITEM(tuple, i), nss) == NULL) {
      Py_DECREF(tuple);
      return NULL;
    }
  }
  Py_DECREF(tuple);

  return nss;
}

/** Public Methods ****************************************************/

PyObject *Domlette_GetNamespaces(NodeObject *node)
{
  PyObject *nss;
  PyObject *prefix;

  nss = PyDict_New();
  if (nss == NULL) return NULL;

  /* add the XML namespace */
  prefix = XmlString_FromASCII("xml");
  if (prefix == NULL) {
    Py_DECREF(nss);
    return NULL;
  }
  if (PyDict_SetItem(nss, prefix, g_xmlNamespace) == -1) {
    Py_DECREF(nss);
    Py_DECREF(prefix);
    return NULL;
  }
  Py_DECREF(prefix);

  if (get_all_ns_domlette(node, nss) == -1) {
    Py_DECREF(nss);
    return NULL;
  }

  /* don't expose the implied default namespace */
  if (PyDict_GetItem(nss, Py_None) == Py_None) {
    if (PyDict_DelItem(nss, Py_None) == -1) {
      Py_DECREF(nss);
      return NULL;
    }
  }

  return nss;
}

char GetAllNs_doc[] = \
"GetAllNs(node) -> dict\n\
\n\
Get all of the namespaces defined in scope of this node.";

PyObject *Domlette_GetAllNs(PyObject *self, PyObject *args)
{
  PyObject *node;
  PyObject *nss;
  PyObject *prefix;
  int result;

  if (!PyArg_ParseTuple(args, "O:GetAllNs", &node))
    return NULL;

  nss = PyDict_New();
  if (nss == NULL) return NULL;

  /* add the XML namespace */
  prefix = XmlString_FromASCII("xml");
  if (prefix == NULL) {
    Py_DECREF(nss);
    return NULL;
  }
  if (PyDict_SetItem(nss, prefix, g_xmlNamespace) == -1) {
    Py_DECREF(nss);
    Py_DECREF(prefix);
    return NULL;
  }
  Py_DECREF(prefix);

  if (Node_Check(node))
    result = get_all_ns_domlette((NodeObject *) node, nss);
  else
    result = get_all_ns_dom(node, nss);

  if (result == -1) {
    Py_DECREF(nss);
    return NULL;
  }

  /* don't expose the implied default namespace */
  if (PyDict_GetItem(nss, Py_None) == Py_None) {
    if (PyDict_DelItem(nss, Py_None) == -1) {
      Py_DECREF(nss);
      return NULL;
    }
  }

  return nss;
}

char SeekNss_doc[] = \
"SeekNss(node) -> dict\n\
\n\
Traverses the tree to seek an approximate set of defined namespaces.";

PyObject *Domlette_SeekNss(PyObject *self, PyObject *args)
{
  PyObject *node;
  PyObject *nss;
  PyObject *result;

  if (!PyArg_ParseTuple(args, "O:SeekNss", &node))
    return NULL;

  nss = PyDict_New();
  if (nss == NULL) return NULL;

  if (Node_Check(node))
    result = seek_nss_domlette((NodeObject *)node, nss);
  else
    result = seek_nss_dom(node, nss);

  if (result == NULL) {
    Py_DECREF(nss);
  }
  else {
    /* don't expose the implied default namespace */
    if (PyDict_GetItem(nss, Py_None) == Py_None) {
      if (PyDict_DelItem(nss, Py_None) == -1) {
        Py_DECREF(nss);
        return NULL;
      }
    }
  }

  return result;
}
