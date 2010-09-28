import unittest
import os
import cStringIO, gc

from amara import tree, ReaderError
from amara import parse
from amara.test import file_finder
from amara.lib import treecompare

#from Ft.Lib import Uri, UriException
#from Ft.Xml import ReaderException, XIncludeException

BASE_URI = iri.os_path_to_uri(os.path.abspath(__file__), attemptAbsolute=True)

# Determine platform line seperator for textual inclusions
f = open(os.path.join(os.path.dirname(__file__), 'data.xml'), 'rb')
line = f.readline()
f.close()
if line.endswith(os.linesep):
    LINESEP = os.linesep.replace('\r', '&#13;')
else:
    # Assume UNIX line-ending
    LINESEP = '\n'
del f, line

#Technique from: http://somethingaboutorange.com/mrl/projects/nose/0.11.2/writing_tests.html#test-generators
def test_xinclude_spec_examples():
    'XInclude spec examples'
xinclude_tests = [
    (check_xinclude, 'C.1 Basic Inclusion', SPEC_SRC_1, SPEC_EXPECTED_1)
    (check_xinclude, 'Basic Inclusion Success Ignores Fallback', SPEC_SRC_1_plus_fallback, SPEC_EXPECTED_1)
    (check_xinclude, 'C.2 Textual Inclusion', SPEC_SRC_2, SPEC_EXPECTED_2)
    (check_xinclude, 'C.3 Textual Inclusion of XML', SPEC_SRC_3, SPEC_EXPECTED_3)
    (check_xinclude, 'C.6 Fallback', SPEC_SRC_6, SPEC_EXPECTED_6)
    (check_xinclude, 'C.6 Fallback erratum PEX1', SPEC_SRC_7, SPEC_EXPECTED_7)
]    
    for check, desc, source, expected in xinclude_tests:
        check.description = desc
        yield check, source, expected
    return


def check_xinclude(source, expected):
    doc = parse()
    assert n % 2 == 0 or nn % 2 == 0


def test_xinclude(tester):
    tester.startGroup("XInclude only")

    tester.startGroup()
    tester.groupDone()

    tester.startGroup('XInclude spec errata')
    doTest(tester, 'PEX1 Error in ignored fallback', PEX1_SRC, PEX1_EXPECTED)
    tester.startGroup('PEX6')
    doTest(tester, 'BOM in included UTF-8 text parsed as UTF-8',
           PEX6_SRC_1, PEX6_EXPECTED_1)
    doTest(tester, 'BOM in included UTF-8 text parsed as ISO-8859-1',
           PEX6_SRC_2, PEX6_EXPECTED_2)
    #doTest(tester, 'BOM in included UTF-16 text parsed as default',
    #       PEX6_SRC_3, PEX6_EXPECTED_3)
    #doTest(tester, 'BOM in included UTF-16 text parsed as UTF-16LE',
    #       PEX6_SRC_4, PEX6_EXPECTED_4)
    tester.groupDone()
    #PEX7 only says that the encoding attribute need not be a valid encoding name.
    #That has nothing to do with whether the given encoding is supported.
    #We don't validate that attribute's value, so there's nothing to test for PEX7;
    #we already accept any value.
    #
    #PEX10 affects the accept attribute, which we don't support (support is optional anyway)
    #
    #PEX11 is editorial.
    #
    #PEX15 only makes it no longer a fatal error for the xpointer attribute, which
    #is not a URI ref, to contain %-encoded sequences. We weren't doing %-decoding
    #on it anyway, so there's no change to test.
    #
    #PEX16 allows processors to have a user option to suppress xml:base/lang fixup.
    #
    #PEX17 is editorial.
    tester.groupDone()

    tester.startGroup('Misc tests')
    doTest(tester, 'simple XInclude', SRC_1, expected_1)
    doTest(tester, 'two-level XInclude', SRC_2, expected_2)
    doTest(tester, 'textual inclusion of XML', SRC_3, expected_3)
    doTest(tester, 'multiple XIncludes', SRC_12, expected_12)
    doTest(tester, '3.1 encoding given for included XML', SRC_15, expected_15)
    tester.groupDone()

    tester.startGroup('Misc exception tests')
    doExceptionTest(tester, 'recursive XInclude', ReaderException,
                    {'errorCode': ReaderException.RECURSIVE_PARSE_ERROR},
                    src_filename='recursive-xinclude.xml')
    doExceptionTest(tester, 'empty href', XIncludeException,
                    {'errorCode': XIncludeException.MISSING_HREF},
                    src_str=EXC_SRC_1)
    doExceptionTest(tester, 'missing href', XIncludeException,
                    {'errorCode': XIncludeException.MISSING_HREF},
                    src_str=EXC_SRC_2)
    doExceptionTest(tester, 'invalid value for parse attribute', XIncludeException,
                    {'errorCode': XIncludeException.INVALID_PARSE_ATTR},
                    src_str=EXC_SRC_3)
    doExceptionTest(tester, 'resource error', UriException,
                    {'errorCode': UriException.RESOURCE_ERROR},
                    src_str=EXC_SRC_4)
    doExceptionTest(tester, 'parser error in sub-resource', ReaderException,
                    {'errorCode': ReaderException.INCORRECT_ENCODING},
                    src_str=EXC_SRC_5)
    tester.groupDone()

    tester.groupDone()
    return


