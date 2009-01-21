########################################################################
# amara/xslt/reader/attribute_types.py
"""
Classes that support validation and evaluation of attribute values in
XSLT instruction elements
"""

#from amara import TranslateMessage as _
from gettext import gettext as _

import cStringIO, traceback

#from amara.xpath import RuntimeException as XPathRuntimeException
from amara.xpath import datatypes, parser
from amara.xpath.parser import _parse as parse_xpath

from amara.xslt import XsltError, XsltStaticError, XsltRuntimeError
from amara.xslt.xpatterns import _parse as parse_xpattern

from amara.namespaces import XML_NAMESPACE, XMLNS_NAMESPACE
from amara.lib.xmlstring import isqname, splitqname
from amara.xslt.expressions.avt import avt_expression


class attribute_type(object):

    __slots__ = ('required', 'default', 'description')

    display = 'unknown'

    def __init__(self, required=False, default=None, description=''):
        self.required = required
        self.default = default
        self.description = description
        return

    def __str__(self):
        return self.display

    def prepare(self, element, value):
        if value is None:
            return self.default
        return value

    # `reprocess` is used in avt_expression
    reprocess = prepare

    def validate(self, validation):
        return True


class _avt_constant(avt_expression):
    # optimization hook
    constant = True

    def __init__(self, element, attribute_type, value):
        self._format = attribute_type.reprocess(element, value)
        self._args = None

    def __str__(self):
        return repr(self._format)

    def __nonzero__(self):
        return self._format is not None


class _avt_wrapper(avt_expression):
    __slots__ = ('constant', '_element', '_attribute_type')
    def __init__(self, element, attribute_type, value):
        avt_expression.__init__(self, value)
        self._element = element
        self._attribute_type = attribute_type
        self.constant = not self._args

    def evaluate_as_string(self, context):
        result = avt_expression.evaluate_as_string(self, context)
        return self._attribute_type.reprocess(self._element, result)
    evaluate = evaluate_as_string


class choice(attribute_type):

    __slots__ = ('values',)

    def __init__(self, values, required=False, default=None, description=''):
        attribute_type.__init__(self, required, default, description)
        self.values = values
        return

    def prepare(self, element, value):
        if value is None:
            return self.default
        if value not in self.values:
            # check for an `attribute_type` instance
            for allowed in self.values:
                if isinstance(allowed, self.__class__):
                    try:
                        allowed.prepare(element, value)
                    except:
                        pass
                    else:
                        break
            else:
                # if we get here it is an error
                raise XsltError(XsltError.INVALID_ATTR_CHOICE, value=value)
        return value
    reprocess = prepare

    def __str__(self):
        return ' | '.join('"' + v + '"' for v in self.values)


class avt:

    def __str__(self):
        return '{ %s }' % self.display

    def prepare(self, element, value):
        if value is None:
            return _avt_constant(element, self, self.default)
        elif '{' not in value and '}' not in value:
            return _avt_constant(element, self, value)
        try:
            return _avt_wrapper(element, self, value)
        except XsltError, error:
            # an error from the AVT parser
            raise XsltError(XsltError.INVALID_AVT, value=value,
                            baseuri=element.baseUri, line=element.lineNumber,
                            col=element.columnNumber, msg=str(error))


class choice_avt(avt, choice):

    def __str__(self):
        return '{ %s }' % choice.__str__(self)


class any_avt(avt, attribute_type):
    display = _('any avt')


class string(attribute_type):
    display = _('string')


class string_avt(avt, string):
    pass


class char(attribute_type):
    """
    A string value with a length of one
    """
    display = _('char')

    def prepare(self, element, value):
        if value is None:
            return self.default
        if len(value) > 1:
            raise XsltError(XsltError.INVALID_CHAR_ATTR, value=value)
        return value
    reprocess = prepare


class char_avt(avt, char):
    pass


class number(attribute_type):
    display = _('number')

    def prepare(self, element, value):
        if value is None:
            return self.default
        try:
            return float(value or self.default)
        except:
            raise XsltError(XsltError.INVALID_NUMBER_ATTR, value=value)
    reprocess = prepare


class number_avt(avt, number):
    reprocess = number.prepare


class uri_reference(attribute_type):
    display = _('uri-reference')

    def prepare(self, element, value):
        if value is None:
            return self.default
        return value
    reprocess = prepare


class uri_reference_avt(avt, uri_reference):
    pass


