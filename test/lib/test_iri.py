import os, unittest, sys, codecs
import warnings
from amara.lib import iri, irihelpers, inputsource
from amara.test.lib import find_file

# Test cases for BaseJoin() ==================================================
# (base, relative, expected)
basejoin_test_cases = [
    ('','file:docs/xml/4XLink.api','file:docs/xml/4XLink.api'),
    ('file:docs/xml/','file:docs/xml/4XLink.api','file:docs/xml/4XLink.api'),
    ('file:/usr/local/lib/xslt/bar.xslt','http://4Suite.org/foo.xslt','http://4Suite.org/foo.xslt'),
    ]

# Test cases for Absolutize() ================================================
#CURRENT_DOC_URI = 'http://spam.com/bacon/eggs.xml'
BASE_URI = ('http://a/b/c/d;p?q',
            'http://a/b/c/d;p?q=1/2',
            'http://a/b/c/d;p=1/2?q',
            'fred:///s//a/b/c',
            'http:///s//a/b/c',
            )
# (ref, base, expected)
absolutize_test_cases = [
    # http://lists.w3.org/Archives/Public/uri/2004Feb/0114.html
    ('../c',  'foo:a/b', 'foo:c'),
    ('foo:.', 'foo:a',   'foo:.'),
    ('/foo/../../../bar', 'zz:abc', 'zz:/bar'),
    ('/foo/../bar',       'zz:abc', 'zz:/bar'),
    ('foo/../../../bar',  'zz:abc', 'zz:bar'),
    ('foo/../bar',        'zz:abc', 'zz:bar'),
    ('zz:.',              'zz:abc', 'zz:.'),
    ('/.'      , BASE_URI[0], 'http://a/'),
    ('/.foo'   , BASE_URI[0], 'http://a/.foo'),
    ('.foo'    , BASE_URI[0], 'http://a/b/c/.foo'),

    # http://gbiv.com/protocols/uri/test/rel_examples1.html
    # examples from RFC 2396
    ('g:h'     , BASE_URI[0], 'g:h'),
    ('g'       , BASE_URI[0], 'http://a/b/c/g'),
    ('./g'     , BASE_URI[0], 'http://a/b/c/g'),
    ('g/'      , BASE_URI[0], 'http://a/b/c/g/'),
    ('/g'      , BASE_URI[0], 'http://a/g'),
    ('//g'     , BASE_URI[0], 'http://g'),
    # changed with RFC 2396bis
    #('?y'      , BASE_URI[0], 'http://a/b/c/d;p?y'),
    ('?y'      , BASE_URI[0], 'http://a/b/c/d;p?y'),
    ('g?y'     , BASE_URI[0], 'http://a/b/c/g?y'),
    # changed with RFC 2396bis
    #('#s'      , BASE_URI[0], CURRENT_DOC_URI + '#s'),
    ('#s'      , BASE_URI[0], 'http://a/b/c/d;p?q#s'),
    ('g#s'     , BASE_URI[0], 'http://a/b/c/g#s'),
    ('g?y#s'   , BASE_URI[0], 'http://a/b/c/g?y#s'),
    (';x'      , BASE_URI[0], 'http://a/b/c/;x'),
    ('g;x'     , BASE_URI[0], 'http://a/b/c/g;x'),
    ('g;x?y#s' , BASE_URI[0], 'http://a/b/c/g;x?y#s'),
    # changed with RFC 2396bis
    #(''        , BASE_URI[0], CURRENT_DOC_URI),
    (''        , BASE_URI[0], 'http://a/b/c/d;p?q'),
    ('.'       , BASE_URI[0], 'http://a/b/c/'),
    ('./'      , BASE_URI[0], 'http://a/b/c/'),
    ('..'      , BASE_URI[0], 'http://a/b/'),
    ('../'     , BASE_URI[0], 'http://a/b/'),
    ('../g'    , BASE_URI[0], 'http://a/b/g'),
    ('../..'   , BASE_URI[0], 'http://a/'),
    ('../../'  , BASE_URI[0], 'http://a/'),
    ('../../g' , BASE_URI[0], 'http://a/g'),
    ('../../../g', BASE_URI[0], ('http://a/../g', 'http://a/g')),
    ('../../../../g', BASE_URI[0], ('http://a/../../g', 'http://a/g')),
    # changed with RFC 2396bis
    #('/./g', BASE_URI[0], 'http://a/./g'),
    ('/./g', BASE_URI[0], 'http://a/g'),
    # changed with RFC 2396bis
    #('/../g', BASE_URI[0], 'http://a/../g'),
    ('/../g', BASE_URI[0], 'http://a/g'),
    ('g.', BASE_URI[0], 'http://a/b/c/g.'),
    ('.g', BASE_URI[0], 'http://a/b/c/.g'),
    ('g..', BASE_URI[0], 'http://a/b/c/g..'),
    ('..g', BASE_URI[0], 'http://a/b/c/..g'),
    ('./../g', BASE_URI[0], 'http://a/b/g'),
    ('./g/.', BASE_URI[0], 'http://a/b/c/g/'),
    ('g/./h', BASE_URI[0], 'http://a/b/c/g/h'),
    ('g/../h', BASE_URI[0], 'http://a/b/c/h'),
    ('g;x=1/./y', BASE_URI[0], 'http://a/b/c/g;x=1/y'),
    ('g;x=1/../y', BASE_URI[0], 'http://a/b/c/y'),
    ('g?y/./x', BASE_URI[0], 'http://a/b/c/g?y/./x'),
    ('g?y/../x', BASE_URI[0], 'http://a/b/c/g?y/../x'),
    ('g#s/./x', BASE_URI[0], 'http://a/b/c/g#s/./x'),
    ('g#s/../x', BASE_URI[0], 'http://a/b/c/g#s/../x'),
    ('http:g', BASE_URI[0], ('http:g', 'http://a/b/c/g')),
    ('http:', BASE_URI[0], ('http:', BASE_URI[0])),
    # not sure where this one originated
    ('/a/b/c/./../../g', BASE_URI[0], 'http://a/a/g'),

    # http://gbiv.com/protocols/uri/test/rel_examples2.html
    # slashes in base URI's query args
    ('g'       , BASE_URI[1], 'http://a/b/c/g'),
    ('./g'     , BASE_URI[1], 'http://a/b/c/g'),
    ('g/'      , BASE_URI[1], 'http://a/b/c/g/'),
    ('/g'      , BASE_URI[1], 'http://a/g'),
    ('//g'     , BASE_URI[1], 'http://g'),
    # changed in RFC 2396bis
    #('?y'      , BASE_URI[1], 'http://a/b/c/?y'),
    ('?y'      , BASE_URI[1], 'http://a/b/c/d;p?y'),
    ('g?y'     , BASE_URI[1], 'http://a/b/c/g?y'),
    ('g?y/./x' , BASE_URI[1], 'http://a/b/c/g?y/./x'),
    ('g?y/../x', BASE_URI[1], 'http://a/b/c/g?y/../x'),
    ('g#s'     , BASE_URI[1], 'http://a/b/c/g#s'),
    ('g#s/./x' , BASE_URI[1], 'http://a/b/c/g#s/./x'),
    ('g#s/../x', BASE_URI[1], 'http://a/b/c/g#s/../x'),
    ('./'      , BASE_URI[1], 'http://a/b/c/'),
    ('../'     , BASE_URI[1], 'http://a/b/'),
    ('../g'    , BASE_URI[1], 'http://a/b/g'),
    ('../../'  , BASE_URI[1], 'http://a/'),
    ('../../g' , BASE_URI[1], 'http://a/g'),

    # http://gbiv.com/protocols/uri/test/rel_examples3.html
    # slashes in path params
    # all of these changed in RFC 2396bis
    ('g'       , BASE_URI[2], 'http://a/b/c/d;p=1/g'),
    ('./g'     , BASE_URI[2], 'http://a/b/c/d;p=1/g'),
    ('g/'      , BASE_URI[2], 'http://a/b/c/d;p=1/g/'),
    ('g?y'     , BASE_URI[2], 'http://a/b/c/d;p=1/g?y'),
    (';x'      , BASE_URI[2], 'http://a/b/c/d;p=1/;x'),
    ('g;x'     , BASE_URI[2], 'http://a/b/c/d;p=1/g;x'),
    ('g;x=1/./y', BASE_URI[2], 'http://a/b/c/d;p=1/g;x=1/y'),
    ('g;x=1/../y', BASE_URI[2], 'http://a/b/c/d;p=1/y'),
    ('./'      , BASE_URI[2], 'http://a/b/c/d;p=1/'),
    ('../'     , BASE_URI[2], 'http://a/b/c/'),
    ('../g'    , BASE_URI[2], 'http://a/b/c/g'),
    ('../../'  , BASE_URI[2], 'http://a/b/'),
    ('../../g' , BASE_URI[2], 'http://a/b/g'),

    # http://gbiv.com/protocols/uri/test/rel_examples4.html
    # double and triple slash, unknown scheme
    ('g:h'     , BASE_URI[3], 'g:h'),
    ('g'       , BASE_URI[3], 'fred:///s//a/b/g'),
    ('./g'     , BASE_URI[3], 'fred:///s//a/b/g'),
    ('g/'      , BASE_URI[3], 'fred:///s//a/b/g/'),
    ('/g'      , BASE_URI[3], 'fred:///g'),  # may change to fred:///s//a/g
    ('//g'     , BASE_URI[3], 'fred://g'),   # may change to fred:///s//g
    ('//g/x'   , BASE_URI[3], 'fred://g/x'), # may change to fred:///s//g/x
    ('///g'    , BASE_URI[3], 'fred:///g'),
    ('./'      , BASE_URI[3], 'fred:///s//a/b/'),
    ('../'     , BASE_URI[3], 'fred:///s//a/'),
    ('../g'    , BASE_URI[3], 'fred:///s//a/g'),
    ('../../'  , BASE_URI[3], 'fred:///s//'),    # may change to fred:///s//a/../
    ('../../g' , BASE_URI[3], 'fred:///s//g'),   # may change to fred:///s//a/../g
    ('../../../g', BASE_URI[3], 'fred:///s/g'),  # may change to fred:///s//a/../../g
    ('../../../../g', BASE_URI[3], 'fred:///g'), # may change to fred:///s//a/../../../g

    # http://gbiv.com/protocols/uri/test/rel_examples5.html
    # double and triple slash, well-known scheme
    ('g:h'     , BASE_URI[4], 'g:h'),
    ('g'       , BASE_URI[4], 'http:///s//a/b/g'),
    ('./g'     , BASE_URI[4], 'http:///s//a/b/g'),
    ('g/'      , BASE_URI[4], 'http:///s//a/b/g/'),
    ('/g'      , BASE_URI[4], 'http:///g'),  # may change to http:///s//a/g
    ('//g'     , BASE_URI[4], 'http://g'),   # may change to http:///s//g
    ('//g/x'   , BASE_URI[4], 'http://g/x'), # may change to http:///s//g/x
    ('///g'    , BASE_URI[4], 'http:///g'),
    ('./'      , BASE_URI[4], 'http:///s//a/b/'),
    ('../'     , BASE_URI[4], 'http:///s//a/'),
    ('../g'    , BASE_URI[4], 'http:///s//a/g'),
    ('../../'  , BASE_URI[4], 'http:///s//'),    # may change to http:///s//a/../
    ('../../g' , BASE_URI[4], 'http:///s//g'),   # may change to http:///s//a/../g
    ('../../../g', BASE_URI[4], 'http:///s/g'),  # may change to http:///s//a/../../g
    ('../../../../g', BASE_URI[4], 'http:///g'), # may change to http:///s//a/../../../g

    # from Dan Connelly's tests in http://www.w3.org/2000/10/swap/uripath.py
    ("bar:abc", "foo:xyz", "bar:abc"),
    ('../abc', 'http://example/x/y/z', 'http://example/x/abc'),
    ('http://example/x/abc', 'http://example2/x/y/z', 'http://example/x/abc'),
    ('../r', 'http://ex/x/y/z', 'http://ex/x/r'),
    ('q/r', 'http://ex/x/y', 'http://ex/x/q/r'),
    ('q/r#s', 'http://ex/x/y', 'http://ex/x/q/r#s'),
    ('q/r#s/t', 'http://ex/x/y', 'http://ex/x/q/r#s/t'),
    ('ftp://ex/x/q/r', 'http://ex/x/y', 'ftp://ex/x/q/r'),
    ('', 'http://ex/x/y', 'http://ex/x/y'),
    ('', 'http://ex/x/y/', 'http://ex/x/y/'),
    ('', 'http://ex/x/y/pdq', 'http://ex/x/y/pdq'),
    ('z/', 'http://ex/x/y/', 'http://ex/x/y/z/'),
    ('#Animal', 'file:/swap/test/animal.rdf', 'file:/swap/test/animal.rdf#Animal'),
    ('../abc', 'file:/e/x/y/z', 'file:/e/x/abc'),
    ('/example/x/abc', 'file:/example2/x/y/z', 'file:/example/x/abc'),
    ('../r', 'file:/ex/x/y/z', 'file:/ex/x/r'),
    ('/r', 'file:/ex/x/y/z', 'file:/r'),
    ('q/r', 'file:/ex/x/y', 'file:/ex/x/q/r'),
    ('q/r#s', 'file:/ex/x/y', 'file:/ex/x/q/r#s'),
    ('q/r#', 'file:/ex/x/y', 'file:/ex/x/q/r#'),
    ('q/r#s/t', 'file:/ex/x/y', 'file:/ex/x/q/r#s/t'),
    ('ftp://ex/x/q/r', 'file:/ex/x/y', 'ftp://ex/x/q/r'),
    ('', 'file:/ex/x/y', 'file:/ex/x/y'),
    ('', 'file:/ex/x/y/', 'file:/ex/x/y/'),
    ('', 'file:/ex/x/y/pdq', 'file:/ex/x/y/pdq'),
    ('z/', 'file:/ex/x/y/', 'file:/ex/x/y/z/'),
    ('file://meetings.example.com/cal#m1', 'file:/devel/WWW/2000/10/swap/test/reluri-1.n3', 'file://meetings.example.com/cal#m1'),
    ('file://meetings.example.com/cal#m1', 'file:/home/connolly/w3ccvs/WWW/2000/10/swap/test/reluri-1.n3', 'file://meetings.example.com/cal#m1'),
    ('./#blort', 'file:/some/dir/foo', 'file:/some/dir/#blort'),
    ('./#', 'file:/some/dir/foo', 'file:/some/dir/#'),
    # Ryan Lee
    ("./", "http://example/x/abc.efg", "http://example/x/"),

    #
    # Graham Klyne's tests
    # http://www.ninebynine.org/Software/HaskellUtils/Network/UriTest.xls
    # 01-31 are from Connelly's cases
    #
    # 32-49
    ('./q:r', 'http://ex/x/y', 'http://ex/x/q:r'),
    ('./p=q:r', 'http://ex/x/y', 'http://ex/x/p=q:r'),
    ('?pp/rr', 'http://ex/x/y?pp/qq', 'http://ex/x/y?pp/rr'),
    ('y/z', 'http://ex/x/y?pp/qq', 'http://ex/x/y/z'),
    ('local/qual@domain.org#frag', 'mailto:local', 'mailto:local/qual@domain.org#frag'),
    ('more/qual2@domain2.org#frag', 'mailto:local/qual1@domain1.org', 'mailto:local/more/qual2@domain2.org#frag'),
    ('y?q', 'http://ex/x/y?q', 'http://ex/x/y?q'),
    ('/x/y?q', 'http://ex?p', 'http://ex/x/y?q'),
    ('c/d',  'foo:a/b', 'foo:a/c/d'),
    ('/c/d', 'foo:a/b', 'foo:/c/d'),
    ('', 'foo:a/b?c#d', 'foo:a/b?c'),
    ('b/c', 'foo:a', 'foo:b/c'),
    ('../b/c', 'foo:/a/y/z', 'foo:/a/b/c'),
    ('./b/c', 'foo:a', 'foo:b/c'),
    ('/./b/c', 'foo:a', 'foo:/b/c'),
    ('../../d', 'foo://a//b/c', 'foo://a/d'),
    ('.', 'foo:a', 'foo:'),
    ('..', 'foo:a', 'foo:'),
    #
    # 50-57 (cf. TimBL comments --
    #  http://lists.w3.org/Archives/Public/uri/2003Feb/0028.html,
    #  http://lists.w3.org/Archives/Public/uri/2003Jan/0008.html)
    ('abc', 'http://example/x/y%2Fz', 'http://example/x/abc'),
    ('../../x%2Fabc', 'http://example/a/x/y/z', 'http://example/a/x%2Fabc'),
    ('../x%2Fabc', 'http://example/a/x/y%2Fz', 'http://example/a/x%2Fabc'),
    ('abc', 'http://example/x%2Fy/z', 'http://example/x%2Fy/abc'),
    ('q%3Ar', 'http://ex/x/y', 'http://ex/x/q%3Ar'),
    ('/x%2Fabc', 'http://example/x/y%2Fz', 'http://example/x%2Fabc'),
    ('/x%2Fabc', 'http://example/x/y/z', 'http://example/x%2Fabc'),
    ('/x%2Fabc', 'http://example/x/y%2Fz', 'http://example/x%2Fabc'),
    #
    # 70-77
    ('local2@domain2', 'mailto:local1@domain1?query1', 'mailto:local2@domain2'),
    ('local2@domain2?query2', 'mailto:local1@domain1', 'mailto:local2@domain2?query2'),
    ('local2@domain2?query2', 'mailto:local1@domain1?query1', 'mailto:local2@domain2?query2'),
    ('?query2', 'mailto:local@domain?query1', 'mailto:local@domain?query2'),
    ('local@domain?query2', 'mailto:?query1', 'mailto:local@domain?query2'),
    ('?query2', 'mailto:local@domain?query1', 'mailto:local@domain?query2'),
    ('http://example/a/b?c/../d', 'foo:bar', 'http://example/a/b?c/../d'),
    ('http://example/a/b#c/../d', 'foo:bar', 'http://example/a/b#c/../d'),
    #
    # 82-88
    ('http:this', 'http://example.org/base/uri', 'http:this'),
    ('http:this', 'http:base', 'http:this'),
    ('.//g', 'f:/a', 'f://g'),
    ('b/c//d/e', 'f://example.org/base/a', 'f://example.org/base/b/c//d/e'),
    ('m2@example.ord/c2@example.org', 'mid:m@example.ord/c@example.org', 'mid:m@example.ord/m2@example.ord/c2@example.org'),
    ('mini1.xml', 'file:///C:/DEV/Haskell/lib/HXmlToolbox-3.01/examples/', 'file:///C:/DEV/Haskell/lib/HXmlToolbox-3.01/examples/mini1.xml'),
    ('../b/c', 'foo:a/y/z', 'foo:a/b/c'),

]


