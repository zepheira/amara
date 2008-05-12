#########################################################################
# amara/domlette.py
"""
A very fast DOM-like library tailored for use in XPath/XSLT.
"""

from amara._domlette import *

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
