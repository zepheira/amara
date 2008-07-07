########################################################################
# amara/xpath/expressions/__init__.py
"""
The implementation of parsed XPath expression tokens.
"""

from amara._xmlstring import splitqname
from amara.xpath import XPathError
from amara.xpath import datatypes, expressions

class literal(expressions.expression):
    """
    An object representing a string literal expression
    (XPath 1.0 grammar production 29: Literal)
    """

    def __init__(self, literal):
        self._literal = literal

    def compile_as_boolean(self, compiler):
        if self._literal:
            value = datatypes.boolean.TRUE
        else:
            value = datatypes.boolean.FALSE
        compiler.emit('LOAD_CONST', value)
        return

    def compile_as_number(self, compiler):
        try:
            value = datatypes.number(self._literal)
        except ValueError:
            value = datatypes.number.NaN
        compiler.emit('LOAD_CONST', value)
        return

    def compile_as_string(self, compiler):
        try:
            value = datatypes.string(self._literal)
        except ValueError:
            value = datatypes.string.EMPTY
        compiler.emit('LOAD_CONST', value)
        return

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)


class string_literal(literal):
    """
    An object representing a string literal expression
    (XPath 1.0 grammar production 29: Literal)
    """

    return_type = datatypes.string

    def __init__(self, literal):
        # FIXME - this constructor can go away once the BisonGen parser
        # is updated to use the non-quoted value as the `literal` argument.
        if literal[:1] in ("'", '"') and literal[:1] == literal[-1:]:
            literal = literal[1:-1]
        self._literal = literal

    compile = literal.compile_as_string

    def __str__(self):
        return '"%s"' % self._literal.replace('"', '\\"')


class number_literal(literal):
    """
    An object representing a numeric literal expression
    (XPath 1.0 grammar production 30: Number)
    """

    return_type = datatypes.number

    compile = literal.compile_as_number

    def __str__(self):
        return str(self._literal)


class variable_reference(expressions.expression):
    """
    An object representing a variable reference expression
    (XPath 1.0 grammar production 36: VariableReference)
    """
    def __init__(self, name):
        # FIXME - the slice of the name can go away once the BisonGen parser
        # is updated to use just the qualified name as the `name` argument.
        self._name = name[1:]
        return

    def compile(self, compiler):
        """
        Generates opcodes for the expression:

            context.variables[namespaceUri, localName]

        where `namespaceUri` is the URI bound to the prefix of the
        qualified name for the variable reference.
        """
        # Construct the expanded-name tuple
        prefix, local = splitqname(self._name)
        if prefix:
            try:
                namespace = compiler.namespaces[prefix]
            except KeyError:
                raise XPathError(XPathError.UNDEFINED_PREFIX, prefix=prefix)
        else:
            namespace = None
        if (namespace, local) not in compiler.variables:
            raise XPathError(XPathError.UNDEFINED_VARIABLE,
                             variable=self._name, key=(namespace, local))
        # Add the actual opcodes
        compiler.emit('LOAD_FAST', 'context')
        compiler.emit('LOAD_ATTR', 'variables')
        compiler.emit('LOAD_CONST', namespace)
        compiler.emit('LOAD_CONST', local)
        compiler.emit('BUILD_TUPLE', 2)
        compiler.emit('BINARY_SUBSCR')
        return

    def compile_as_nodeset(self, compiler):
        # Load the callable object
        compiler.emit('LOAD_CONST', datatypes.nodeset)
        # Build the argument(s)
        self.compile(compiler)
        compiler.emit('CALL_FUNCTION', 1)
        return

    def compile_iterable(self, compiler):
        self.compile(compiler)
        compiler.emit('GET_ITER')
        return

    def pprint(self, indent='', stream=None):
        print >> stream, indent + repr(self)

    def __str__(self):
        return '$' + self._name