# Test cases for Relativize() ================================================
relativize_test_cases = [
    ('s://ex/a', 's://ex', 'a', 'a'),
    ('s://ex/a', 's://ex/', 'a', 'a'),
    ('s://ex/a/b/c', 's://ex/a/d', 'b/c', 'b/c'),
    ('s://ex/b/b/c', 's://ex/a/d', '/b/b/c', None),
    ('s://ex/a/b/c', 's://ex/a/b/', 'c', 'c'),
    ('s://ex/a/b/c', 's://ex/b/../a/', 'b/c', 'b/c'),
    ('s://other.ex/a/b/c', 's://ex/a/d', None, None),
    ('s://ex/a/b/c', 's://other.ex/a/d', None, None),
    ('t://ex/a/b/c', 's://ex/a/d', None, None),
    ('s://ex/a/b/c', 't://ex/a/d', None, None),
    ('s://ex/a', 's://ex/b/c/d', '/a', None),
    ('s://ex/b/c/d', 's://ex/a', 'b/c/d', 'b/c/d'),
    ('s://ex/a/b/c?h', 's://ex/a/d?w', 'b/c?h', 'b/c?h'),
    ('s://ex/a/b/c#h', 's://ex/a/d#w', 'b/c#h', 'b/c#h'),
    ('s://ex/a/b/c?h#i', 's://ex/a/d?w#j', 'b/c?h#i', 'b/c?h#i'),
    ('s://ex/a#i', 's://ex/a', '#i', '#i'),
    ('s://ex/a?i', 's://ex/a', '?i', '?i'),

    # This is the kind of case which might indicate that we ought to always
    # return strings, and that returning `None` is dangerous.
    ('s://ex/a/b/', 's://ex/a/b/', '', ''),
    ('s://ex/a/b', 's://ex/a/b', '', ''),
    ('s://ex/', 's://ex/', '', ''),

    ('foo', 'bar', None, None),

    # This is the kind of case where we might want to instead return 'b/c'
    ('b/c', 's://ex/a/d', None, None),

    # Some tests specific to when we use isSubPath = False:
    ('s://ex/a/b/c', 's://ex/a/d/c', '../b/c', None),
    ('s://ex/a/b/c/', 's://ex/a/d/c', '../b/c/', None),
    ('s://ex/a/b/c/d', 's://ex/a/d/c/d', '../../b/c/d', None),
    ('s://ex/a/b/c', 's://ex/d/e/f', '/a/b/c', None),
    ('s://ex/a/b/', 's://ex/a/c/d/e', '../../b/', None),

    # Some tests to ensure that empty path segments don't cause problems.
    ('s://ex/a/b', 's://ex/a//b/c', '../../b', None),
    ('s://ex/a///b', 's://ex/a/', './//b', './//b'),
    ('s://ex/a/', 's://ex/a///b', '../../', None),
    ('s://ex/a//b/c', 's://ex/a/b', './/b/c', './/b/c')
]


