#########################################################################
# amara/domlette.py
"""
A very fast DOM-like library tailored for use in XPath/XSLT.
"""

__all__ = ["_parse"]

from amara._domlette import *
from amara._domlette import parse as _parse
from amara.lib import inputsource

def parse(obj, uri=None, node_factories=None, standalone=False, validate=False):
    if standalone:
        flags = PARSE_FLAGS_STANDALONE
    elif validate:
        flags = PARSE_FLAGS_VALIDATE
    else:
        flags = PARSE_FLAGS_EXTERNAL_ENTITIES
    return _parse(inputsource(obj, uri), flags, node_factories=node_factories)


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
