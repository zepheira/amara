########################################################################
# $Header: /var/local/cvsroot/4Suite/Ft/Lib/Resolvers.py,v 1.3 2005-01-05 10:04:22 mbrown Exp $
"""
Specialized and useful input source and URI tools

Copyright 2008-2009 Uche Ogbuji
"""

import os, sys
from cStringIO import StringIO
import urllib, urllib2
import mimetools
from email.Utils import formatdate as _formatdate

from amara.lib import IriError
#from amara.lib import inputsource
from amara.lib.iri import *

__all__ = [
'DEFAULT_URI_SCHEMES',
'DEFAULT_RESOLVER',
'scheme_registry_resolver',
'facade_resolver',
'uridict',
'resolver',
]

# URI schemes supported by resolver_base
DEFAULT_URI_SCHEMES = ('http', 'file', 'ftp', 'data', 'pkgdata')
if hasattr(urllib2, 'HTTPSHandler'):
    DEFAULT_URI_SCHEMES += ('https',)
DEFAULT_HIERARCHICAL_SEP = '/' #a separator to place between path segments when creating URLs

class resolver:
    """
    """
    _supported_schemes = DEFAULT_URI_SCHEMES
    def __init__(self, authorizations=None, lenient=True):
        """
        """
        self.authorizations = authorizations
        self.lenient = lenient

    def resolve(self, uriRef, baseUri=None):
        """
        Takes a URI or a URI reference plus a base URI, produces a absolutized URI
        if a base URI was given, then attempts to obtain access to an entity
        representing the resource identified by the resulting URI,
        returning the entity as a stream (a file-like object).

        Raises a IriError if the URI scheme is unsupported or if a stream
        could not be obtained for any reason.
        """
        if not isinstance(uriRef, urllib2.Request):
            if baseUri is not None:
                uri = self.absolutize(uriRef, baseUri)
                scheme = get_scheme(uri)
            else:
                uri = uriRef
                scheme = get_scheme(uriRef)
                # since we didn't use absolutize(), we need to verify here
                if scheme not in self._supported_schemes:
                    if scheme is None:
                        raise ValueError('When the URI to resolve is a relative '
                            'reference, it must be accompanied by a base URI.')
                    else:
                        raise IriError(IriError.UNSUPPORTED_SCHEME,
                                           scheme=scheme, resolver=self.__class__.__name__)
            req = urllib2.Request(uri)
        else:
            req, uri = uriRef, uriRef.get_full_url()

        if self.authorizations and not self.authorize(uri):
            raise IriError(IriError.DENIED_BY_RULE, uri=uri)
        # Bypass urllib for opening local files.
        if scheme == 'file':
            path = uri_to_os_path(uri, attemptAbsolute=False)
            try:
                stream = open(path, 'rb')
            except IOError, e:
                raise IriError(IriError.RESOURCE_ERROR,
                                   loc='%s (%s)' % (uri, path),
                                   uri=uri, msg=str(e))
            # Add the extra metadata that urllib normally provides (sans
            # the poorly guessed Content-Type header).
            stats = os.stat(path)
            size = stats.st_size
            mtime = _formatdate(stats.st_mtime)
            headers = mimetools.Message(StringIO(
                'Content-Length: %s\nLast-Modified: %s\n' % (size, mtime)))
            stream = urllib.addinfourl(stream, headers, uri)
        else:
            # urllib2.urlopen, wrapped by us, will suffice for http, ftp,
            # data and gopher
            try:
                stream = urllib2.urlopen(req)
            except IOError, e:
                raise IriError(IriError.RESOURCE_ERROR,
                                   uri=uri, loc=uri, msg=str(e))
        return stream

    def authorize(self, uri):
        """
        Implement an authorization mechanism for resolvers, allowing you to create "jails" where only certain URIs are allowed
        """
        for match, allow in self.authorizations:
            if callable(match):
                if match(uri):
                    return allow
            elif match:
                return allow
        #If authoriztions are specified, and none allow the URI, deny by default
        #The user can easily reverse this by adding an auth (True, True)
        return False

    def absolutize(self, uriRef, baseUri):
        """
        For most cases iri.absolutize is good enough, and does the main work of this function.
        
        Resolves a URI reference to absolute form, effecting the result of RFC
        3986 section 5. The URI reference is considered to be relative to
        the given base URI.

        Also verifies that the resulting URI reference has a scheme that
        resolve() supports, raising a IriError if it doesn't.

        Default implementation does not perform any validation on the base
        URI beyond that performed by iri.absolutize().

        If leniency has been turned on (self.lenient=True), accepts a base URI
        beginning with '/', in which case the argument is assumed to be an absolute
        path component of 'file' URI with no authority component.
        """
        # since we know how absolutize works, we can anticipate the scheme of
        # its return value and verify that it's supported first
        if self.lenient:
            # assume file: if leading "/"
            if baseUri.startswith('/'):
                baseUri = 'file://' + baseUri
        return absolutize(uriRef, baseUri, limit_schemes=self._supported_schemes)

