########################################################################
# $Header: /var/local/cvsroot/4Suite/Ft/Lib/Resolvers.py,v 1.3 2005-01-05 10:04:22 mbrown Exp $
"""
Specialized and useful URI resolvers

Copyright 2005-2008 Fourthought, Inc. (USA).
Detailed license and copyright information: http://4suite.org/COPYRIGHT
Project home, documentation, distributions: http://4suite.org/
"""

import os, sys, cStringIO
from amara.lib import iri


class scheme_registry_resolver(iri.default_resolver):
    """
    A type of resolver that allows developers to register different callable
    objects to handle different URI schemes.  The default action if there
    is nothing registered for the scheme will be to fall back to
    base behavior *unless* you have in the mapping a special
    scheme None.  The callable object that is the value on that key will
    then be used as the default for all unknown schemes.

    The expected function signature for scheme call-backs matches
    iri.default_resolver.resolve, without the instance argument:

    resolve(uri, base=None)

    Reminder: Since this does not include self, if you are registering
    a method, use the method instance (i.e. myresolver().handler
    rather than myresolver.handler)

    You can manipulate the mapping directly using the "handlers" attribute.
    """
    def __init__(self, handlers=None):
        """
        handlers - a Python dictionary with scheme names as keys (e.g. "http")
        and callable objects as values
        """
        iri.default_resolver.__init__(self)
        self.handlers = handlers or {}
        return

    def resolve(self, uri, base=None):
        scheme = iri.get_scheme(uri)
        if not scheme:
            if base:
                scheme = iri.get_scheme(base)
            if not scheme:
                #Another option is to fall back to Base class behavior
                raise Iri.IriError(Iri.IriError.SCHEME_REQUIRED,
                                   base=base, ref=uri)
        func = self.handlers.get(scheme)
        if not func:
            func = self.handlers.get(None)
            if not func:
                return iri.default_resolver.resolve(self, uri, base)
        return func(uri, base)


class FacadeResolver(iri.default_resolver):
    """
    A type of resolver that uses a cache of resources, a dictionary of URI
    to result mappings (similar to memoizing the resolve method).  When a
    URI is provided for resolution, the mapping is first checked, and a
    stream is constructed by wrapping the mapping value string.
    If no match is found in the mapping, fall back to the base
    resolver logic.

    You can manipulate the mapping directly using the "cache" attribute.
    """
    def __init__(self, cache=None, observer=None):
        """
        cache - a dictionary with mapings from URI to value (as an object
        to be converted to a UTF-8 encoded string)
        observer - callable object invoked on each resolution request
        """
        iri.default_resolver.__init__(self)
        self.cache = cache or {}
        self.observer = observer
        return

    def resolve(self, uri, base=None):
        self.observer(uri, base)
        #Does not factor in base.  Should it noramlize before checking?
        if uri in self.cache:
            cachedval = self.cache[uri]
            if isinstance(cachedval, unicode):
                return cStringIO.StringIO(cachedval.encode('utf-8'))
            else:
                return cStringIO.StringIO(str(cachedval))
        return iri.default_resolver.resolve(self, uri, base)


