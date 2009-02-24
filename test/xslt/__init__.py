########################################################################
# test/xslt/__init__.py
import os
import gc
import sys
import uuid
import difflib

from amara import Error
from amara.lib import inputsource, iri, treecompare
from amara.xpath import datatypes, util
from amara.xslt import XsltError, transform
from amara.xslt.processor import processor

# Defined to ignore this module in tracebacks
__unittest = True

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

class testsource(object):
    """
    Encapsulates an inputsource given as a string or URI, so that it can be
    referenced in various ways. Used by XsltTest().
    """
    __slots__ = ('source', 'uri', 'validate', 'xinclude', 'external')
    def __init__(self, source, uri=None, validate=False, xinclude=True,
                 external=False):
        self.source = source
        self.uri = uri
        self.validate = validate
        self.xinclude = xinclude
        self.external = external

class filesource(testsource):
    def __init__(self, path, validate=False, xinclude=True, external=False):
        # Same logic that exists in _4xslt.py
        # The processor only deals with URIs, not file paths
        if not os.path.isabs(path):
            # it is relative to the calling module
            module = sys._getframe(1).f_globals['__name__']
            module = sys.modules[module]
            moduledir = os.path.dirname(os.path.abspath(module.__file__))
            path = os.path.join(moduledir, path)
            assert os.path.exists(path)
        testsource.__init__(self, path, None, validate, xinclude)

class stringsource(testsource):
    def __init__(self, source, uri=None, validate=False, xinclude=True,
                 external=False):
        if not uri:
            # it is relative to the calling module
            module = sys._getframe(1).f_globals['__name__']
            module = sys.modules[module]
            moduledir = os.path.dirname(os.path.abspath(module.__file__))
            path = str(uuid.uuid4())
            uri = iri.os_path_to_uri(os.path.join(moduledir, path))
        testsource.__init__(self, source, uri, validate, xinclude)


from amara.test import test_main, test_case, TestError

class xslt_test(test_case):

    source = None
    transform = None
    expected = None
    parameters = None

    class __metaclass__(type):
        def __init__(cls, name, bases, namespace):
            transform = cls.transform
            if transform and not isinstance(transform, testsource):
                cls.transform = tuple(transform)

    def _format_error(self, error_class, error_code):
        if not issubclass(error_class, Error):
            return error_class.__name__
        for name, value in error_class.__dict__.iteritems():
            if value == error_code:
                error_code = error_class.__name__ + '.' + name
                break
        return '%s(%s)' % (error_class.__name__, error_code)

    def setUp(self):
        self.source = inputsource(self.source.source, self.source.uri)
        if isinstance(self.transform, testsource):
            T = self.transform
            self.transform = [inputsource(T.source, T.uri)]
        elif self.transform:
              self.transform = [ inputsource(T.source, T.uri)
                                 for T in self.transform ]
        else:
            self.transform = ()
        return

    def _assert_result(self, result):
        method = result.parameters.method
        omit_decl = result.parameters.omit_xml_declaration
        expected, compared = self.expected, result
        if method == (None, 'xml') and not omit_decl:
            diff = treecompare.xml_diff(expected, compared)
        elif method == (None, 'html'):
            diff = treecompare.html_diff(expected, compared)
        else:
            expected = expected.splitlines()
            compared = compared.splitlines()
            diff = difflib.unified_diff(expected, compared,
                                        'expected', 'compared',
                                        n=2, lineterm='')
        diff = '\n'.join(diff)
        self.assertFalse(diff, msg=(None, diff))
        gc.collect()

    def test_processor(self):
        P = processor()
        for transform in self.transform:
            P.append_transform(transform)
        parameters = self.parameters
        if parameters:
            parameters = util.parameterize(parameters)
        result = P.run(self.source, parameters=parameters)
        self._assert_result(result)

    #def test_transform(self):
    #    result = transform(self.source, self.transform, params=self.parameters)
    #    self._assert_result(result)


class xslt_error(xslt_test):
    error_class = XsltError
    error_code = None

    class __metaclass__(xslt_test.__metaclass__):
        def __init__(cls, name, bases, namespace):
            xslt_test.__metaclass__.__init__(cls, name, bases, namespace)
            if (issubclass(cls.error_class, Error)
                and cls.error_code is None
                and 'error_code' not in namespace
                and '__unittest__' not in namespace):
                raise ValueError("class '%s' must define 'error_code'" %
                                 name)

    def test_processor(self):
        try:
            xslt_test.test_processor(self)
        except self.error_class, error:
            expected = self._format_error(self.error_class, self.error_code)
            compared = self._format_error(self.error_class,
                                          getattr(error, 'code', None))
            self.assertEquals(expected, compared)
        else:
            expected = self._format_error(self.error_class, self.error_code)
            self.fail('%s not raised' % expected)

if __name__ == '__main__':
    import glob
    module_dir = os.path.dirname(os.path.abspath(__file__))
    pattern = os.path.join(module_dir, 'test_*.py')
    test_modules = [ os.path.basename(fn)[:-3] for fn in glob.glob(pattern) ]
    # Re-arrange the modules /slightly/
    for name in ('test_basics', 'test_exslt', 'test_borrowed'):
        try:
            test_modules.remove(name)
        except ValueError:
            pass
        else:
            test_modules.append(name)
    test_modules.remove('test_borrowed')
    test_main(*test_modules)