class namespace_uri(uri_reference):
    def prepare(self, element, value):
        if value is None:
            return self.default
        if value in (XML_NAMESPACE, XMLNS_NAMESPACE):
            raise XsltError(XsltError.INVALID_NS_URIREF_ATTR, value=value)
        return value
    reprocess = prepare


class namespace_uri_avt(avt, namespace_uri):
    pass


class id(attribute_type):
    display = _('id')

    def prepare(self, element, value):
        if value is None:
            return self.default
        if not value:
            raise XsltError(XsltError.INVALID_ID_ATTR, value=value)
        return value
    reprocess = prepare


class id_avt(avt, id):
    pass


class qname(attribute_type):
    display = _('qname')

    def prepare(self, element, value):
        if value is None:
            if self.default is None:
                return None
            value = self.default
        elif not isqname(value):
            raise XsltError(XsltError.INVALID_QNAME_ATTR, value=value)

        prefix, local = splitqname(value)
        if prefix:
            try:
                namespace = element.namespaces[prefix]
            except KeyError:
                raise XsltRuntimeException(XsltError.UNDEFINED_PREFIX,
                                           elem=element, prefix=prefix)
        else:
            namespace = None
        return (namespace, local)
    reprocess = prepare


class qname_avt(avt, qname):
    pass


class raw_qname(qname):

    def prepare(self, element, value):
        if value is None:
            if self.default is None:
                return None
            value = self.default
        elif not isqname(value):
            raise XsltError(XsltError.INVALID_QNAME_ATTR, value=value)
        return splitqname(value)
    reprocess = prepare


class raw_qname_avt(avt, raw_qname):
    pass


class ncname(attribute_type):
    display = _('ncname')

    def prepare(self, element, value):
        if value is None:
            return self.default
        if not value:
            raise XsltError(XsltError.INVALID_NCNAME_ATTR, value=value)
        if ':' in value:
            raise XsltError(XsltError.INVALID_NCNAME_ATTR, value=value)
        return value
    reprocess = prepare


class ncname_avt(avt, ncname):
    pass


class prefix(attribute_type):
    display = _('prefix')

    def prepare(self, element, value):
        if value is None:
            return self.default
        if not value:
            raise XsltError(XsltError.INVALID_PREFIX_ATTR, value=value)
        if ':' in value:
            raise XsltError(XsltError.INVALID_PREFIX_ATTR, value=value)
        if value == '#default':
            value = None
        return value
    reprocess = prepare


class prefix_avt(avt, prefix):
    pass


class nmtoken(attribute_type):
    display = _('nmtoken')

    def prepare(self, element, value):
        if value is None:
            return self.default
        if not value:
            raise XsltError(XsltError.INVALID_NMTOKEN_ATTR, value=value)
        return value
    reprocess = prepare


class nmtoken_avt(avt, nmtoken):
    pass


class qname_but_not_ncname(attribute_type):
    display = _('qname-but-not-ncname')

    def prepare(self, element, value):
        if value is None:
            if self.default is None:
                return None
            value = self.default
        elif not value:
            raise XsltError(XsltError.QNAME_BUT_NOT_NCNAME, value=value)

        try:
            index = value.index(':')
        except ValueError:
            raise XsltError(XsltError.QNAME_BUT_NOT_NCNAME, value=value)
        prefix, local = value[:index], value[index+1:]
        try:
            namespace = element.namespaces[prefix]
        except KeyError:
            raise XsltRuntimeException(XsltError.UNDEFINED_PREFIX,
                                       elem=element, prefix=prefix)
        return (namespace, local)
    reprocess = prepare


class token(attribute_type):
    """
    An attribute whose value is used as an XPath NameTest
    """
    display = _('token')

    def prepare(self, element, value):
        # a 'token' is really an XPath NameTest; '*' | NCName ':' '*' | QName
        # From XPath 1.0 section 2.3:
        #  if the QName does not have a prefix, then the namespace URI is null
        index = value.rfind(':')
        if index == -1:
            namespace = None
            local = value
        else:
            prefix = value[:index]
            local = value[index+1:]
            try:
                namespace = element.namespaces[prefix]
            except KeyError:
                raise XsltRuntimeException(XsltError.UNDEFINED_PREFIX,
                                       elem=element, prefix=prefix)
        return (namespace, local)
    reprocess = prepare


class token_avt(avt, token):
    pass