def test_xinclude_xptr(tester):
    tester.startGroup("XInclude with XPointer")

    test_lowlevel_xinclude_xptr(tester)

    tester.startGroup('XInclude spec examples')
    doTest(tester, 'C.4 Fragment Inclusion', SPEC_SRC_4, SPEC_EXPECTED_4)
    tester.startTest('C.5 Range Inclusion')
    tester.warning('Not tested; requires XPointer range support')
    tester.testDone()
    #doTest(tester, 'C.5 Range Inclusion', SPEC_SRC_5, SPEC_EXPECTED_5)
    tester.groupDone()

    tester.startGroup('Misc tests')
    doTest(tester, '/ADDRBOOK/ENTRY part 1', SRC_4, expected_4)
    doTest(tester, '/ADDRBOOK/ENTRY part 2', SRC_5, expected_5)
    doTest(tester, '/ADDRBOOK', SRC_6, expected_6)
    doTest(tester, '/ADDRBOOK/ENTRY/NAME', SRC_7, expected_7)
    doTest(tester, '/ADDRBOOK/ENTRY[2]', SRC_8, expected_8)
    doTest(tester, "/ADDRBOOK/ENTRY[@ID='en']", SRC_9, expected_9)
    doTest(tester, "/messages/msg[@xml:lang='en']", SRC_10, expected_10)
    doTest(tester, '/x:ADDRBOOK/x:ENTRY with x=http://spam.com', SRC_11, expected_11)
    doTest(tester, '/messages/*', SRC_13, expected_13)
    doTest(tester, "Cascading includes", SRC_14, expected_14)
    tester.groupDone()

    tester.groupDone()
    return


