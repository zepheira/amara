from cStringIO import StringIO

import amara
from amara.pushtree import pushtree
from amara.lib import treecompare
from amara.test import KnownFailure

XMLDECL = '<?xml version="1.0" encoding="UTF-8"?>\n'

XML1 = '''<doc>
  <one><a>0</a><a>1</a></one>
  <two><a>10</a><a>11</a></two>
</doc>'''

XML2 = '''<doc xmlns="urn:bogus:x">
  <one><a>0</a><a>1</a></one>
  <two><a>10</a><a>11</a></two>
</doc>'''

XML3 = '''<x:doc xmlns:x="urn:bogus:x">
  <x:one><x:a>0</x:a><x:a>1</x:a></x:one>
  <x:two><x:a>10</x:a><x:a>11</x:a></x:two>
</x:doc>'''

XML4 = '''<doc xmlns:x="urn:bogus:x">
  <one><x:a>0</x:a><x:a>1</x:a></one>
  <two><a>10</a><a>11</a></two>
</doc>'''

def test_1():
    EXPECTED = ['<a>0</a>', '<a>1</a>', '<a>10</a>', '<a>11</a>']
    results = []

    def callback(node):
        results.append(node)

    pushtree(XML1, u"a", callback)

    for result, expected in zip(results, EXPECTED):
        treecompare.check_xml(result.xml_encode(), XMLDECL+expected)
    return

#
def test_2():
    EXPECTED = ['<a xmlns="urn:bogus:x">0</a>', '<a xmlns="urn:bogus:x">1</a>', '<a xmlns="urn:bogus:x">10</a>', '<a xmlns="urn:bogus:x">11</a>']
    results = []

    def callback(node):
        results.append(node)

    pushtree(XML2, u"a", callback, namespaces = {None: "urn:bogus:x"})

    for result, expected in zip(results, EXPECTED):
        treecompare.check_xml(result.xml_encode(), XMLDECL+expected)

    return

#
def test_3():
    EXPECTED = ['<x:a xmlns:x="urn:bogus:x">0</x:a>', '<x:a xmlns:x="urn:bogus:x">1</x:a>', '<x:a xmlns:x="urn:bogus:x">10</x:a>', '<x:a xmlns:x="urn:bogus:x">11</x:a>']
    results = []

    def callback(node):
        results.append(node)

    pushtree(XML3, u"x:a", callback, namespaces = {"x": "urn:bogus:x"})

    for result, expected in zip(results, EXPECTED):
        treecompare.check_xml(result.xml_encode(), XMLDECL+expected)

    return

#
def test_4():
    EXPECTED = ['<x:a xmlns:x="urn:bogus:x">0</x:a>', '<x:a xmlns:x="urn:bogus:x">1</x:a>']
    results = []

    def callback(node):
        results.append(node)

    pushtree(XML4, u"x:a", callback, namespaces = {"x": "urn:bogus:x"})

    for result, expected in zip(results, EXPECTED):
        treecompare.check_xml(result.xml_encode(), XMLDECL+expected)

    return

testdoc = """\
    <a xmlns:x='http://spam.com/'>
    <?xml-stylesheet href='mystyle.css' type='text/css'?>
    <blah>
    <x:a b='2'></x:a>
    </blah>
    <c d='3'/>
    </a>
    """

import unittest

class TestPushTree(unittest.TestCase):
    def setUp(self):
        self.results = []
        self.infile = StringIO(testdoc)
    def tearDown(self):
        del self.results[:]
    # Callback function trigged on pattern match
    def callback(self,node):
        self.results.append(node)
        #print node

    def testsimpleelement(self):
        pushtree(self.infile,"a",self.callback)
        self.assertEquals(len(self.results), 2)
        expected_names = [
            (u'http://spam.com/', u'a'), # XXX this should not be expected?
            (None, u'a')
        ]
        for node,ename in zip(self.results,expected_names):
            self.assertEquals(node.xml_name,ename)

    def testnestedelement(self):
        pushtree(self.infile,"a/c",self.callback)
        self.assertEquals(len(self.results),1)
        self.assertEquals(self.results[0].xml_name,(None,u'c'))

    def testattribute(self):
        pushtree(self.infile,"a/*/*/@b",self.callback)
        self.assertEquals(len(self.results),1)
        self.assertEquals(self.results[0].xml_name,(u'http://spam.com/',u'a'))

    def testnamespaces(self):
        # This is currently broken.  Possible bug in matching code
        pushtree(self.infile,"/a//q:a",self.callback,
                 namespaces = {"q":"http://spam.com/"})
        self.assertEquals(len(self.results),1)
        self.assertEquals(self.results[0].xml_name,(u'http://spam.com/',u'a'))

##     def testprocessing(self):
##         # Currently broken.  Possible bug in matching code
##         pushtree(self.infile,"processing-instruction('xml-stylesheet')",
##                  self.callback)

### This tests more of the nitty-gritty

TREE1 = """
<a x='1'>
  <b x='2'>
    <c x='3'>
      <b x='4'>
        <d x='5' />
        <e x='6' />
        <d x='7' />
        <b x='8' />
        <c x='9' />
      </b>
      <c x='10'><c x='11' /></c>
    </c>
  </b>
</a>
"""
TREEDOC = amara.parse(TREE1)

class TestXPathMatcher(unittest.TestCase):
    def setUp(self):
        self.results = []
        self.infile = StringIO(testdoc)
    def tearDown(self):
        del self.results[:]
    # Callback function trigged on pattern match
    def callback(self,node):
        self.results.append(node.xml_attributes["x"])


    def compare_matches(self, xpath):
        del self.results[:]
        select_ids = set(node.xml_attributes["x"]
                                for node in TREEDOC.xml_select("//"+xpath))
        pushtree(TREE1, xpath, self.callback)
        push_ids = set(self.results)
        self.assertEquals(select_ids, push_ids)
        
    def test_relative_single(self):
        self.compare_matches("a")
        self.compare_matches("b")
        self.compare_matches("c")


def test_predicate1():
    EXPECTED = ['''<b x='4'>
        <d x='5' />
        <e x='6' />
        <d x='7' />
        <b x='8' />
        <c x='9' />
      </b>''']
    results = []
    raise KnownFailure("No predicates support.  See: http://trac.xml3k.org/ticket/23")


    def callback(node):
        results.append(node)

    pushtree(TREE1, u"b[x='4']", callback)

    for result, expected in zip(results, EXPECTED):
        treecompare.check_xml(result.xml_encode(), XMLDECL+expected)
    return


XML5 = '''<doc>
  <one><a>0</a><a>1</a></one>
  <two><a>10</a><a>11</a></two>
  <one>repeat</one>
</doc>'''

def test_predicate2():
    EXPECTED = ['<one>repeat</one>']
    results = []

    def callback(node):
        results.append(node)

    pushtree(XML5, u"doc/one[2]", callback)

    for result, expected in zip(results, EXPECTED):
        treecompare.check_xml(result.xml_encode(), XMLDECL+expected)
    return


if __name__ == '__main__':
    unittest.main()
