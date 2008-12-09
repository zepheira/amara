########################################################################
# amara/xpath/__init__.py
"""
XPath initialization and principal functions
"""

__all__ = [# global constants:
           # exception class:
           'XPathError',
           # XPath expression processing:
           #'Compile', 'Evaluate', 'SimpleEvaluate',
           # DOM preparation for XPath processing:
           #'NormalizeNode',
           'context'
           ]


# -- XPath exceptions --------------------------------------------------------

from amara import Error

class XPathError(Error):
    """
    Base class for exceptions specific to XPath processing
    """

    # internal or other unexpected errors
    INTERNAL = 1

    # syntax or other static errors
    SYNTAX             = 10
    UNDEFINED_VARIABLE = 11
    UNDEFINED_PREFIX   = 12
    UNDEFINED_FUNCTION = 13
    ARGCOUNT_NONE      = 14
    ARGCOUNT_ATLEAST   = 15
    ARGCOUNT_EXACT     = 16
    ARGCOUNT_ATMOST    = 17

    TYPE_ERROR         = 20

    NO_CONTEXT         = 30

    @classmethod
    def _load_messages(cls):
        from gettext import gettext as _
        return {
            # -- internal/unexpected errors --------------------------------
            XPathError.INTERNAL: _(
                'There is an internal bug in 4XPath.  Please make a post to '
                'the 4Suite mailing list to report this error message to the '
                'developers. Include platform details and info about how to '
                'reproduce the error. Info about the mailing list is at '
                'http://lists.4suite.org/mailman/listinfo/4suite.\n'
                'The error code to report is: %s'),

            # -- expression syntax errors ----------------------------------
            XPathError.SYNTAX: _(
                'XPath expression syntax error at line %(line)d, '
                'column %(column)d: %(text)s'),
            XPathError.UNDEFINED_VARIABLE: _(
                "Variable '%(variable)s' not declared"),
            XPathError.UNDEFINED_PREFIX: _(
                'Undefined namespace prefix: "%(prefix)s".'),
            XPathError.UNDEFINED_FUNCTION: _(
                'Undefined function: "%(function)s".'),
            XPathError.ARGCOUNT_NONE: _(
                '%(function)s() takes no arguments (%(total)d given)'),
            XPathError.ARGCOUNT_ATLEAST: _(
                '%(function)s() takes at least %(count)d arguments '
                '(%(total)d given)'),
            XPathError.ARGCOUNT_EXACT: _(
                '%(function)s() takes exactly %(count)d arguments '
                '(%(total)d given)'),
            XPathError.ARGCOUNT_ATMOST: _(
                '%(function)s() takes at most %(count)d arguments '
                '(%(total)d given)'),
            XPathError.TYPE_ERROR: _(
                "%(what)s must be '%(expected)s', not '%(actual)s'"),

            # -- evaluation errors -----------------------------------------
            XPathError.NO_CONTEXT: _(
                'An XPath Context object is required in order to evaluate an '
                'expression.'),
            }

# -- Additional setup --------------------------------------------------------

# -- Core XPath API ----------------------------------------------------------

#from Util import Compile, Evaluate, SimpleEvaluate, NormalizeNode

import types
import operator

from amara import tree
from amara.namespaces import XML_NAMESPACE
from amara.writers import writer, treewriter, stringwriter
from amara.xpath import extensions, parser

_writer_methods = operator.attrgetter(
    'start_document', 'end_document', 'start_element', 'end_element',
    'namespace', 'attribute', 'text', 'comment', 'processing_instruction')