# Test cases for URI reference syntax ========================================
good_uri_references = [
    'file:///foo/bar',
    'mailto:user@host?subject=blah',
    'dav:', # empty opaque part / rel-path allowed by RFC 2396bis
    'about:', # empty opaque part / rel-path allowed by RFC 2396bis
    #
    # the following test cases are from a Perl script by David A. Wheeler
    # at http://www.dwheeler.com/secure-programs/url.pl
    'http://www.yahoo.com',
    'http://www.yahoo.com/',
    'http://1.2.3.4/',
    'http://www.yahoo.com/stuff',
    'http://www.yahoo.com/stuff/',
    'http://www.yahoo.com/hello%20world/',
    'http://www.yahoo.com?name=obi',
    'http://www.yahoo.com?name=obi+wan&status=jedi',
    'http://www.yahoo.com?onery',
    'http://www.yahoo.com#bottom',
    'http://www.yahoo.com/yelp.html#bottom',
    'https://www.yahoo.com/',
    'ftp://www.yahoo.com/',
    'ftp://www.yahoo.com/hello',
    'demo.txt',
    'demo/hello.txt',
    'demo/hello.txt?query=hello#fragment',
    '/cgi-bin/query?query=hello#fragment',
    '/demo.txt',
    '/hello/demo.txt',
    'hello/demo.txt',
    '/',
    '',
    '#',
    '#here',
    # Wheeler's script says these are invalid, but they aren't
    'http://www.yahoo.com?name=%00%01',
    'http://www.yaho%6f.com',
    'http://www.yahoo.com/hello%00world/',
    'http://www.yahoo.com/hello+world/',
    'http://www.yahoo.com?name=obi&',
    'http://www.yahoo.com?name=obi&type=',
    'http://www.yahoo.com/yelp.html#',
    '//',
    #
    # the following test cases are from a Haskell program by Graham Klyne
    # at http://www.ninebynine.org/Software/HaskellUtils/Network/URITest.hs
    'http://example.org/aaa/bbb#ccc',
    'mailto:local@domain.org',
    'mailto:local@domain.org#frag',
    'HTTP://EXAMPLE.ORG/AAA/BBB#CCC',
    '//example.org/aaa/bbb#ccc',
    '/aaa/bbb#ccc',
    'bbb#ccc',
    '#ccc',
    '#',
    #'/', # repeat of test above
    "A'C",
    #-- escapes
    'http://example.org/aaa%2fbbb#ccc',
    'http://example.org/aaa%2Fbbb#ccc',
    '%2F',
    'aaa%2Fbbb',
    #-- ports
    'http://example.org:80/aaa/bbb#ccc',
    'http://example.org:/aaa/bbb#ccc',
    'http://example.org./aaa/bbb#ccc',
    'http://example.123./aaa/bbb#ccc',
    #-- bare authority
    'http://example.org',
    #-- IPv6 literals (from RFC2732):
    'http://[FEDC:BA98:7654:3210:FEDC:BA98:7654:3210]:80/index.html',
    'http://[1080:0:0:0:8:800:200C:417A]/index.html',
    'http://[3ffe:2a00:100:7031::1]',
    'http://[1080::8:800:200C:417A]/foo',
    'http://[::192.9.5.5]/ipng',
    'http://[::FFFF:129.144.52.38]:80/index.html',
    'http://[2010:836B:4179::836B:4179]',
    '//[2010:836B:4179::836B:4179]',
    #-- Random other things that crop up
    'http://example/Andr&#567;',
    'file:///C:/DEV/Haskell/lib/HXmlToolbox-3.01/examples/',
    ]

