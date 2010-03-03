import os, unittest, sys, codecs
import warnings
from amara.lib import iri, irihelpers, inputsource
from amara.test import file_finder

FILE = file_finder(__file__)

class Test_default_resolver(unittest.TestCase):
    '''irihelpers.resolver'''
    def test_uri_jail(self):
        start_uri = iri.os_path_to_uri(FILE('test_irihelpers.py'))
        #raise start_uri
        #print >> sys.stderr, "GRIPPO", start_uri
        start_base = start_uri.rsplit('/', 1)[0] + '/'
        #Only allow access files in the same directory as sampleresource.txt via URL jails
        auths = [(lambda u: u.rsplit('/', 1)[0] + '/' == start_base, True)]
        resolver = irihelpers.resolver(authorizations=auths)
        start_isrc = inputsource(start_uri, resolver=resolver)
        new_isrc = start_isrc.resolve('sampleresource.txt', start_base)
        self.assertEqual('Spam', new_isrc.stream.read().strip())
        self.assertRaises(iri.IriError, resolver.resolve,
                          'http://google.com', start_base)


class Test_scheme_registry_resolver(unittest.TestCase):
    '''scheme_registry_resolver'''
    def test_scheme_registry_resolver(self):
        def eval_scheme_handler(uri, base=None):
            if base: uri = base+uri
            uri = uri[5:]
            return str(eval(uri))

        def shift_scheme_handler(uri, base=None):
            if base: uri = base+uri
            uri = uri[6:]
            return ''.join([ chr(ord(c)+1) for c in uri])

        resolver = irihelpers.scheme_registry_resolver(
            handlers={'eval': eval_scheme_handler,
                      'shift': shift_scheme_handler})
        start_isrc =  inputsource(FILE('sampleresource.txt'),
                                        resolver=resolver)
        
        scheme_cases = [(None, 'eval:150-50', '100'),
                (None, 'shift:abcde', 'bcdef'),
                ('eval:150-', '50', '100'),
                ('shift:ab', 'cde', 'bcdef'),
            ]

        for base, relative, expected in scheme_cases:
            res = resolver.resolve(relative, base)
            self.assertEqual(expected, res, "URI: base=%s uri=%s" % (base, relative))

        resolver.handlers[None] = shift_scheme_handler
        del resolver.handlers['shift']

        for base, relative, expected in scheme_cases:
            res = resolver.resolve(relative, base)
            self.assertEqual(expected, res, "URI: base=%s uri=%s" % (base, relative))