class context(writer):
    """
    The context of an XPath expression
    """
    functions = extensions.extension_functions
    current_instruction = None

    def __init__(self, node, position=1, size=1,
                 variables=None, namespaces=None,
                 extmodules=(), extfunctions=None,
                 output_parameters=None):
        writer.__init__(self, output_parameters)
        self.node, self.position, self.size = node, position, size
        self.variables = {}
        if variables:
            self.variables.update(variables)
        self.namespaces = {'xml': XML_NAMESPACE}
        if namespaces:
            self.namespaces.update(namespaces)

        # This may get mutated during processing
        self.functions = self.functions.copy()
        # Search the extension modules for defined functions
        for module in extmodules:
            if module:
                if not isinstance(module, types.ModuleType):
                    module = __import__(module, {}, {}, ['ExtFunctions'])
                funcs = getattr(module, 'extension_functions', None)
                if funcs:
                    self.functions.update(funcs)
        # Add functions given directly
        if extfunctions:
            self.functions.update(extfunctions)
        self._writers = []
        return

    def __repr__(self):
        ptr = id(self)
        if ptr < 0: ptr += 0x100000000L
        return "<Context at 0x%x: Node=%s, Postion=%d, Size=%d>" % (
            ptr, self.node, self.position, self.size)

    def push_writer(self, writer):
        self._writers.append(writer)
        # copy writer methods onto `self` for performance
        (self.start_document, self.end_document, self.start_element,
         self.end_element, self.namespace, self.attribute, self.text,
         self.comment, self.processing_instruction) = _writer_methods(writer)
        # begin processing
        writer.start_document()
        return

    def push_tree_writer(self, base_uri):
        writer = treewriter.treewriter(self.output_parameters, base_uri)
        self.push_writer(writer)

    def push_string_writer(self, errors=True):
        writer = stringwriter.stringwriter(self.output_parameters, errors)
        self.push_writer(writer)

    def pop_writer(self):
        writer = self._writers[-1]
        del self._writers[-1]
        writer.end_document()
        if self._writers:
            # copy writer methods onto `self` for performance
            (self.start_document, self.end_document, self.start_element,
            self.end_element, self.namespace, self.attribute, self.text,
            self.comment, self.processing_instruction
            ) = _writer_methods(self._writers[-1])
        return writer

    def copy_nodes(self, nodes):
        for node in nodes:
            self.copy_node(node)
        return

    def copy_node(self, node):
        if isinstance(node, tree.element):
            self.start_element(node.xml_qname, node.xml_namespace,
                               node.xmlns_attributes.copy())
            for attr in node.xml_attributes.nodes():
                self.attribute(attr.xml_qname, attr.xml_value, attr.xml_namespace)
            for child in node:
                self.copy_node(child)
            self.end_element(node.xml_qname, node.xml_namespace)
        elif isinstance(node, tree.attribute):
            self.attribute(node.xml_qname, node.xml_value, node.xml_namespace)
        elif isinstance(node, tree.text):
            self.text(node.xml_value, not node.xsltOutputEscaping)
        elif isinstance(node, tree.processing_instruction):
            self.processing_instruction(node.xml_target, node.xml_data)
        elif isinstance(node, tree.comment):
            self.comment(node.xml_value)
        elif isinstance(node, tree.entity):
            for child in node:
                self.copy_node(child)
        elif isinstance(node, tree.namespace):
            self.namespace(node.xml_name, node.xml_value)
        else:
            pass
        return

    def add_function(self, name, function):
        if not callable(function):
            raise TypeError("function must be a callable object")
        self.functions[name] = function
        return

    def clone(self):
        return self.__class__(self, self.node, self.position, self.size,
                              self.variables, self.namespaces)

    def evaluate(self, expr):
        """
        The main entry point for evaluating an XPath expression, using self as context
        expr - a unicode object with the XPath expression
        """
        parsed = parser.parse(expr)
        return parsed.evaluate(self)

    def __repr__(self):
        ptr = id(self)
        if ptr < 0:
            ptr += 0x100000000L
        return ('<%s at 0x%x: node %r, position %d, size %d>' %
                (self.__class__.__name__, ptr, self.node, self.position,
                 self.size))


def launch(*args, **kwargs):
    import pprint
    from amara.xpath.util import simplify
    source = args[0]
    expr = args[1]
    import amara
    doc = amara.parse(source)
    result = doc.xml_select(expr.decode('utf-8'))
    pprint.pprint(simplify(result))
    return


import sys, getopt

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hv", ["help", ])
        except getopt.error, msg:
            raise Usage(msg)
    
        # option processing
        kwargs = {}
        for option, value in opts:
            if option == "-v":
                verbose = True
            if option in ("-h", "--help"):
                raise Usage(help_message)
    
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2

    launch(*args, **kwargs)


if __name__ == "__main__":
    sys.exit(main())