bad_uri_references = [
    'beepbeep\x07\x07',
    '\n',
    '::', # not OK, per Roy Fielding on the W3C uri list on 2004-04-01
    #
    # the following test cases are from a Perl script by David A. Wheeler
    # at http://www.dwheeler.com/secure-programs/url.pl
    'http://www yahoo.com',
    'http://www.yahoo.com/hello world/',
    'http://www.yahoo.com/yelp.html#"',
    #
    # the following test cases are from a Haskell program by Graham Klyne
    # at http://www.ninebynine.org/Software/HaskellUtils/Network/URITest.hs
    '[2010:836B:4179::836B:4179]',
    ' ',
    '%',
    'A%Z',
    '%ZZ',
    '%AZ',
    'A C',
    r"A\'C",
    'A`C',
    'A<C',
    'A>C',
    'A^C',
    r'A\\C',
    'A{C',
    'A|C',
    'A}C',
    'A[C',
    'A]C',
    'A[**]C',
    'http://[xyz]/',
    'http://]/',
    'http://example.org/[2010:836B:4179::836B:4179]',
    'http://example.org/abc#[2010:836B:4179::836B:4179]',
    'http://example.org/xxx/[qwerty]#a[b]',
    #
    # from a post to the W3C uri list on 2004-02-17
    'http://w3c.org:80path1/path2',
    ]

# Test cases for UriToOsPath =================================================
#
# Each tuple is (URI, expected for Windows, expected for POSIX).
# None means a UriException is expected.
file_uris = [
    ('file:x/y/z',         r'x\y\z',       'x/y/z'),
    ('file:/x/y/z',        r'\x\y\z',      '/x/y/z'),
    ('file:/x/y/z/',       '\\x\\y\\z\\',  '/x/y/z/'),
    ('file:///x/y/z',      r'\x\y\z',      '/x/y/z'),
    ('file:///x/y/z/',     '\\x\\y\\z\\',  '/x/y/z/'),
    ('file:///x/y/z?q1=1&q2=2', r'\x\y\z', '/x/y/z'),
    ('file:///x/y/z#frag', r'\x\y\z',      '/x/y/z'),
    ('file:///c:/x/y/z',   r'C:\x\y\z',    '/c:/x/y/z'),
    ('file:///c|/x/y/z',   r'C:\x\y\z',    '/c|/x/y/z'),
    ('file:///c:/x:/y/z',  r'C:\x:\y\z',   '/c:/x:/y/z'),
    ('file://c:/x/y/z',    r'C:\x\y\z',    None),
    ('file://host/share/x/y/z', r'\\host\share\x\y\z', None),
    ('file:////host/share/x/y/z', r'\\host\share\x\y\z', '//host/share/x/y/z'),
    ('file://host/c:/x/y/z', r'\\host\c:\x\y\z', None),
    ('file://localhost/x/y/z', r'\x\y\z',  '/x/y/z'),
    ('file://localhost/c:/x/y/z', r'C:\x\y\z', '/c:/x/y/z'),
    ('file:///C:%5Cx%5Cy%5Cz', r'C:\x\y\z', r'/C:\x\y\z'),
    ('file:///C:%2Fx%2Fy%2Fz', r'C:\x\y\z', r'/C:\/x\/y\/z'),
    ('file:///water%3D%E6%B0%B4', '\\water=\xe6\xb0\xb4', '/water=\xe6\xb0\xb4'),
    (u'file:///water%3D%E6%B0%B4', u'\\water=\u6c34', u'/water=\u6c34'),
    ]

# Test cases for OsPathToUri =================================================
#
# Each tuple is (OS path, expected for Windows, expected for POSIX).
# None means a UriException is expected.

if iri.WINDOWS_SLASH_COMPAT:
    # if treating '/' as alias for '\' on Windows
    file_paths = [
        # relative path
        ('x/y/z',     'file:x/y/z',              'file:x/y/z'),
        # absolute path
        ('/x/y/z',    'file:///x/y/z',           'file:///x/y/z'),
        # authority + absolute path
        ('//x/y/z',   'file://x/y/z',            'file:////x/y/z'),
        # authority + absolute path with extra leading slashes
        ('///x/y/z',  'file:///x/y/z',           'file://///x/y/z'),
    ]
else:
    # if NOT treating '/' as alias for '\' on Windows
    file_paths = [
        ('x/y/z',     'file:x%2Fy%2Fz',          'file:x/y/z'),
        ('/x/y/z',    'file:%2Fx%2Fy%2Fz',       'file:///x/y/z'),
        ('//x/y/z',   'file:%2F%2Fx%2Fy%2Fz',    'file:////x/y/z'),
        ('///x/y/z',  'file:%2F%2F%2Fx%2Fy%2Fz', 'file://///x/y/z'),
    ]

file_paths += [
    # absolute windows path, with drivespec
    ('C:\\',      'file:///C:/',             'file:C%3A%5C'),
    (r'C:\a\b\c', 'file:///C:/a/b/c',        'file:C%3A%5Ca%5Cb%5Cc'),
    # absolute windows path, no drivespec
    (r'\a\b\c',   'file:///a/b/c',           'file:%5Ca%5Cb%5Cc'),
    # relative windows path
    (r'a\b\c',    'file:a/b/c',              'file:a%5Cb%5Cc'),
    # absolute windows path with dot segments
    (r'C:\a\b\c\d\..\..\C', 'file:///C:/a/b/C',
     'file:C%3A%5Ca%5Cb%5Cc%5Cd%5C..%5C..%5CC'),
    # windows path with space chars
    (r'C:\Documents and Settings\Your Name\Local Settings\Temp',
     'file:///C:/Documents%20and%20Settings/Your%20Name/Local%20Settings/Temp',
     'file:C%3A%5CDocuments%20and%20Settings%5CYour%20Name%5CLocal%20Settings%5CTemp'),
    # relative windows path with dot segments
    ('.',         'file:.',                  'file:.'),
    ('..\Y\Z',    'file:../Y/Z',             'file:..%5CY%5CZ'),
    # reserved-character bytes in path
    ('a!;b?c#d^e()', 'file:a%21%3Bb%3Fc%23d%5Ee%28%29',
     'file:a%21%3Bb%3Fc%23d%5Ee%28%29'),
    # non-ASCII characters in path
    (u'98.6\xb0F', 'file:98.6%C2%B0F',       'file:98.6%C2%B0F'),
    (u'water=\u6c34', 'file:water%3D%E6%B0%B4', 'file:water%3D%E6%B0%B4'),
    # UNC path
    (r'\\h\s\x\y\z', 'file://h/s/x/y/z',     'file:%5C%5Ch%5Cs%5Cx%5Cy%5Cz'),
    (r'\\h\$c$\x\y\z', 'file://h/%24c%24/x/y/z',
     'file:%5C%5Ch%5C%24c%24%5Cx%5Cy%5Cz'),
    (r'\\localhost\share\x\y\z', 'file://localhost/share/x/y/z',
     'file:%5C%5Clocalhost%5Cshare%5Cx%5Cy%5Cz'),
    ]


# Test cases for NormalizeCase ===============================================
#
# Each tuple is (URI, expected w/o normalizing host, expected with norm. host)
case_normalization_tests = [
    ('HTTP://www.EXAMPLE.com/', 'http://www.EXAMPLE.com/', 'http://www.example.com/'),
    ('example://A/b/c/%7bfoo%7d', 'example://A/b/c/%7Bfoo%7D', 'example://a/b/c/%7Bfoo%7D'),
    ]