def test_lowlevel_xinclude_xptr(tester):
    tester.startGroup("Low-level XPointer")
    ELEMENT_MATCH = cDomlette.ELEMENT_MATCH
    ELEMENT_COUNT = cDomlette.ELEMENT_COUNT
    ATTRIBUTE_MATCH = cDomlette.ATTRIBUTE_MATCH

    FRAG = "xpointer(/spam)"
    EXPECTED = [[(ELEMENT_MATCH, None, u'spam')]]
    tester.startTest(FRAG)
    states = cDomlette.ProcessFragment(FRAG)
    tester.compare(EXPECTED, states)
    tester.testDone()

    FRAG = "xpointer(/spam/eggs)"
    EXPECTED = [[(ELEMENT_MATCH, None, u'spam')],
                [(ELEMENT_MATCH, None, u'eggs')],
                ]
    tester.startTest(FRAG)
    states = cDomlette.ProcessFragment(FRAG)
    tester.compare(EXPECTED, states)
    tester.testDone()

    FRAG = "xpointer(/spam/eggs/juice)"
    EXPECTED = [[(ELEMENT_MATCH, None, u'spam')],
                [(ELEMENT_MATCH, None, u'eggs')],
                [(ELEMENT_MATCH, None, u'juice')],
                ]
    tester.startTest(FRAG)
    states = cDomlette.ProcessFragment(FRAG)
    tester.compare(EXPECTED, states)
    tester.testDone()

    FRAG = "xpointer(spam)"
    EXPECTED = [[(ELEMENT_MATCH, None, u'spam')]]
    tester.startTest(FRAG)
    states = cDomlette.ProcessFragment(FRAG)
    tester.compare(EXPECTED, states)
    tester.testDone()

    FRAG = "xpointer(spam/eggs)"
    EXPECTED = [[(ELEMENT_MATCH, None, u'spam')],
                [(ELEMENT_MATCH, None, u'eggs')],
                ]
    tester.startTest(FRAG)
    states = cDomlette.ProcessFragment(FRAG)
    tester.compare(EXPECTED, states)
    tester.testDone()

    FRAG = "xpointer(spam/eggs/juice)"
    EXPECTED = [[(ELEMENT_MATCH, None, u'spam')],
                [(ELEMENT_MATCH, None, u'eggs')],
                [(ELEMENT_MATCH, None, u'juice')],
                ]
    tester.startTest(FRAG)
    states = cDomlette.ProcessFragment(FRAG)
    tester.compare(EXPECTED, states)
    tester.testDone()

    FRAG = "xpointer(/spam/eggs[1])"
    EXPECTED = [[(ELEMENT_MATCH, None, u'spam')],
                [(ELEMENT_MATCH, None, u'eggs'), (ELEMENT_COUNT, 1)],
                ]
    tester.startTest(FRAG)
    states = cDomlette.ProcessFragment(FRAG)
    tester.compare(EXPECTED, states)
    tester.testDone()

    FRAG = "xpointer(/spam[1]/eggs)"
    EXPECTED = [[(ELEMENT_MATCH, None, u'spam'), (ELEMENT_COUNT, 1)],
                [(ELEMENT_MATCH, None, u'eggs')],
                ]
    tester.startTest(FRAG)
    states = cDomlette.ProcessFragment(FRAG)
    tester.compare(EXPECTED, states)
    tester.testDone()

    FRAG = "xpointer(/spam[1]/eggs[1])"
    EXPECTED = [[(ELEMENT_MATCH, None, u'spam'), (ELEMENT_COUNT, 1)],
                [(ELEMENT_MATCH, None, u'eggs'), (ELEMENT_COUNT, 1)],
                ]
    tester.startTest(FRAG)
    states = cDomlette.ProcessFragment(FRAG)
    tester.compare(EXPECTED, states)
    tester.testDone()

    FRAG = "xpointer(/spam/eggs[@a='b'])"
    EXPECTED = [[(ELEMENT_MATCH, None, u'spam')],
                [(ELEMENT_MATCH, None, u'eggs'),
                 (ATTRIBUTE_MATCH, None, u'a', u'b')],
                ]
    tester.startTest(FRAG)
    states = cDomlette.ProcessFragment(FRAG)
    tester.compare(EXPECTED, states)
    tester.testDone()

    FRAG = "xpointer(/spam[@a='b']/eggs)"
    EXPECTED = [[(ELEMENT_MATCH, None, u'spam'),
                 (ATTRIBUTE_MATCH, None, u'a', u'b')],
                [(ELEMENT_MATCH, None, u'eggs')],
                ]
    tester.startTest(FRAG)
    states = cDomlette.ProcessFragment(FRAG)
    tester.compare(EXPECTED, states)
    tester.testDone()

    FRAG = "xpointer(/spam[@a='b']/eggs[@a='b'])"
    EXPECTED = [[(ELEMENT_MATCH, None, u'spam'),
                 (ATTRIBUTE_MATCH, None, u'a', u'b')],
                [(ELEMENT_MATCH, None, u'eggs'),
                  (ATTRIBUTE_MATCH, None, u'a', u'b')],
                ]
    tester.startTest(FRAG)
    states = cDomlette.ProcessFragment(FRAG)
    tester.compare(EXPECTED, states)
    tester.testDone()

    FRAG = "xmlns(ns=http://spam.com) xpointer(/spam/eggs[@ns:a='b'])"
    EXPECTED = [[(ELEMENT_MATCH, None, u'spam')],
                [(ELEMENT_MATCH, None, u'eggs'),
                 (ATTRIBUTE_MATCH, u'http://spam.com', u'a', u'b')],
                ]
    tester.startTest(FRAG)
    states = cDomlette.ProcessFragment(FRAG)
    tester.compare(EXPECTED, states)
    tester.testDone()

    tester.groupDone()
    return

