########################################################################
# test/xslt/__init__.py
import os
import sys
import unittest

from amara import Error
from amara.lib import inputsource, iri
from amara.xpath import datatypes
from amara.xslt import XsltError

#from amara.xslt.functions import generate_id_function as xslt_generate_id
#g_idmap = {}
#class generate_id_function(xslt_generate_id):
#    """
#    Replacement for XSLT's generate-id(). Generates IDs that are
#    unique, but not random, for comparisons in the test suites.
#    """
#    def evaluate(self, context):
#        result = xslt_generate_id.evaluate(self, context)
#        if result:
#            result = g_idmap.setdefault(result, len(g_idmap) + 1)
#            result = datatypes.string(u'id%d' % result)
#        return result

class _mapping_resolver(iri.default_resolver):
    def __init__(self, uris):
        iri.default_resolver.__init__(self)
        self._uris = uris

    def normalize(self, uriref, baseuri):
        if uriref in self._uris:
            return uriref
        return iri.default_resolver.normalize(self, uriref, baseuri)

    def resolve(self, uri, baseuri=None):
        if uri in self._uris:
            return cStringIO.StringIO(self._uris[uri])
        return iri.default_resolver.resolve(self, uri, baseuri)

def get_mapping_factory():
    return


class testsource(inputsource):
    """
    Encapsulates an inputsource given as a string or URI, so that it can be
    referenced in various ways. Used by XsltTest().
    """
    def __new__(cls, source, uri=None, validate=False, xinclude=True):
        self = inputsource.__new__(cls, source, uri)
        self.source = source
        self.validate = validate
        self.xinclude = xinclude
        return self

    def copy(self):
        return testsource(self.source, self.uri, self.validate, self.xinclude)

class filesource(testsource):
    def __new__(cls, path, validate=False, xinclude=True):
        # Same logic that exists in _4xslt.py
        # The processor only deals with URIs, not file paths
        if not os.path.isabs(path):
            # it is relative to the calling module
            module = sys._getframe(1).f_globals['__name__']
            module = sys.modules[module]
            path = os.path.join(os.path.dirname(module.__file__), path)
        return testsource.__new__(cls, path, None, validate, xinclude)

class stringsource(testsource):
    def __new__(cls, arg, uri=None, validate=False, xinclude=True):
        if not uri:
            # it is relative to the calling module
            module = sys._getframe(1).f_globals['__name__']
            module = sys.modules[module]
            uri = iri.os_path_to_uri(module.__file__)
        return testsource.__new__(cls, arg, uri, validate, xinclude)


class xslt_test(unittest.TestCase):
    source = None
    transform = None
    processor_arguments = {}

    class __metaclass__(type):
        def __init__(cls, name, bases, namespace):
            transform = cls.transform
            if transform and not isinstance(transform, testsource):
                cls.transform = tuple(transform)

    def _format_error(self, error_class, error_code):
        if issubclass(error_class, Error):
            for name, value in error_class.__dict__.iteritems():
                if value == error_code:
                    error_code = error_class.__name__ + '.' + name
                    break
        return '%s(%s)' % (error_class.__name__, error_code)

    def setUp(self):
        from amara.xslt.processor import processor
        P = self.processor = processor()
        if isinstance(self.transform, testsource):
            P.append_transform(self.transform.copy())
        else:
            for transform in (self.transform or ()):
                P.append_transform(transform.copy())
        return

    def runTest(self):
        self.processor.run(self.source.copy(), **self.processor_arguments)
        return


class xslt_error(xslt_test):
    error_class = XsltError
    error_code = None

    class __metaclass__(xslt_test.__metaclass__):
        def __init__(cls, name, bases, namespace):
            xslt_test.__metaclass__.__init__(cls, name, bases, namespace)
            if cls.error_code is None and 'error_code' not in namespace:
                raise ValueError("class '%s' must define 'error_code'" % name)

    def runTest(self):
        try:
            xslt_test.runTest(self)
        except self.error_class, error:
            expected = self._format_error(self.error_class, self.error_code)
            compared = self._format_error(self.error_class, error.code)
            self.assertEquals(expected, compared)
        else:
            expected = self._format_error(self.error_class, self.error_code)
            self.fail('%s not raised' % expected)