# Test cases for NormalizePercentEncoding ====================================
#
# Each tuple is (URI, expected)
pct_enc_normalization_tests = [
    ('http://host/%7Euser/x/y/z', 'http://host/~user/x/y/z'),
    ('http://host/%7euser/x/y/z', 'http://host/~user/x/y/z'),
    ('example://A/b/c/%7bfoo%7d', 'example://A/b/c/%7bfoo%7d'),
    ]


# Test cases for NormalizePathSegments =======================================
#
# Each tuple is (path, expected)
path_segment_normalization_tests = [
    ('/a/b/../../c', '/c'),
    ('a/b/../../c', 'a/b/../../c'),
    ('/a/b/././c', '/a/b/c'),
    ('a/b/././c', 'a/b/././c'),
    ('/a/b/../c/././d', '/a/c/d'),
    ('a/b/../c/././d', 'a/b/../c/././d'),
    ]


# Test cases for MakeUrllibSafe ==============================================
#
# Each tuple is (URI, expected)
make_urllib_safe_tests = [
    # Martin Duerst's IDN tests in http://www.w3.org/2004/04/uri-rel-test.html
    ('http://www.w%33.org', 'http://www.w3.org'), # 101
    ('http://r%C3%A4ksm%C3%B6rg%C3%A5s.josefsson.org', 'http://xn--rksmrgs-5wao1o.josefsson.org'), # 111
    ('http://%E7%B4%8D%E8%B1%86.w3.mag.keio.ac.jp', 'http://xn--99zt52a.w3.mag.keio.ac.jp'), # 112
    ('http://www.%E3%81%BB%E3%82%93%E3%81%A8%E3%81%86%E3%81%AB%E3%81%AA%E3%81'
     '%8C%E3%81%84%E3%82%8F%E3%81%91%E3%81%AE%E3%82%8F%E3%81%8B%E3%82%89%E3%81'
     '%AA%E3%81%84%E3%81%A9%E3%82%81%E3%81%84%E3%82%93%E3%82%81%E3%81%84%E3%81'
     '%AE%E3%82%89%E3%81%B9%E3%82%8B%E3%81%BE%E3%81%A0%E3%81%AA%E3%81%8C%E3%81'
     '%8F%E3%81%97%E3%81%AA%E3%81%84%E3%81%A8%E3%81%9F%E3%82%8A%E3%81%AA%E3%81'
     '%84.w3.mag.keio.ac.jp/',
     'http://www.xn--n8jaaaaai5bhf7as8fsfk3jnknefdde3fg11amb5gzdb4wi9bya3kc6lr'
     'a.w3.mag.keio.ac.jp/'), # 121
    ('http://%E3%81%BB%E3%82%93%E3%81%A8%E3%81%86%E3%81%AB%E3%81%AA%E3%81%8C'
     '%E3%81%84%E3%82%8F%E3%81%91%E3%81%AE%E3%82%8F%E3%81%8B%E3%82%89%E3%81%AA'
     '%E3%81%84%E3%81%A9%E3%82%81%E3%81%84%E3%82%93%E3%82%81%E3%81%84%E3%81%AE'
     '%E3%82%89%E3%81%B9%E3%82%8B%E3%81%BE%E3%81%A0%E3%81%AA%E3%81%8C%E3%81%8F'
     '%E3%81%97%E3%81%AA%E3%81%84%E3%81%A8%E3%81%9F%E3%82%8A%E3%81%AA%E3%81%84'
     '.%E3%81%BB%E3%82%93%E3%81%A8%E3%81%86%E3%81%AB%E3%81%AA%E3%81%8C%E3%81'
     '%84%E3%82%8F%E3%81%91%E3%81%AE%E3%82%8F%E3%81%8B%E3%82%89%E3%81%AA%E3%81'
     '%84%E3%81%A9%E3%82%81%E3%81%84%E3%82%93%E3%82%81%E3%81%84%E3%81%AE%E3%82'
     '%89%E3%81%B9%E3%82%8B%E3%81%BE%E3%81%A0%E3%81%AA%E3%81%8C%E3%81%8F%E3%81'
     '%97%E3%81%AA%E3%81%84%E3%81%A8%E3%81%9F%E3%82%8A%E3%81%AA%E3%81%84.%E3'
     '%81%BB%E3%82%93%E3%81%A8%E3%81%86%E3%81%AB%E3%81%AA%E3%81%8C%E3%81%84%E3'
     '%82%8F%E3%81%91%E3%81%AE%E3%82%8F%E3%81%8B%E3%82%89%E3%81%AA%E3%81%84%E3'
     '%81%A9%E3%82%81%E3%81%84%E3%82%93%E3%82%81%E3%81%84%E3%81%AE%E3%82%89%E3'
     '%81%B9%E3%82%8B%E3%81%BE%E3%81%A0%E3%81%AA%E3%81%8C%E3%81%8F%E3%81%97%E3'
     '%81%AA%E3%81%84%E3%81%A8%E3%81%9F%E3%82%8A%E3%81%AA%E3%81%84.w3.mag.keio'
     '.ac.jp/',
     'http://xn--n8jaaaaai5bhf7as8fsfk3jnknefdde3fg11amb5gzdb4wi9bya3kc6lra.xn'
     '--n8jaaaaai5bhf7as8fsfk3jnknefdde3fg11amb5gzdb4wi9bya3kc6lra.xn--n8jaaaa'
     'ai5bhf7as8fsfk3jnknefdde3fg11amb5gzdb4wi9bya3kc6lra.w3.mag.keio.ac.jp/'), #122
    # Unicode versions of above
    (u'http://www.w%33.org', u'http://www.w3.org'), # 101
    (u'http://r%C3%A4ksm%C3%B6rg%C3%A5s.josefsson.org', u'http://xn--rksmrgs-5wao1o.josefsson.org'), # 111
    (u'http://%E7%B4%8D%E8%B1%86.w3.mag.keio.ac.jp', u'http://xn--99zt52a.w3.mag.keio.ac.jp'), # 112
    (u'http://www.%E3%81%BB%E3%82%93%E3%81%A8%E3%81%86%E3%81%AB%E3%81%AA%E3%81'
     u'%8C%E3%81%84%E3%82%8F%E3%81%91%E3%81%AE%E3%82%8F%E3%81%8B%E3%82%89%E3%81'
     u'%AA%E3%81%84%E3%81%A9%E3%82%81%E3%81%84%E3%82%93%E3%82%81%E3%81%84%E3%81'
     u'%AE%E3%82%89%E3%81%B9%E3%82%8B%E3%81%BE%E3%81%A0%E3%81%AA%E3%81%8C%E3%81'
     u'%8F%E3%81%97%E3%81%AA%E3%81%84%E3%81%A8%E3%81%9F%E3%82%8A%E3%81%AA%E3%81'
     u'%84.w3.mag.keio.ac.jp/',
     u'http://www.xn--n8jaaaaai5bhf7as8fsfk3jnknefdde3fg11amb5gzdb4wi9bya3kc6lr'
     u'a.w3.mag.keio.ac.jp/'), # 121
    (u'http://%E3%81%BB%E3%82%93%E3%81%A8%E3%81%86%E3%81%AB%E3%81%AA%E3%81%8C'
     u'%E3%81%84%E3%82%8F%E3%81%91%E3%81%AE%E3%82%8F%E3%81%8B%E3%82%89%E3%81%AA'
     u'%E3%81%84%E3%81%A9%E3%82%81%E3%81%84%E3%82%93%E3%82%81%E3%81%84%E3%81%AE'
     u'%E3%82%89%E3%81%B9%E3%82%8B%E3%81%BE%E3%81%A0%E3%81%AA%E3%81%8C%E3%81%8F'
     u'%E3%81%97%E3%81%AA%E3%81%84%E3%81%A8%E3%81%9F%E3%82%8A%E3%81%AA%E3%81%84'
     u'.%E3%81%BB%E3%82%93%E3%81%A8%E3%81%86%E3%81%AB%E3%81%AA%E3%81%8C%E3%81'
     u'%84%E3%82%8F%E3%81%91%E3%81%AE%E3%82%8F%E3%81%8B%E3%82%89%E3%81%AA%E3%81'
     u'%84%E3%81%A9%E3%82%81%E3%81%84%E3%82%93%E3%82%81%E3%81%84%E3%81%AE%E3%82'
     u'%89%E3%81%B9%E3%82%8B%E3%81%BE%E3%81%A0%E3%81%AA%E3%81%8C%E3%81%8F%E3%81'
     u'%97%E3%81%AA%E3%81%84%E3%81%A8%E3%81%9F%E3%82%8A%E3%81%AA%E3%81%84.%E3'
     u'%81%BB%E3%82%93%E3%81%A8%E3%81%86%E3%81%AB%E3%81%AA%E3%81%8C%E3%81%84%E3'
     u'%82%8F%E3%81%91%E3%81%AE%E3%82%8F%E3%81%8B%E3%82%89%E3%81%AA%E3%81%84%E3'
     u'%81%A9%E3%82%81%E3%81%84%E3%82%93%E3%82%81%E3%81%84%E3%81%AE%E3%82%89%E3'
     u'%81%B9%E3%82%8B%E3%81%BE%E3%81%A0%E3%81%AA%E3%81%8C%E3%81%8F%E3%81%97%E3'
     u'%81%AA%E3%81%84%E3%81%A8%E3%81%9F%E3%82%8A%E3%81%AA%E3%81%84.w3.mag.keio'
     u'.ac.jp/',
     u'http://xn--n8jaaaaai5bhf7as8fsfk3jnknefdde3fg11amb5gzdb4wi9bya3kc6lra.xn'
     u'--n8jaaaaai5bhf7as8fsfk3jnknefdde3fg11amb5gzdb4wi9bya3kc6lra.xn--n8jaaaa'
     u'ai5bhf7as8fsfk3jnknefdde3fg11amb5gzdb4wi9bya3kc6lra.w3.mag.keio.ac.jp/'), #122
    ]

