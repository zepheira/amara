########################################################################
# amara/xslt/extensions/functions.py

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

    attribute_types = {
        'raw': attribute_types.yesno_avt(
            default='no',
            description="Present keys in a compact non-XML format"),
        'force-update': attribute_types.yesno_avt(
            default='no',
            description="Force evaluation of all keys on all loaded documents"),
        }

    def instantiate(self, context):
        processor = context.processor
        if self._force_update.evaluate(context):
            context.transform.updateAllKeys(context, processor)

        doc = context.node.xml_root
        try:
            xkeys = processor.keys[doc]
        except KeyError:
            xkeys = {}
        param = (EXTENSION_NAMESPACE, 'indices')
        if param in processor.extensionParams:
            for k, v in processor.extensionParams[param].items():
                #Dummy to xsl:key storage format
                xkeys[(None, k)] = v

        if self._raw.evaluate(context):
            processor.xslMessage(repr(xkeys))
        else:
            context.start_element(u'zz:KeyDump', RESERVED_NAMESPACE)
            for k, v in xkeys.iteritems():
                context.start_element(u'zz:Key', RESERVED_NAMESPACE)
                context.attribute(u'name', k[1], EMPTY_NAMESPACE)
                for kk, vv in v.iteritems():
                    context.start_element(u'zz:MatchSet', RESERVED_NAMESPACE)
                    context.attribute(u'value', kk, EMPTY_NAMESPACE)
                    for node in vv:
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
