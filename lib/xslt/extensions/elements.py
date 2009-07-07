########################################################################
# amara/xslt/extensions/elements.py

from amara import tree
from amara.namespaces import EXTENSION_NAMESPACE
from amara.xslt.tree import xslt_element, content_model, attribute_types

__all__ = ('extension_namespaces', 'extension_functions', 'extension_elements')

RESERVED_NAMESPACE = u'http://xmlns.4suite.org/reserved'

class dump_keys_element(xslt_element):
    """
    f:dump-keys reports the XSLT keys that have been defined, and the
    nodes they identify, for the document that owns the context node.
    Keys will only be reported if key() has been evaluated prior to
    the instantiation of this element. The key() evaluation must have
    been performed with a context node that is from the same document
    as the context node for this element.

    This extension element is useful for debugging.

    By default, the key data is exposed as nodes with this structure:

    <zz:KeyDump xmlns:zz="%s">
      <zz:Key name="keyName">
        <zz:MatchSet value="keyUseValue">
          (representation of nodes matched by the key)
        </zz:MatchSet>
        ...
      </zz:Key>
      ...
    </zz:KeyDump>

    zz:Key elements will be in random order.
    zz:MatchSet elements will be in document order.

    The node representation will be a copy of each of the nodes,
    except for attributes. Attribute nodes matched by the key will
    manifest as comment nodes with the content "Attribute: name=value".

    If raw="yes", the keys will be emitted as a stylesheet message
    (as if via xsl:message) and the format will be their Python repr()
    representation.

    If force-update="yes" all keys will be computed on all documents
    that have been loaded into the processor.

    4Suite evaluates keys lazily, which means that you could have
    situations where f:dump-keys returns unexpected empty results
    because the key of interest has not yet been invoked.
    """ % RESERVED_NAMESPACE

    content_model = content_model.empty
    attribute_types = {
        'raw': attribute_types.yesno_avt(
            default='no',
            description="Present keys in a compact non-XML format"),
        'force-update': attribute_types.yesno_avt(
            default='no',
            description="Force evaluation of all keys on all loaded documents"),
        }

    def instantiate(self, context):
        if self._force_update.evaluate(context):
            context.update_keys()
        doc = context.node.xml_root
        #param = (EXTENSION_NAMESPACE, 'indices')
        #if param in processor.extension_parameters:
        #    for k, v in processor.extension_parameters[param].items():
        #        # Dummy to xsl:key storage format
        #        xkeys[(None, k)] = v
        if self._raw.evaluate(context):
            lines = []
            for key_name in sorted(context.keys):
                lines.append('Key: %r' % key_name)
                string_values = context.keys[key_name][doc]
                for string_value in sorted(string_values, key=unicode):
                    nodes = string_values[string_value]
                    lines.append('  %r=%r' % (string_value, nodes))
            context.message('\n'.join(lines))
        else:
            context.start_element(u'zz:KeyDump', RESERVED_NAMESPACE)
            for key_name in sorted(context.keys):
                context.start_element(u'zz:Key', RESERVED_NAMESPACE)
                context.attribute(u'name', key_name[1])
                string_values = context.keys[key_name][doc]
                for string_value in sorted(string_values, key=unicode):
                    context.start_element(u'zz:MatchSet', RESERVED_NAMESPACE)
                    context.attribute(u'value', string_value)
                    for node in string_values[string_value]:
                        if isinstance(node, tree.attribute):
                            data = u"Attribute: %s=%s" % (node.xml_qname,
                                                          node.xml_value)
                            context.comment(data)
                        else:
                            context.copy_node(node)
                    context.end_element(u'zz:MatchSet', RESERVED_NAMESPACE)
                context.end_element(u'zz:Key', RESERVED_NAMESPACE)
            context.end_element(u'zz:KeyDump', RESERVED_NAMESPACE)
        return

## XSLT Extension Module Interface ####################################

extension_namespaces = {
    EXTENSION_NAMESPACE: 'f',
    }

extension_functions = {
    }

extension_elements = {
    (EXTENSION_NAMESPACE, 'dump-keys'): dump_keys_element,
    }