SPEC_SRC_1 = """<?xml version='1.0'?>
<document xmlns:xi="http://www.w3.org/2001/XInclude">
  <p>120 Mz is adequate for an average home user.</p>
  <xi:include href="disclaimer.xml"/>
</document>"""

SPEC_SRC_1_plus_fallback = """<?xml version='1.0'?>
<document xmlns:xi="http://www.w3.org/2001/XInclude">
  <p>120 Mz is adequate for an average home user.</p>
  <xi:include href="disclaimer.xml">
    <xi:fallback><foo/></xi:fallback>
  </xi:include>
</document>"""

SPEC_EXPECTED_1 = """<?xml version="1.0" encoding="UTF-8"?>
<document xmlns:xi="http://www.w3.org/2001/XInclude">
  <p>120 Mz is adequate for an average home user.</p>
  <disclaimer xml:base="%s">
  <p>The opinions represented herein represent those of the individual
  and should not be interpreted as official policy endorsed by this
  organization.</p>
</disclaimer>
</document>""" % Uri.Absolutize("disclaimer.xml", BASE_URI)

SPEC_SRC_2 = """<?xml version='1.0'?>
<document xmlns:xi="http://www.w3.org/2001/XInclude">
  <p>This document has been accessed
  <xi:include href="count.txt" parse="text"/> times.</p>
</document>"""

SPEC_EXPECTED_2 = """<?xml version="1.0" encoding="UTF-8"?>
<document xmlns:xi="http://www.w3.org/2001/XInclude">
  <p>This document has been accessed
  324387 times.</p>
</document>"""

SPEC_SRC_3 = """<?xml version='1.0'?>
<document xmlns:xi="http://www.w3.org/2001/XInclude">
  <p>The following is the source of the "data.xml" resource:</p>
  <example><xi:include href="data.xml" parse="text"/></example>
</document>"""

SPEC_EXPECTED_3 = """<?xml version="1.0" encoding="UTF-8"?>
<document xmlns:xi="http://www.w3.org/2001/XInclude">
  <p>The following is the source of the "data.xml" resource:</p>
  <example>&lt;?xml version='1.0'?&gt;%(linesep)s&lt;data&gt;%(linesep)s  &lt;item&gt;&lt;![CDATA[Brooks &amp; Shields]]&gt;&lt;/item&gt;%(linesep)s&lt;/data&gt;</example>
</document>""" % {'linesep' : LINESEP}

SPEC_SRC_4 = """<?xml version='1.0'?>
<price-quote xmlns:xi="http://www.w3.org/2001/XInclude">
  <prepared-for>Joe Smith</prepared-for>
  <good-through>20040930</good-through>
  <xi:include href="price-list.xml" xpointer="w002-description"/>
  <volume>40</volume>
  <xi:include href="price-list.xml" xpointer="element(w002-prices/2)"/>
</price-quote>"""

SPEC_EXPECTED_4 = """<?xml version="1.0" encoding="UTF-8"?>
<price-quote xmlns:xi="http://www.w3.org/2001/XInclude">
  <prepared-for>Joe Smith</prepared-for>
  <good-through>20040930</good-through>
  <description id="w002-description" xml:lang="en-us" xml:base="%(base)s">
      <p>Super-sized widget with bells <i>and</i> whistles.</p>
    </description>
  <volume>40</volume>
  <price currency="USD" volume="10+" xml:lang="en-us"
         xml:base="%(base)s">54.95</price>
</price-quote>""" % {'base': Uri.Absolutize("price-list.xml", BASE_URI)}

