#amara.lib._inputsource
#Named with _ to avoid clash with amara.lib.inputsource class

import os
from cStringIO import StringIO
from uuid import UUID, uuid1, uuid4

from amara._expat import InputSource
from amara.lib import iri, xmlstring
from amara.lib.xmlstring import isxml

__all__ = ['_inputsource']

class _inputsource(InputSource):
    def __new__(self, arg, uri=None, resolver=iri.DEFAULT_RESOLVER):
        """
        arg - a string, Unicode object (only if you really know what you're doing),
              file-like object (stream), file path or URI.  You can also pass an
              InputSource object, in which case the return value is just the same
              object, possibly with the URI modified
        uri - optional override URI.  The base URI for the IS will be set to this
              value

        Returns an InputSource which can be passed to 4Suite APIs.
        """
        #do the imports within the function: a tad bit less efficient, but
        #avoid circular crap
        #from amara._xmlstring import IsXml as isxml

        if isinstance(arg, InputSource):
            return arg

        if hasattr(arg, 'read'):
            #Create dummy Uri to use as base
            uri = uri or uuid4().urn
            stream = arg
        elif isxml(arg):
            uri = uri or uuid4().urn
            stream = StringIO(arg)
        elif iri.is_absolute(arg) and not os.path.isfile(arg):
            uri = arg
            stream = resolver.resolve(uri)
        else:
            uri = iri.os_path_to_uri(arg)
            stream = resolver.resolve(uri)

        #We might add the ability to load zips, gzips & bzip2s
        #http://docs.python.org/lib/module-zlib.html
        #http://docs.python.org/lib/module-gzip.html
        #http://docs.python.org/lib/module-bz2.html
        #http://docs.python.org/lib/zipfile-objects.html

        return InputSource.__new__(self, stream, uri)