class expression_wrapper:

    def __init__(self, expression, element, original):
        self.expression = expression
        self.element = element
        self.original = original
        return

    def __nonzero__(self):
        # True if self.expression is not None, which is always the case
        # otherwise this instance would not exist!
        return True

    def __getattr__(self, attr):
        """Make this behave as if it was the expression object itself."""
        return getattr(self.expression, attr)

    # Provide the copy/pickle helpers so as to not get them from the
    # wrapped expression.
    def __getstate__(self):
        return (self.expression, self.element, self.original)

    def __setstate__(self, state):
        self.expression, self.element, self.original = state
        return

    def evaluate(self,context):
        try:
            return self.expression.evaluate(context)
        except XPathRuntimeException, e:
            import MessageSource
            e.message = MessageSource.EXPRESSION_POSITION_INFO % (
                self.element.baseUri, self.element.lineNumber,
                self.element.columnNumber, self.original, str(e))
            # By modifying the exception value directly, we do not need
            # to raise with that value, thus leaving the frame stack
            # intact (original traceback is displayed).
            raise
        except XsltError, e:
            import MessageSource
            e.message = MessageSource.XSLT_EXPRESSION_POSITION_INFO % (
                str(e), self.original)
            # By modifying the exception value directly, we do not need
            # to raise with that value, thus leaving the frame stack
            # intact (original traceback is displayed).
            raise
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            import MessageSource
            tb = cStringIO.StringIO()
            tb.write("Lower-level traceback:\n")
            traceback.print_exc(1000, tb)
            raise RuntimeError(MessageSource.EXPRESSION_POSITION_INFO % (
                self.element.baseUri, self.element.lineNumber,
                self.element.columnNumber, self.original, tb.getvalue()))

class expression(attribute_type):
    """
    An attribute whose value is used as an XPath expression
    """
    display = _('expression')

    def prepare(self, element, value):
        if value is None:
            if self.default is None:
                return None
            value = self.default
        try:
            return parse_xpath(value)
        except SyntaxError, error:
            raise XsltError(XsltError.INVALID_EXPRESSION, value=value,
                            baseuri=element.baseUri, line=element.lineNumber,
                            col=element.columnNumber, msg=str(error))

class nodeset_expression(expression):
    display = _('nodeset-expression')

class string_expression(expression):
    display = _('string-expression')

class number_expression(expression):
    display = _('number-expression')

class boolean_expression(expression):
    display = _('boolean-expression')


class pattern(attribute_type):
    """
    An attribute whose value is used as an XPattern expression
    """
    display = _('pattern')

    def prepare(self, element, value):
        if value is None:
            if self.default:
                value = self.default
            else:
                return None
        try:
            return parse_xpattern(value)
        except XsltError, err:
            if err.__class__ is XsltError:
                XsltRuntimeError.update_error(err, element)
            raise

class tokens(token):
    """
    A whitespace separated list of tokens (see Token for description of a token)
    """
    display = _('tokens')

    def prepare(self, element, value):
        if value is None:
            return []
        tokens = []
        for value in value.split():
            prepared = token.prepare(self, element, value)
            tokens.append(prepared)
        return tokens
    reprocess = prepare

class tokens_avt(avt, tokens):
    pass


class qnames(qname):
    """
    A whitespace separated list of qnames (see QName for description of a qname)
    """
    display = _('qnames')

    def prepare(self, element, value):
        if value is None:
            return []
        qnames = []
        for value in value.split():
            prepared = qname.prepare(self, element, value)
            qnames.append(prepared)
        return qnames
    reprocess = prepare

class qnames_avt(avt, qnames):
    pass


class prefixes(prefix):
    """
    A whitespace separated list of prefixes (see Prefix for more information)
    """
    display = _('prefixes')

    def prepare(self, element, value):
        if value is None:
            return []
        prefixes = []
        for value in value.split():
            prepared = prefix.prepare(self, element, value)
            prefixes.append(prepared)
        return prefixes
    reprocess = prepare

class prefixes_avt(avt, prefixes):
    pass


class yesno(attribute_type):

    display = '"yes" | "no"'

    def prepare(self, element, value):
        if value is None:
            return self.default and self.default == 'yes'
        elif value not in ['yes', 'no']:
            raise XsltError(XsltError.INVALID_ATTR_CHOICE, value=value)#, str(self))
        return value == 'yes'
    reprocess = prepare

class yesno_avt(avt, yesno):
    pass