SPEC_SRC_5 = """<?xml version='1.0'?>
<document>
  <p>The relevant excerpt is:</p>
  <quotation>
    <include xmlns="http://www.w3.org/2001/XInclude"
       href="source.xml" xpointer="xpointer(string-range(chapter/p[1],'Sentence 2')/
             range-to(string-range(/chapter/p[2]/i,'3.',1,2)))"/>
  </quotation>
</document>"""

SPEC_EXPECTED_5 = """<?xml version="1.0" encoding="UTF-8"?>
<?xml version='1.0'?>
<document>
  <p>The relevant excerpt is:</p>
  <quotation>
    <p xml:base="http://www.example.com/source.xml">Sentence 2.</p>
  <p xml:base="http://www.example.com/source.xml"><i>Sentence 3.</i></p>
  </quotation>
</document>"""

SPEC_SRC_6 = """<?xml version='1.0'?>
<div>
  <xi:include href="example.txt" parse="text" xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:fallback><xi:include href="fallback-example.txt" parse="text">
        <xi:fallback><a href="mailto:bob@example.org">Report error</a></xi:fallback>
      </xi:include></xi:fallback>
  </xi:include>
</div>"""

SPEC_EXPECTED_6 = """<?xml version="1.0" encoding="UTF-8"?>
<div xmlns:xi="http://www.w3.org/2001/XInclude">
  <a href="mailto:bob@example.org">Report error</a>
</div>"""

# erratum PEX1: errors in fallback should be ignored if fallback isn't performed.
# This test assumes include1.xml will be successfully included.
SPEC_SRC_7="""<?xml version='1.0'?><x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="include1.xml"><xi:fallback><xi:include href="include2.xml" parse="bogus"/></xi:fallback></xi:include>
</x>"""

SPEC_EXPECTED_7 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<foo xml:base="%s"/>
</x>""" % Uri.Absolutize("include1.xml", BASE_URI)

SRC_1="""<?xml version='1.0'?><x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="include1.xml"/>
</x>"""

expected_1 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<foo xml:base="%s"/>
</x>""" % Uri.Absolutize("include1.xml", BASE_URI)

SRC_2="""<?xml version='1.0'?><x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="include2.xml"/>
</x>"""

expected_2="""<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<foo xml:base="%s">
  <foo xml:base="%s"/>
</foo>
</x>""" % (Uri.Absolutize("include2.xml", BASE_URI),
           Uri.Absolutize("include1.xml", BASE_URI))

SRC_3="""<?xml version='1.0'?><x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="include2.xml" parse='text'/>
</x>"""

expected_3="""<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
&lt;?xml version='1.0' encoding='utf-8'?&gt;%(linesep)s&lt;foo xmlns:xi="http://www.w3.org/2001/XInclude"&gt;%(linesep)s  &lt;xi:include href="include1.xml"/&gt;%(linesep)s&lt;/foo&gt;
</x>""" % {'linesep' : LINESEP}

SRC_4="""<?xml version='1.0'?><x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="include3.xml" xpointer="xpointer(/ADDRBOOK/ENTRY)"/>
</x>"""

expected_4 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<ENTRY ID="pa" xml:base="%(base)s">
    <NAME>Pieter Aaron</NAME>
    <EMAIL>pieter.aaron@inter.net</EMAIL>
  </ENTRY>
</x>""" % {"base" : Uri.Absolutize("include3.xml", BASE_URI)}

SRC_5="""<?xml version='1.0'?><x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="include4.xml" xpointer="xpointer(/ADDRBOOK/ENTRY)"/>
</x>"""

expected_5 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<ENTRY xml:base="%(base)s" ID="pa">
    <NAME>Pieter Aaron</NAME>
    <EMAIL>pieter.aaron@inter.net</EMAIL>
  </ENTRY><ENTRY xml:base="%(base)s" ID="en">
    <NAME>Emeka Ndubuisi</NAME>
    <EMAIL>endubuisi@spamtron.com</EMAIL>
  </ENTRY><ENTRY xml:base="%(base)s" ID="vz">
    <NAME>Vasia Zhugenev</NAME>
    <EMAIL>vxz@gog.ru</EMAIL>
  </ENTRY>
</x>""" % {"base" : Uri.Absolutize("include4.xml", BASE_URI)}