DEFAULT_RESOLVER = resolver()


class scheme_registry_resolver(resolver):
    """
    Resolver that handles URI resolution with a registry for handling different
    URI schemes.  The default action if there is nothing registered for the scheme
    will be to fall back to base behavior *unless* you have in the mapping a special
    scheme None.  The callable object that is the value on that key will then be used
    as the default for all unknown schemes.

    The expected function signature for scheme call-backs matches
    inputsource.resolve, without the instance argument:

    resolve(uri, base=None)

    Reminder: Since this does not include self, if you are registering
    a method, use the method instance (i.e. myresolver().handler
    rather than myresolver.handler)

    You can manipulate the mapping directly using the "handlers" attribute.
    handlers - a Python dictionary with scheme names as keys (e.g. "http")
    and callable objects as values
    """
    def __init__(self, authorizations=None, lenient=True, handlers=None):
        """
        """
        self.lenient = lenient
        self.handlers = handlers or {}
        resolver.__init__(self, authorizations, lenient)

    def resolve(self, uri, base=None):
        scheme = get_scheme(uri)
        if not scheme:
            if base:
                scheme = get_scheme(base)
            if not scheme:
                #Another option is to fall back to Base class behavior
                raise Iri.IriError(Iri.IriError.SCHEME_REQUIRED,
                                   base=base, ref=uri)
        func = self.handlers.get(scheme)
        #import sys; print >> sys.stderr, (self, self.handlers)
        if not func:
            func = self.handlers.get(None)
            if not func:
                return resolver.resolve(self, uri, base)
        return func(uri, base)


#Eliminate this class by demonstrating a standard memoize tool with the resolver
class facade_resolver(resolver):
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
        default_resolver.__init__(self)
        self.cache = cache or {}
        self.observer = observer
        return

    def resolve(self, uri, base=None):
        self.observer(uri, base)
        #Does not factor in base.  Should it noramlize before checking?
        if uri in self.cache:
            cachedval = self.cache[uri]
            if isinstance(cachedval, unicode):
                return StringIO(cachedval.encode('utf-8'))
            else:
                return StringIO(str(cachedval))
        return default_resolver.resolve(self, uri, base)

#
class uridict(dict):
    """
    A dictionary that uses URIs as keys. It attempts to observe some degree of
    URI equivalence as defined in RFC 3986 section 6. For example, if URIs
    A and B are equivalent, a dictionary operation involving key B will return
    the same result as one involving key A, and vice-versa.

    This is useful in situations where retrieval of a new representation of a
    resource is undesirable for equivalent URIs, such as "file:///x" and
    "file://localhost/x" (see RFC 1738), or "http://spam/~x/",
    "http://spam/%7Ex/" and "http://spam/%7ex" (see RFC 3986).

    Normalization performed includes case normalization on the scheme and
    percent-encoded octets, percent-encoding normalization (decoding of
    octets corresponding to unreserved characters), and the reduction of
    'file://localhost/' to 'file:///', in accordance with both RFC 1738 and
    RFC 3986 (although RFC 3986 encourages using 'localhost' and doing
    this for all schemes, not just file).

    An instance of this class is used by Ft.Xml.Xslt.XsltContext for caching
    documents, so that the XSLT function document() will return identical
    nodes, without refetching/reparsing, for equivalent URIs.
    """
    # RFC 3986 requires localhost to be the default host no matter
    # what the scheme, but, being descriptive of existing practices,
    # leaves it up to the implementation to decide whether to use this
    # and other tests of URI equivalence in the determination of
    # same-document references. So our implementation results in what
    # is arguably desirable, but not strictly required, behavior.
    #
    #FIXME: make localhost the default for all schemes, not just file
    def _normalizekey(self, key):
        key = normalize_case(normalize_percent_encoding(key))
        if key[:17] == 'file://localhost/':
            return 'file://' + key[16:]
        else:
            return key

    def __getitem__(self, key):
        return super(uridict, self).__getitem__(self._normalizekey(key))

    def __setitem__(self, key, value):
        return super(uridict, self).__setitem__(self._normalizekey(key), value)

    def __delitem__(self, key):
        return super(uridict, self).__delitem__(self._normalizekey(key))

    def has_key(self, key):
        return super(uridict, self).has_key(self._normalizekey(key))

    def __contains__(self, key):
        return super(uridict, self).__contains__(self._normalizekey(key))

    def __iter__(self):
        return iter(self.keys())

    iterkeys = __iter__
    def iteritems(self):
        for key in self.iterkeys():
            yield key, self.__getitem__(key)


#FIXME: Port to more amara.lib.iri functions
def get_filename_from_url(url):
    fullname = url.split('/')[-1].split('#')[0].split('?')[0]
    return fullname


def get_filename_parts_from_url(url):
    fullname = url.split('/')[-1].split('#')[0].split('?')[0]
    t = list(os.path.splitext(fullname))
    if t[1]:
        t[1] = t[1][1:]
    return t

