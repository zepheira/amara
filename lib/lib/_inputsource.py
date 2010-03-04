#amara.lib._inputsource
#Named with _ to avoid clash with amara.lib.inputsource class

from __future__ import with_statement

import os
import urllib, urllib2
from cStringIO import StringIO
from uuid import uuid4

from amara.lib import IriError
from amara._expat import InputSource
from amara.lib.iri import is_absolute, os_path_to_uri
from amara.lib.xmlstring import isxml
from amara.lib.irihelpers import DEFAULT_RESOLVER

__all__ = [
'_inputsource', 'XMLSTRING', 'XMLURI', 'XMLFILE',
]

MAX_URI_LENGTH_FOR_HEURISTIC = 1024

#Classifications of raw input sources
XMLSTRING = 1
XMLURI = 2
XMLFILE = 3

class _inputsource(InputSource):
    """
    The representation of a resource. Supports further, relative resolution of
    URIs, including resolution to absolute form of URI references.

    Standard object attributes:
        _supported_schemes is a list of URI schemes supported 
        for dereferencing (representation retrieval).
    """
    def __new__(cls, arg, uri=None, encoding=None, resolver=None, sourcetype=0):
        """
        arg - a string, Unicode object (only if you really know what you're doing),
              file-like object (stream), file path or URI.  You can also pass an
              InputSource object, in which case the return value is just the same
              object, possibly with the URI modified
        uri - optional override URI.  The base URI for the IS will be set to this
              value

        Returns an input source which can be passed to Amara APIs.
        """
        #do the imports within the function: a tad bit less efficient, but
        #avoid circular crap
        #from amara._xmlstring import IsXml as isxml
        resolver = resolver or DEFAULT_RESOLVER

        if isinstance(arg, InputSource):
            return arg

        #if arg == (u'', ''): -> UnicodeWarning: Unicode equal comparison failed to convert both arguments to Unicode - interpreting them as being unequal
        if arg == '':
            #FIXME L10N
            raise ValueError("Cannot parse an empty string as XML")
        
        if hasattr(arg, 'read'):
            #Create dummy Uri to use as base
            uri = uri or uuid4().urn
            stream = arg
        #XXX: Should we at this point refuse to proceed unless it's a basestring?
        elif sourcetype == XMLSTRING or isxml(arg):
            #See this article about XML detection heuristics
            #http://www.xml.com/pub/a/2007/02/28/what-does-xml-smell-like.html
            uri = uri or uuid4().urn
            stream = StringIO(arg)
        elif is_absolute(arg) and not os.path.isfile(arg):
            uri = arg
            stream = resolver.resolve(uri)
        #If the arg is beyond a certain length, don't even try it as a URI
        elif len(arg) < MAX_URI_LENGTH_FOR_HEURISTIC:
            uri = os_path_to_uri(arg)
            stream = resolver.resolve(uri)
        else:
            #FIXME L10N
            raise ValueError("Does not appear to be well-formed XML")

        #We might add the ability to load zips, gzips & bzip2s
        #http://docs.python.org/lib/module-zlib.html
        #http://docs.python.org/lib/module-gzip.html
        #http://docs.python.org/lib/module-bz2.html
        #http://docs.python.org/lib/zipfile-objects.html

        #import inspect; print inspect.stack()
        #InputSource.__new__ is in C: expat/input_source.c:inputsource_new
        return InputSource.__new__(cls, stream, uri, encoding)

    def __init__(self, arg, uri=None, encoding=None, resolver=None, sourcetype=0):
        #uri is set 
        self.resolver = resolver or DEFAULT_RESOLVER

    @staticmethod
    def text(arg, uri=None, encoding=None, resolver=None):
        '''
        Set up an input source from text, according to the markup convention of the term
        (i.e. in Python terms a string with XML, HTML, fragments thereof, or tag soup)
        
        Supports processing content sources that are not unambiguously XMl or HTML strings
        '''
        return _inputsource(arg, uri, encoding, resolver, sourcetype=XMLSTRING)

    def resolve(self, uriRef, baseUri=None):
        """
        Takes a URI or a URI reference plus a base URI, produces an absolutized URI
        if a base URI was given, then attempts to obtain access to an entity
        representing the resource identified by the resulting URI,
        returning the entity as a stream (a file-like object).
        (this work is done in self.resolver)

        Raises a IriError if the URI scheme is unsupported or if a stream
        could not be obtained for any reason.
        """
        if baseUri:
            uriRef = self.resolver.absolutize(uriRef, baseUri)
        return self.__class__(uriRef)

    def absolutize(self, uriRef, baseUri):
        """
        Resolves a URI reference to absolute form, effecting the result of RFC
        3986 section 5. The URI reference is considered to be relative to
        the given base URI.

        Also verifies that the resulting URI reference has a scheme that
        resolve() supports, raising a IriError if it doesn't.

        The default implementation does not perform any validation on the base
        URI beyond that performed by absolutize().

        If leniency has been turned on (self.lenient=True), accepts a base URI
        beginning with '/', in which case the argument is assumed to be an absolute
        path component of 'file' URI with no authority component.
        """
        return self.resolver.absolutize(uriRef, baseUri)

