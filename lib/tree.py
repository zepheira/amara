#########################################################################
# amara/tree.py
"""
A very fast tree (node API) library for XML processing with sensible conventions.
"""

__all__ = ["_parse", 'node', 'entity', 'element', 'attribute', 'comment', 'processing_instruction', 'text']

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

#FiXME: and so on

def parse(obj, uri=None, entity_factory=None, standalone=False, validate=False):
    if standalone:
        flags = PARSE_FLAGS_STANDALONE
    elif validate:
        flags = PARSE_FLAGS_VALIDATE
    else:
        flags = PARSE_FLAGS_EXTERNAL_ENTITIES
    return _parse(inputsource(obj, uri), flags, entity_factory=entity_factory)


def NonvalParse(isrc, readExtDtd=True, nodeFactories=None):
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
    import warnings
    warnings.warn("use parse_fragment(source[, namespaces[, node_factories]]) "
                "instead",
                DeprecationWarning)
    return parse_fragment(*args, **kwds)
