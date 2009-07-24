import sys
import amara
from amara import tree
from amara.writers.struct import *
#from amara.namespaces import *

INDENT_STR = '    '

def srewrite(source, **kwargs):
    doc = amara.parse(source)
    def handle_node(node, indent=0):
        empty = True
        if isinstance(node, tree.text):
            yield repr(node.xml_value)
        elif isinstance(node, tree.entity):
            yield  INDENT_STR*indent + 'ROOT('
            for child in node.xml_children:
                empty = False
                yield '\n'
                for chunk in handle_node(child, indent+1):
                    yield chunk
            yield (not empty)*INDENT_STR*indent + ')\n'
        elif isinstance(node, tree.element):
            yield  INDENT_STR*indent + 'E('
            yield repr((node.xml_namespace, node.xml_local)) if node.xml_namespace else repr(node.xml_local)
            if node.xml_attributes:
                yield repr(dict(node.xml_attributes))
            for child in node.xml_children:
                empty = False
                yield '\n'
                for chunk in handle_node(child, indent+1):
                    yield chunk
            yield (not empty)*INDENT_STR*indent + ')\n'
    for chunk in handle_node(doc): yield chunk
    return

def launch(source, **kwargs):
    print kwargs['srewrite']
    if kwargs.get('srewrite', True):
        print ''.join(srewrite(source, **kwargs))
    return

#Ideas borrowed from
# http://www.artima.com/forums/flat.jsp?forum=106&thread=4829

def command_line_prep():
    from optparse import OptionParser
    usage = "Amara 2.x.  Tool to generate code to generate XML.\n"
    usage += "python -m 'amara.tools.kekule' [options] source"
    parser = OptionParser(usage=usage)
    parser.add_option("--struct-rewrite",
                      action="store_true", dest="srewrite", default=True,
                      help="Output a skeleton of structwriter code corresponding to the given XML")
    parser.add_option("-S", "--struct",
                      action="store_true", dest="structw", default=True,
                      help="Output code for Amara structwriter")
    return parser


def main(argv=None):
    #But with better integration of entry points
    if argv is None:
        argv = sys.argv
    # By default, optparse usage errors are terminated by SystemExit
    try:
        optparser = command_line_prep()
        options, args = optparser.parse_args(argv[1:])
        # Process mandatory arguments with IndexError try...except blocks
        try:
            source = args[0]
        except IndexError:
            optparser.error("Missing source kekule")
    except SystemExit, status:
        return status

    # Perform additional setup work here before dispatching to run()
    # Detectable errors encountered here should be handled and a status
    # code of 1 should be returned. Note, this would be the default code
    # for a SystemExit exception with a string message.

    if source == '-':
        source = sys.stdin
    launch(source, structw=options.structw, srewrite=options.srewrite)
    return


if __name__ == "__main__":
    sys.exit(main(sys.argv))

