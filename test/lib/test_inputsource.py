########################################################################
# test/xslt/test_inputsource.py

import os, unittest, sys
from amara.lib import inputsource, iri, treecompare
#from amara.test.xslt import filesource
from amara.test import file_finder

FILE = file_finder(__file__)

#
class Test_basic_uri_resolver(unittest.TestCase):
    '''Basic Uri Resolver'''
    def test_basic_uri_resolver(self):
        data = [('http://foo.com/root/', 'path', 'http://foo.com/root/path'),
                ('http://foo.com/root',  'path', 'http://foo.com/path'),
                ]
        #import sys; print >> sys.stderr, filesource('sampleresource.txt').uri
        start_isrc = inputsource(FILE('sampleresource.txt'))
        #start_isrc = inputsource(filesource('sampleresource.txt').uri)
        for base, uri, exp in data:
            res = start_isrc.absolutize(uri, base)
            self.assertEqual(exp, res, "absolutize: %s %s" % (base, uri))

        base = 'foo:foo.com'
        uri = 'path'
        self.assertRaises(iri.IriError, start_isrc.absolutize, uri, base)

        base = os.getcwd()
        if base[-1] != os.sep:
            base += os.sep
        new_isrc = start_isrc.resolve(FILE('sampleresource.txt'), iri.os_path_to_uri(base))
        self.assertEqual('Spam', new_isrc.stream.readline().rstrip(), 'resolve')


#FIXME: Following tests badly need update
rlimit_nofile = 300
try:
    import resource
except ImportError:
    pass
else:
    rlimit_nofile = resource.getrlimit(resource.RLIMIT_NOFILE)[0] + 10

def test_many_inputsources():
    assert rlimit_nofile < 20000, "is your file limit really that large?"

    # Amara's inputsource consumes a filehandle, in the 'stream' attribute
    # See what happens if we run out of file handles.
    sources = []
    filename = __file__
    for i in range(rlimit_nofile):
        try:
            sources.append(inputsource(filename))
        except:
            print "Failed after", i, "files"

#
if __name__ == '__main__':
    raise SystemExit("Use nosetests")

