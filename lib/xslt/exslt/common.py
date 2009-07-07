########################################################################
# amara/xslt/exslt/common.py
"""
EXSLT 2.0 - Common (http://www.exslt.org/exsl/index.html)
"""
from amara import tree
from amara.writers import outputparameters
from amara.xpath import datatypes
from amara.xslt.tree import xslt_element, content_model, attribute_types

EXSL_COMMON_NS = "http://exslt.org/common"

def nodeset_function(context, arg0):
    """
    The purpose of the exsl:node-set function is to return a node-set from a
    result tree fragment. If the argument is a node-set already, it is simply
    returned as is. If the argument to exsl:node-set is not a node-set or a
    result tree fragment, then it is converted to a string as by the string()
    function, and the function returns a node-set consisting of a single text
    node with that string value.

    The exsl:node-set function does not have side-effects: the result tree
    fragment used as an argument is still available as a result tree fragment
    after it is passed as an argument to exsl:node-set.
    """
    obj = arg0.evaluate(context)
    if not isinstance(obj, datatypes.nodeset):
        if not isinstance(obj, tree.entity):
            obj = (tree.text(datatypes.string(obj)),)
        obj = datatypes.nodeset([obj])
    return obj


def object_type_function(context, arg0):
    """
    The exsl:object-type function returns a string giving the type of the
    object passed as the argument. The possible object types are: 'string',
    'number', 'boolean', 'node-set', 'RTF' or 'external'.
    """
    obj = arg0.evaluate(context)
    if isinstance(obj, datatypes.nodeset):
        tp_name = 'node-set'
    elif isinstance(obj, datatypes.string):
        tp_name =  'string'
    elif isinstance(obj, datatypes.number):
        tp_name = 'number'
    elif isinstance(obj, datatypes.boolean):
        tp_name = 'boolean'
    elif isinstance(obj, tree.entity):
        tp_name = 'RTF'
    else:
        tp_name = 'external'
    return datatypes.string(tp_name)


class document_element(xslt_element):
    """
    For the basic specification, see:
    http://www.exslt.org/exsl/elements/document/index.html
    The only URI scheme supported by 4Suite currently is 'file:'
    Security note:
    As a precaution, if you try to overwrite an existing file, it will be
    saved to a temporary file (there will be a warning with the file name).
    If this this precaution fails, the instruction will abort.  You can
    override this precaution, always allowing the function to overwrite
    a document by using the f:overwrite-okay extension attribute.
    """

    content_model = content_model.template
    attribute_types = {
        'href' : attribute_types.uri_reference_avt(required=True),
        'method' : attribute_types.qname_avt(),
        'version' : attribute_types.nmtoken_avt(),
        'encoding' : attribute_types.string_avt(),
        'omit-xml-declaration' : attribute_types.yesno_avt(),
        'standalone' : attribute_types.yesno_avt(),
        'doctype-public' : attribute_types.string_avt(),
        'doctype-system' : attribute_types.string_avt(),
        'cdata-section-elements' : attribute_types.qnames_avt(),
        'indent' : attribute_types.yesno_avt(),
        'media-type' : attribute_types.string_avt(),
        'f:byte-order-mark' : attribute_types.yesno_avt(
            default='no',
            description=("Whether to force output of a byte order mark (BOM). "
                         "Usually used to generate a UTF-8 BOM.  Do not use "
                         "this unless you're sure you know what you're doing")),
        'f:overwrite-safeguard' : attribute_types.yesno_avt(
            default='no',
            description=("Whether or not to make backup copies of any file "
                         "before it's overwritten.")),
        }

    def setup(self):
        self._output_parameters = outputparameters.outputparameters()
        return

    def instantiate(self, context):
        context.instruction, context.namespaces = self, self.namespaces

        # this uses attributes directly from self
        self._output_parameters.avtParse(self, context)
        href = self._href.evaluate(context)

        if Uri.IsAbsolute(href):
            uri = href
        else:
            try:
                uri = Uri.Absolutize(href,
                  Uri.OsPathToUri(processor.writer.getStream().name))
            except Exception, e:
                raise XsltRuntimeException(
                        ExsltError.NO_EXSLTDOCUMENT_BASE_URI,
                        context.currentInstruction, href)
        path = Uri.UriToOsPath(uri)
        if (self.attributes.get((FT_EXT_NAMESPACE, 'overwrite-safeguard') == u'yes')
            and os.access(path, os.F_OK)):
            # Kick in the safety measures
            # FIXME: Security hole.  Switch to the mkstemp as soon as we
            #   mandate Python 2.3 mnimum
            savefile = tempfile.mktemp('', os.path.split(path)[-1]+'-')
            processor.warn("The file you are trying to create with"
                           " exsl:document already exists.  As a safety"
                           " measure it will be copied to a temporary file"
                           " '%s'." % savefile)  #FIXME: l10n
            try:
                shutil.copyfile(path, savefile)
            except:
                raise XsltRuntimeException(
                    ExsltError.ABORTED_EXSLDOCUMENT_OVERWRITE,
                    context.currentInstruction, path, savefile)
        try:
            stream = open(path, 'w')
        except IOError:
            dirname = os.path.dirname(path)
            # Should we also check base path writability with os.W_OK?
            if not os.access(dirname, os.F_OK):
                os.makedirs(dirname)
                stream = open(path, 'w')
            else:
                raise

        processor.addHandler(self._output_parameters, stream)
        try:
            self.processChildren(context, processor)
        finally:
            processor.removeHandler()
            stream.close()
        return

## XSLT Extension Module Interface ####################################

extension_namespaces = {
    EXSL_COMMON_NS : 'exsl',
    }

extension_functions = {
    (EXSL_COMMON_NS, 'node-set'): nodeset_function,
    (EXSL_COMMON_NS, 'object-type'): object_type_function,
    }

extension_elements = {
    (EXSL_COMMON_NS, 'document'): document_element,
    }