win_make_urllib_safe_tests = [
    ('file:///C:/path/to/file', 'file:///C|/path/to/file'),
    ('http://foo/bar:baz/', 'http://foo/bar:baz/'),
    ]


# Test cases for public_id_to_urn and urn_to_public_id =============================
#
public_id_tests = [
    # examples from RFC 3151
    ("ISO/IEC 10179:1996//DTD DSSSL Architecture//EN",
     "urn:publicid:ISO%2FIEC+10179%3A1996:DTD+DSSSL+Architecture:EN"),
    ("ISO 8879:1986//ENTITIES Added Latin 1//EN",
     "urn:publicid:ISO+8879%3A1986:ENTITIES+Added+Latin+1:EN"),
    ("-//OASIS//DTD DocBook XML V4.1.2//EN",
     "urn:publicid:-:OASIS:DTD+DocBook+XML+V4.1.2:EN"),
    ("+//IDN example.org//DTD XML Bookmarks 1.0//EN//XML",
     "urn:publicid:%2B:IDN+example.org:DTD+XML+Bookmarks+1.0:EN:XML"),
    ("-//ArborText::prod//DTD Help Document::19970708//EN",
     "urn:publicid:-:ArborText;prod:DTD+Help+Document;19970708:EN"),
    ("foo",
     "urn:publicid:foo"),
    ("3+3=6",
     #"urn:publicid:3%2B3=6" # RFC 2396
     "urn:publicid:3%2B3%3D6"), # RFC 2396bis
    ("-//Acme, Inc.//DTD Book Version 1.0",
     #"urn:publicid:-:Acme,+Inc.:DTD+Book+Version+1.0" # RFC 2396
     "urn:publicid:-:Acme%2C+Inc.:DTD+Book+Version+1.0"), # RFC 2396bis
]

# Test cases for percent_encode and percent_decode =============================
#
percent_encode_tests = [
    # Empty string
    ('', ''),
    (u'', u''),
    # The unreserved set: the only characters that don't need to be
    # percent-encoded (it's OK to percent-encode them, though, as it
    # will still produce an equivalent URI). We expect that they won't
    # be percent-encoded.
    ('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~',
     'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~'),
    (u'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~',
     u'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~'),
    # The reserved set: characters that need to be percent-encoded when they
    # are not being used for their reserved purpose. We expect that they
    # will all be percent-encoded.
    (":/?#[]@!$&'()*+,;=",
     '%3A%2F%3F%23%5B%5D%40%21%24%26%27%28%29%2A%2B%2C%3B%3D'),
    (u":/?#[]@!$&'()*+,;=",
     u'%3A%2F%3F%23%5B%5D%40%21%24%26%27%28%29%2A%2B%2C%3B%3D'),
    # Disallowed characters: characters not in the reserved or unreserved
    # sets; these must be converted to percent-encoded octets, always.
    # Basically this is all of Unicode, which would be impractical to test.
    # We'll just test some reasonable subsets.
    #
    #   1. the rest of printable ASCII
    (' %^{}|\\"<>`',
     '%20%25%5E%7B%7D%7C%5C%22%3C%3E%60'),
    (u' %^{}|\\"<>`',
     u'%20%25%5E%7B%7D%7C%5C%22%3C%3E%60'),
    #   2. the ASCII / C0 control set
    (''.join(map(chr, xrange(32))) + '\x7f',
     '%00%01%02%03%04%05%06%07%08%09%0A%0B%0C%0D%0E%0F' \
     '%10%11%12%13%14%15%16%17%18%19%1A%1B%1C%1D%1E%1F%7F'),
    (u''.join(map(unichr, xrange(32))) + u'\x7f',
     u'%00%01%02%03%04%05%06%07%08%09%0A%0B%0C%0D%0E%0F' \
     u'%10%11%12%13%14%15%16%17%18%19%1A%1B%1C%1D%1E%1F%7F'),
    #   3. non-ASCII (ISO-8859-* range)
    (''.join(map(chr, xrange(128, 256))),
     '%80%81%82%83%84%85%86%87%88%89%8A%8B%8C%8D%8E%8F' \
     '%90%91%92%93%94%95%96%97%98%99%9A%9B%9C%9D%9E%9F' \
     '%A0%A1%A2%A3%A4%A5%A6%A7%A8%A9%AA%AB%AC%AD%AE%AF' \
     '%B0%B1%B2%B3%B4%B5%B6%B7%B8%B9%BA%BB%BC%BD%BE%BF' \
     '%C0%C1%C2%C3%C4%C5%C6%C7%C8%C9%CA%CB%CC%CD%CE%CF' \
     '%D0%D1%D2%D3%D4%D5%D6%D7%D8%D9%DA%DB%DC%DD%DE%DF' \
     '%E0%E1%E2%E3%E4%E5%E6%E7%E8%E9%EA%EB%EC%ED%EE%EF' \
     '%F0%F1%F2%F3%F4%F5%F6%F7%F8%F9%FA%FB%FC%FD%FE%FF'),
    (u''.join(map(unichr, xrange(128, 256))),
     u'%C2%80%C2%81%C2%82%C2%83%C2%84%C2%85%C2%86%C2%87' \
     u'%C2%88%C2%89%C2%8A%C2%8B%C2%8C%C2%8D%C2%8E%C2%8F' \
     u'%C2%90%C2%91%C2%92%C2%93%C2%94%C2%95%C2%96%C2%97' \
     u'%C2%98%C2%99%C2%9A%C2%9B%C2%9C%C2%9D%C2%9E%C2%9F' \
     u'%C2%A0%C2%A1%C2%A2%C2%A3%C2%A4%C2%A5%C2%A6%C2%A7' \
     u'%C2%A8%C2%A9%C2%AA%C2%AB%C2%AC%C2%AD%C2%AE%C2%AF' \
     u'%C2%B0%C2%B1%C2%B2%C2%B3%C2%B4%C2%B5%C2%B6%C2%B7' \
     u'%C2%B8%C2%B9%C2%BA%C2%BB%C2%BC%C2%BD%C2%BE%C2%BF' \
     u'%C3%80%C3%81%C3%82%C3%83%C3%84%C3%85%C3%86%C3%87' \
     u'%C3%88%C3%89%C3%8A%C3%8B%C3%8C%C3%8D%C3%8E%C3%8F' \
     u'%C3%90%C3%91%C3%92%C3%93%C3%94%C3%95%C3%96%C3%97' \
     u'%C3%98%C3%99%C3%9A%C3%9B%C3%9C%C3%9D%C3%9E%C3%9F' \
     u'%C3%A0%C3%A1%C3%A2%C3%A3%C3%A4%C3%A5%C3%A6%C3%A7' \
     u'%C3%A8%C3%A9%C3%AA%C3%AB%C3%AC%C3%AD%C3%AE%C3%AF' \
     u'%C3%B0%C3%B1%C3%B2%C3%B3%C3%B4%C3%B5%C3%B6%C3%B7' \
     u'%C3%B8%C3%B9%C3%BA%C3%BB%C3%BC%C3%BD%C3%BE%C3%BF'),
    #   4. U+0100 to low surrogate range, in big steps
    (u''.join(map(unichr, xrange(256, 55296, 1024))) + u'\ud7ff',
     u'%C4%80%D4%80%E0%A4%80%E0%B4%80%E1%84%80%E1%94%80' \
     u'%E1%A4%80%E1%B4%80%E2%84%80%E2%94%80%E2%A4%80%E2' \
     u'%B4%80%E3%84%80%E3%94%80%E3%A4%80%E3%B4%80%E4%84' \
     u'%80%E4%94%80%E4%A4%80%E4%B4%80%E5%84%80%E5%94%80' \
     u'%E5%A4%80%E5%B4%80%E6%84%80%E6%94%80%E6%A4%80%E6' \
     u'%B4%80%E7%84%80%E7%94%80%E7%A4%80%E7%B4%80%E8%84' \
     u'%80%E8%94%80%E8%A4%80%E8%B4%80%E9%84%80%E9%94%80' \
     u'%E9%A4%80%E9%B4%80%EA%84%80%EA%94%80%EA%A4%80%EA' \
     u'%B4%80%EB%84%80%EB%94%80%EB%A4%80%EB%B4%80%EC%84' \
     u'%80%EC%94%80%EC%A4%80%EC%B4%80%ED%84%80%ED%94%80%ED%9F%BF'),
    #  5. U+E000 through U+FFFD, in big steps
    (u''.join(map(unichr, xrange(57344, 65534, 256))) + u'\ufffd',
     u'%EE%80%80%EE%84%80%EE%88%80%EE%8C%80%EE%90%80%EE' \
     u'%94%80%EE%98%80%EE%9C%80%EE%A0%80%EE%A4%80%EE%A8' \
     u'%80%EE%AC%80%EE%B0%80%EE%B4%80%EE%B8%80%EE%BC%80' \
     u'%EF%80%80%EF%84%80%EF%88%80%EF%8C%80%EF%90%80%EF' \
     u'%94%80%EF%98%80%EF%9C%80%EF%A0%80%EF%A4%80%EF%A8' \
     u'%80%EF%AC%80%EF%B0%80%EF%B4%80%EF%B8%80%EF%BC%80%EF%BF%BD'),
    #  6. non-BMP tests moved to body of test, below
]