SRC_6="""<?xml version='1.0'?><x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="include3.xml" xpointer="xpointer(/ADDRBOOK)"/>
</x>"""

expected_6 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<ADDRBOOK xml:base="%(base)s">
  <ENTRY ID="pa">
    <NAME>Pieter Aaron</NAME>
    <EMAIL>pieter.aaron@inter.net</EMAIL>
  </ENTRY>
</ADDRBOOK>
</x>""" % {"base" : Uri.Absolutize("include3.xml", BASE_URI)}

SRC_7="""<?xml version='1.0'?><x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="include3.xml" xpointer="xpointer(/ADDRBOOK/ENTRY/NAME)"/>
</x>"""

expected_7 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<NAME xml:base="%(base)s">Pieter Aaron</NAME>
</x>""" % {"base" : Uri.Absolutize("include3.xml", BASE_URI)}

SRC_8="""<?xml version='1.0'?><x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="include4.xml" xpointer="xpointer(/ADDRBOOK/ENTRY[2])"/>
</x>"""

expected_8 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<ENTRY xml:base="%(base)s" ID="en">
    <NAME>Emeka Ndubuisi</NAME>
    <EMAIL>endubuisi@spamtron.com</EMAIL>
  </ENTRY>
</x>""" % {"base" : Uri.Absolutize("include4.xml", BASE_URI)}

SRC_9="""<?xml version='1.0'?><x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="include4.xml" xpointer="xpointer(/ADDRBOOK/ENTRY[@ID='en'])"/>
</x>"""

expected_9 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<ENTRY xml:base="%(base)s" ID="en">
    <NAME>Emeka Ndubuisi</NAME>
    <EMAIL>endubuisi@spamtron.com</EMAIL>
  </ENTRY>
</x>""" % {"base" : Uri.Absolutize("include4.xml", BASE_URI)}

SRC_10="""<?xml version='1.0'?><x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="include6.xml" xpointer="xpointer(/messages/msg[@xml:lang='en'])"/>
</x>"""

expected_10 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<msg xml:lang="en" xml:base="%(base)s">Hello</msg>
</x>""" % {"base" : Uri.Absolutize("include6.xml", BASE_URI)}

SRC_11="""<?xml version='1.0'?><x xmlns:xi="http://www.w3.org/2001/XInclude">
  <xi:include href="include7.xml" xpointer="xmlns(x=http://spam.com) xpointer(/x:ADDRBOOK/x:ENTRY)"/>
</x>"""

expected_11 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
  <ENTRY xmlns="http://spam.com" xml:base="%(base)s" ID="pa">
    <NAME>Pieter Aaron</NAME>
    <EMAIL>pieter.aaron@inter.net</EMAIL>
  </ENTRY>
</x>""" % {"base" : Uri.Absolutize("include7.xml", BASE_URI)}

SRC_12="""<?xml version='1.0'?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
  <xi:include href="include1.xml"/>
  <xi:include href="include1.xml"/>
</x>"""

expected_12 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
  <foo xml:base="%(base)s"/>
  <foo xml:base="%(base)s"/>
</x>""" % {"base" : Uri.Absolutize("include1.xml", BASE_URI)}

SRC_13 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
  <xi:include href="include6.xml" xpointer="xpointer(messages/*)"/>
  <para/>
  <para>Another paragraph</para>
</x>"""

expected_13 = """<?xml version="1.0" encoding="utf-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
  <msg xml:base="%(base)s" xml:lang="en">Hello</msg><msg xml:base="%(base)s" xml:lang="fr">Bonjour</msg><msg xml:base="%(base)s" xml:lang="ib">Nde ewo</msg>
  <para/>
  <para>Another paragraph</para>
</x>""" % {'base': Uri.Absolutize('include6.xml', BASE_URI)}

SRC_14 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
  <xi:include href="include2.xml" xpointer="xpointer(foo/*)"/>
</x>"""

expected_14 = """<?xml version="1.0" encoding="utf-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
  <foo xml:base="%(base)s"/>
