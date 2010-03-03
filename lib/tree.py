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

def parse(obj, uri=None, entity_factory=None, standalone=False, validate=False):
    '''
    Parse an XML input source and return a tree
    
    obj - The XML to be parsed, in the form of a string, Unicode object (only if you really
          know what you're doing), file-like object (stream), file path, URI or
          amara.inputsource object
    uri - optional document URI.  You really should provide this if the input source is a
          text string or stream
    entity_factory - optional factory callable for creating entity nodes.  This is the
                     main lever for customizing the classes used to construct tree nodes
    standalone - similar to the standalone declaration for XML.  Asserts that the XML
                 being parsed does not require any resouces outside the given input source
                 (e.g. on the network).  In this case has the side-effect of ignoring such
                 external resources if they are encountered (which is where it diverges
                 from XML core.  In XML core that would be a fatal error)
    validate - whether or not to apply DTD validation
    '''
    if standalone:
        flags = PARSE_FLAGS_STANDALONE
    elif validate:
        flags = PARSE_FLAGS_VALIDATE
    else:
        flags = PARSE_FLAGS_EXTERNAL_ENTITIES
    return _parse(inputsource(obj, uri), flags, entity_factory=entity_factory)

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