class Test_file_uri_localhost_equiv(unittest.TestCase):
    '''uridict implementation - file:/// and file://localhost/ equivalence'''
    def test_uri_dict(self):
        '''equivalent key in UriDict'''
        uris = irihelpers.uridict()
        uris['file:///path/to/resource'] = 0
        self.assert_('file://localhost/path/to/resource' in uris, 'RFC 1738 localhost support failed')

    def test_equiv_keys(self):
        '''value of 2 equivalent keys'''
        uris = irihelpers.uridict()
        uris['file:///path/to/resource'] = 1
        uris['file://localhost/path/to/resource'] = 2
        self.assertEqual(2, uris['file:///path/to/resource'], 'RFC 1738 localhost support failed')

class Test_case_equiv(unittest.TestCase):
    '''uridict implementation - case equivalence'''
    def test_case_normalization(self):
        '''case normalization'''
        uris = irihelpers.uridict()
        for uri, expected, junk in case_normalization_tests:
            uris[uri] = 1
            uris[expected] = 2
            self.assertEqual(2, uris[uri], '%s and %s equivalence' % (uri, expected))

    def test_percent_encoding_equivalence(self):
        '''percent-encoding equivalence'''
        uris = irihelpers.uridict()
        for uri, expected in pct_enc_normalization_tests:
            uris[uri] = 1
            uris[expected] = 2
            self.assertEqual(2, uris[uri], '%s and %s equivalence' % (uri, expected))

class Test_percent_encode_decode(unittest.TestCase):
    '''PercentEncode and PercentDecode'''
    #def test_percent_encode(self):
    @classmethod
    def create_test_percent_encodes(cls):
        '''Percent encode'''
        for count, (unencoded, encoded) in enumerate(percent_encode_tests):
            #print "Creating test", "test_percent_encode_%i"%count
            def test_percent_encode_template(self, count=count, unencoded=unencoded, encoded=encoded):
                if len(unencoded) > 10:
                    test_title = unencoded[:11] + '...'
                else:
                    test_title = unencoded
                self.assertEqual(encoded, iri.percent_encode(unencoded))
                self.assertEqual(unencoded, iri.percent_decode(encoded))
            setattr(cls, "test_percent_encode_%i"%count, test_percent_encode_template)

    # non-BMP tests:
    #     a couple of random chars from U+10000 to U+10FFFD.
    #
    # This string will be length 2 or 4 depending on how Python
    # was built. Either way, it should result in the same percent-
    # encoded sequence, which should decode back to the original
    # representation.
    def test_non_bmp1(self):
        '''non-BMP characters: u""\U00010000\U0010FFFD""'''
        unencoded = u'\U00010000\U0010FFFD'
        encoded = u'%F0%90%80%80%F4%8F%BF%BD'
        self.assertEqual(encoded, iri.percent_encode(unencoded), "u'\U00010000\U0010FFFD'")
        self.assertEqual(unencoded, iri.percent_decode(encoded), "u'\U00010000\U0010FFFD'")

    # This string will be length 4, regardless of how Python was
    # built. However, if Python was built with wide (UCS-4) chars,
    # PercentDecode will generate an optimal string (length: 2).
    def test_non_bmp2(self):
        '''non-BMP characters: u"\ud800\udc00\udbff\udffd"'''
        unencoded_in = u'\ud800\udc00\udbff\udffd'
        encoded = u'%F0%90%80%80%F4%8F%BF%BD'
        unencoded_out = u'\U00010000\U0010FFFD'
        self.assertEqual(encoded, iri.percent_encode(unencoded_in), "u'\ud800\udc00\udbff\udffd'")
        self.assertEqual(unencoded_out, iri.percent_decode(encoded), "u'\ud800\udc00\udbff\udffd'")

    # test a few iso-8859-n variations just to make sure
    # iso-8859-1 isn't special
    def test_non_bmp3(self):
        '''non-BMP characters 3'''
        unencoded = ''.join(map(chr, range(256)))
        encoded = '%00%01%02%03%04%05%06%07%08%09%0A%0B%0C%0D%0E%0F' \
                  '%10%11%12%13%14%15%16%17%18%19%1A%1B%1C%1D%1E%1F' \
                  '%20%21%22%23%24%25%26%27%28%29%2A%2B%2C-.%2F' \
                  '0123456789%3A%3B%3C%3D%3E%3F%40' \
                  'ABCDEFGHIJKLMNOPQRSTUVWXYZ%5B%5C%5D%5E_%60' \
                  'abcdefghijklmnopqrstuvwxyz%7B%7C%7D~' \
                  '%7F%80%81%82%83%84%85%86%87%88%89%8A%8B%8C%8D%8E%8F' \
                  '%90%91%92%93%94%95%96%97%98%99%9A%9B%9C%9D%9E%9F' \
                  '%A0%A1%A2%A3%A4%A5%A6%A7%A8%A9%AA%AB%AC%AD%AE%AF' \
                  '%B0%B1%B2%B3%B4%B5%B6%B7%B8%B9%BA%BB%BC%BD%BE%BF' \
                  '%C0%C1%C2%C3%C4%C5%C6%C7%C8%C9%CA%CB%CC%CD%CE%CF' \
                  '%D0%D1%D2%D3%D4%D5%D6%D7%D8%D9%DA%DB%DC%DD%DE%DF' \
                  '%E0%E1%E2%E3%E4%E5%E6%E7%E8%E9%EA%EB%EC%ED%EE%EF' \
                  '%F0%F1%F2%F3%F4%F5%F6%F7%F8%F9%FA%FB%FC%FD%FE%FF'
        for part in (1,2,3,15):
            enc_name = 'iso-8859-%d' % part
            try:
                codecs.lookup(enc_name)
            except LookupError:
                warnings.warn('Not supported on this platform')
                continue
            self.assertEqual(encoded, iri.percent_encode(unencoded, encoding=enc_name), enc_name)
            self.assertEqual(unencoded, iri.percent_decode(encoded, encoding=enc_name), enc_name)

    # utf-16be: why not?
    #unencoded = u'a test string...\x00\xe9...\x20\x22...\xd8\x00\xdc\x00'
    #encoded = u'a%20test%20string...\u00e9...%20%22...%D8%00%DC%00'