</x>""" % {'base': Uri.Absolutize('include1.xml', BASE_URI)}

# 3.1 encoding declaration ignored when parse="xml"
SRC_15 = """<?xml version='1.0'?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="include1.xml" parse="xml" encoding="UTF-16LE"/>
</x>"""

expected_15 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<foo xml:base="%s"/>
</x>""" % Uri.Absolutize("include1.xml", BASE_URI)


# erratum PEX1: errors in fallback should be ignored if fallback isn't performed.
# This test assumes include1.xml will be successfully included.
PEX1_SRC = """<?xml version='1.0'?><x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="include1.xml"><xi:fallback><xi:include href="include2.xml" parse="bogus"/></xi:fallback></xi:include>
</x>"""

PEX1_EXPECTED = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<foo xml:base="%s"/>
</x>""" % Uri.Absolutize("include1.xml", BASE_URI)

# erratum PEX6: when parse="text", a BOM at the start of included text is discarded if that text is being read as UTF-8/16/32
PEX6_SRC_1 = """<?xml version='1.0'?><x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="utf8bom.txt" parse="text" encoding="utf-8"/></x>"""

PEX6_EXPECTED_1 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
This file has a UTF-8 BOM.
</x>"""

# erratum PEX6 continued
PEX6_SRC_2 = """<?xml version='1.0'?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="utf8bom.txt" parse="text" encoding="iso-8859-1"/></x>"""

# Since the included doc is to be read as iso-8859-1, the UTF-8 BOM
# should be interpreted as U+00EF U+00BB U+00BF.
# When serialized as UTF-8, we expect those to turn into C3 AF C2 BB C2 BF.
PEX6_EXPECTED_2 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
\xc3\xaf\xc2\xbb\xc2\xbfThis file has a UTF-8 BOM.
</x>"""

# erratum PEX6 continued
PEX6_SRC_3 = """<?xml version='1.0'?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="utf16bom.txt" parse="text"/></x>"""

PEX6_EXPECTED_3 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
This file has a UTF-16 little-endian BOM.
</x>"""

# erratum PEX6 continued
PEX6_SRC_4 = """<?xml version='1.0'?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="utf16bom.txt" parse="text" encoding="utf-16LE"/></x>"""

# The BOM in the included file will be FF FE.
# When read as UTF-16LE, it will be interpreted as U+FEFF.
# When U+FEFF is serialized as UTF-8, it is EF BB BF (the UTF-8 BOM!)
PEX6_EXPECTED_4 = """<?xml version="1.0" encoding="UTF-8"?>
<x xmlns:xi="http://www.w3.org/2001/XInclude">
\xef\xbb\xbfThis file has a UTF-16 little-endian BOM.
</x>"""

# NOTE: technically, this does not have to be an error;
# it is up to the processor whether it handles it or not
EXC_SRC_1 = """<?xml version="1.0" encoding="utf-8"?>
<wrapper>
<xi:include xmlns:xi="http://www.w3.org/2001/XInclude" href="" parse="xml"/>
</wrapper>"""

# NOTE: technically, this does not have to be an error;
# it is up to the processor whether it handles it or not
EXC_SRC_2 = """<?xml version="1.0" encoding="utf-8"?>
<wrapper>
<xi:include xmlns:xi="http://www.w3.org/2001/XInclude" parse="xml"/>
</wrapper>"""

# Fatal error according to the spec
EXC_SRC_3 = """<?xml version="1.0" encoding="utf-8"?>
<wrapper>
<xi:include xmlns:xi="http://www.w3.org/2001/XInclude" href="include1.xml" parse="bogus"/>
</wrapper>"""

# Resource error
EXC_SRC_4 = """<?xml version="1.0" encoding="utf-8"?>
<wrapper>
<xi:include xmlns:xi="http://www.w3.org/2001/XInclude" href="bogus.xml"/>
</wrapper>"""

# Parse error in sub-resource
EXC_SRC_5 = """<?xml version="1.0" encoding="utf-8"?>
<wrapper>
<xi:include xmlns:xi="http://www.w3.org/2001/XInclude"
                href="badXml_utf8_noBOM_16Decl.xml"/>
</wrapper>"""


if __name__ == '__main__':
    from Ft.Lib.TestSuite import Tester
    tester = Tester.Tester()
    Test(tester)

