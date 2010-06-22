#########################################################################
# amara/tree.py
"""
A very fast tree (node API) library for XML processing with sensible conventions.
"""

__all__ = ["parse", 'node', 'entity', 'element', 'attribute', 'comment', 'processing_instruction', 'text']

from amara._domlette import *
from amara._domlette import parse as _parse
from amara.lib import inputsource

#node = Node
#document = Document
#entity = Document
#element = Element
#namespace = Namespace
#attribute = Attr
#comment = Comment
#processing_instruction = ProcessingInstruction
#text = Text
#character_data = CharacterData

#FIXME: and so on

def parse(obj, uri=None, entity_factory=None, standalone=False, validate=False, rule_handler=None):
    '''
    Parse an XML input source and return a tree

    :param obj: object with "text" to parse
    :type obj: string, Unicode object (only if you really
        know what you're doing), file-like object (stream), file path, URI or
        `amara.inputsource` object
    :param uri: optional document URI.  You really should provide this if the input source is a
        text string or stream
    :type uri: string
    :return: Parsed tree object
    :rtype: `amara.tree.entity` instance
    :raises `amara.ReaderError`: If the XML is not well formed, or there are other core parsing errors

    entity_factory - optional factory callable for creating entity nodes.  This is the
                     main lever for customizing the classes used to construct tree nodes
    standalone - similar to the standalone declaration for XML.  Asserts that the XML
                 being parsed does not require any resouces outside the given input source
                 (e.g. on the network).  In this case has the side-effect of ignoring such
                 external resources if they are encountered (which is where it diverges
                 from XML core.  In XML core that would be a fatal error)
    validate - whether or not to apply DTD validation
    rule_handler - Handler object used to perform rule matching in incremental processing.

    Examples:

    >>> import amara
    >>> MONTY_XML = """<monty>
    ...   <python spam="eggs">What do you mean "bleh"</python>
    ...   <python ministry="abuse">But I was looking for argument</python>
    ... </monty>"""
    >>> doc = amara.parse(MONTY_XML)
    >>> len(doc.xml_children)
    1

    '''
    if standalone:
        flags = PARSE_FLAGS_STANDALONE
    elif validate:
        flags = PARSE_FLAGS_VALIDATE
    else:
        flags = PARSE_FLAGS_EXTERNAL_ENTITIES
    return _parse(inputsource(obj, uri), flags, entity_factory=entity_factory,rule_handler=rule_handler)

#Rest of the functions are deprecated, and will be removed soon

def NonvalParse(isrc, readExtDtd=True, nodeFactories=None):
    '''
    DEPRECATED.  Please instead use parse(isrc, validate=False)
    '''
    import warnings
    if readExtDtd:
        warnings.warn("use parse(source, PARSE_FLAGS_EXTERNAL_ENTITIES"
                      "[, node_factories]) instead",
                      DeprecationWarning, 2)
        flags = PARSE_FLAGS_EXTERNAL_ENTITIES
    else:
        warnings.warn("use parse(source, PARSE_FLAGS_STANDALONE"
                      "[, node_factories]) instead",
                      DeprecationWarning)
        flags = PARSE_FLAGS_STANDALONE
    if nodeFactories is not None:
        args = (nodeFactories,)
    else:
        args = ()
    return parse(isrc, flags, *args)


def ValParse(isrc, nodeFactories=None):
    '''
    DEPRECATED.  Please instead use parse(isrc)
    '''
    import warnings
    warnings.warn("use parse(source, PARSE_FLAGS_VALIDATE[, node_factories]) "
                  "instead",
                  DeprecationWarning)
    if nodeFactories is not None:
        args = (nodeFactories,)
    else:
        args = ()
    return parse(isrc, PARSE_FLAGS_VALIDATE, *args)


def ParseFragment(*args, **kwds):
    '''
    DEPRECATED.  Please instead use parse(isrc)
    '''
    import warnings
    warnings.warn("use parse_fragment(source[, namespaces[, node_factories]]) "
                "instead",
                DeprecationWarning)
    return parse_fragment(*args, **kwds)


# ------------------------------------------------------------
# Experimental sendtree() support.   This should not be used
# for any kind of production.  It is an experimental prototype
# ------------------------------------------------------------

def sendtree(obj, pattern, target, uri=None, entity_factory=None, standalone=False, validate=False):
    # This callback does "pattern matching".  Nothing really implemented now--just a simple check
    # for an element name match.  Eventually build into a pattern matching system.
    def callback(node):
        if node.xml_local == pattern:
            target.send(node)

    # Run the parser
    return parse(obj,uri,entity_factory,standalone,validate,callback)


        