Test_percent_encode_decode.create_test_percent_encodes()

class Test_urns_pubids(unittest.TestCase):
    '''URNs & PubIDs'''
    def test_urns_pubids(self):
        for publicid, urn in public_id_tests:
            self.assertEqual(urn, iri.public_id_to_urn(publicid), "public_id_to_urn: %s"%publicid)

        for publicid, urn in public_id_tests:
            self.assertEqual(publicid, iri.urn_to_public_id(urn), "urn_to_public_id: %s"%urn)

class Test_uriref_syntax(unittest.TestCase):
    '''URI reference syntax'''
    def test_uriref_syntax(self):
        for testuri in good_uri_references:
            self.assertEqual(1, iri.matches_uri_ref_syntax(testuri), "Good URI ref: '%s' Mistakenly tests as invalid" % repr(testuri))

        for testuri in bad_uri_references:
            self.assertEqual(0, iri.matches_uri_ref_syntax(testuri), "Bad URI ref: '%s' Mistakenly tests as valid" % repr(testuri))

class Test_absolutize(unittest.TestCase):
    '''Absolutize'''
    def test_absolutize(self):
        for uriRef, baseUri, expectedUri in absolutize_test_cases:
            res = iri.absolutize(uriRef, baseUri)
            # in a couple cases, there's more than one correct result
            if isinstance(expectedUri, tuple):
                self.assertEqual(1, res in expectedUri, 'base=%r ref=%r' % (baseUri, uriRef))
            else:
                self.assertEqual(expectedUri, res, 'base=%r ref=%r' % (baseUri, uriRef))


class Test_relativize(unittest.TestCase):
    '''Relativize'''
    def test_relativize(self):
        for targetUri, againstUri, relativeUri, subPathUri in relativize_test_cases:
            res = iri.relativize(targetUri, againstUri)
            self.assertEqual(relativeUri, res, 'target=%r against=%r (subPathOnly=False)' %
              (targetUri, againstUri))
            if res is not None:
                res = iri.absolutize(res, againstUri)
                self.assertEqual(res, targetUri, 'target=%r against=%r (subPathOnly=False, Absolutize)' %
                (targetUri, againstUri))
            res = iri.relativize(targetUri, againstUri, True)
            self.assertEqual(subPathUri, res, 'target=%r against=%r (subPathOnly=True)' %
              (targetUri, againstUri))
            if res is not None:
                res = iri.absolutize(res, againstUri)
                self.assertEqual(res, targetUri, 'target=%r against=%r (subPathOnly=True, Absolutize)' %
                (targetUri, againstUri))


class Test_base_join(unittest.TestCase):
    '''base_join'''
    def test_base_join(self):
        for base, relative, expectedUri in basejoin_test_cases:
            res = iri.basejoin(base, relative)
            self.assertEqual(expectedUri, res, 'base=%r rel=%r' % (base, relative))


class Test_uri_to_os_path(unittest.TestCase):
    '''uri_to_os_path'''
    def test_uri_to_os_path(self):
        for osname in ('posix', 'nt'):
            for subgroupname in ('absolute', 'relative'):
                for uri, nt_path, posix_path in file_uris:
                    if subgroupname == 'relative':
                        if uri[:5] == 'file:':
                            uri = uri[5:]
                        else:
                            break
                    if isinstance(uri, unicode):
                        testname = repr(uri)
                    else:
                        testname = uri
                    if osname == 'nt':
                        path = nt_path
                    elif osname == 'posix':
                        path = posix_path
                    else:
                        break
                    if path is None:
                        self.assertRaises(iri.IriError,
                                              lambda uri=uri, osname=osname: iri.uri_to_os_path(
                                                  uri, attemptAbsolute=False, osname=osname),
                                              osname+': '+subgroupname+': '+testname)
                    else:
                        self.assertEqual(path, iri.uri_to_os_path(uri, attemptAbsolute=False, osname=osname),
                                         osname+': '+subgroupname+': '+testname+': '+path)

class Test_os_path_to_uri(unittest.TestCase):
    '''os_path_to_uri'''
    def test_os_path_to_uri(self):
        for osname in ('posix', 'nt'):
            for path, nt_uri, posix_uri in file_paths:
                if isinstance(path, unicode):
                    testname = repr(path)
                else:
                    testname = path
                if osname == 'nt':
                    uri = nt_uri
                elif osname == 'posix':
                    uri = posix_uri
                else:
                    break
                if uri is None:
                    self.assertRaises(iri.IriError,
                                      lambda path=path, osname=osname: iri.os_path_to_uri(
                                          path, attemptAbsolute=False, osname=osname),
                                      osname+': '+testname)
                else:
                    self.assertEqual(uri, iri.os_path_to_uri(path, attemptAbsolute=False, osname=osname),
                                     osname+': '+testname+': '+uri)


class Test_normalize_case(unittest.TestCase):
    '''normalize_case'''
    def test_normalize_case(self):
        for uri, expected0, expected1 in case_normalization_tests:
            testname = uri
            uri = iri.split_uri_ref(uri)
            self.assertEqual(expected0, iri.unsplit_uri_ref(iri.normalize_case(uri)), testname)
            self.assertEqual(expected1, iri.unsplit_uri_ref(iri.normalize_case(uri, doHost=1)), testname + ' (host too)')


class Test_normalize_percent_encoding(unittest.TestCase):
    '''NormalizePercentEncoding'''
    def test_normalize_percent_encoding(self):
        for uri, expected in pct_enc_normalization_tests:
            testname = uri
            self.assertEqual(expected, iri.normalize_percent_encoding(uri), testname)


class Test_normalize_path_segments(unittest.TestCase):
    '''NormalizePathSegments'''
    def test_normalize_path_segments(self):
        for path, expected in path_segment_normalization_tests:
            testname = path
            self.assertEqual(expected, iri.normalize_path_segments(path), testname)


class Test_normalize_path_segments_in_uri(unittest.TestCase):
    '''NormalizePathSegmentsInUri'''
    def test_normalize_path_segments_in_uri(self):
        for path, expectedpath in path_segment_normalization_tests:
            # for non-hierarchical scheme, no change expected in every case
            uri = 'urn:bogus:%s?a=1&b=2#frag' % path
            expected = 'urn:bogus:%s?a=1&b=2#frag' % path
            testname = uri
            self.assertEqual(expected, iri.normalize_path_segments_in_uri(uri), testname)

        for path, expectedpath in path_segment_normalization_tests:
            if path[:1] == '/':
                # hierarchical scheme
                uri = 'file://root:changeme@host%s?a=1&b=2#frag' % path
                expected = 'file://root:changeme@host%s?a=1&b=2#frag' % expectedpath
                testname = uri
                self.assertEqual(expected, iri.normalize_path_segments_in_uri(uri), testname)


class Test_make_urllib_safe(unittest.TestCase):
    '''MakeUrllibSafe'''
    def test_make_urllib_safe(self):
        tests = make_urllib_safe_tests
        if os.name == 'nt':
            tests += win_make_urllib_safe_tests
        for uri, expected in make_urllib_safe_tests:
            if isinstance(uri, unicode):
                test_title = repr(uri)
            else:
                test_title = uri
            res = iri.make_urllib_safe(uri)
            self.assertEqual(expected, res, test_title)


if __name__ == '__main__':
    raise SystemExit("Use nosetests")

