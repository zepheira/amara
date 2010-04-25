import unittest
import amara
from amara.pushtree import pushtree
from cStringIO import StringIO

testdoc = """\
    <a xmlns:x='http://spam.com/'>
    <?xml-stylesheet href='mystyle.css' type='text/css'?>
    <blah>
    <x:a b='2'></x:a>
    </blah>
    <c d='3'/>
    </a>
    """

class TestPushTree(unittest.TestCase):
    def __init__(self):
        pass
    def setUp(self):
        self.results = []
        self.infile = StringIO(testdoc)
    def tearDown(self):
        del self.results[:]
    # Callback function trigged on pattern match
    def callback(self,node):
        self.results.append(node)
#        print node

    def testsimpleelement(self):
        pushtree(self.infile,"a",self.callback)
        self.assertEquals(len(self.results),1)
        expected_names = [
            #(u'http://spam.com/',u'a'), # XXX this should not be expected?
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
        select_ids = [node.xml_attributes["x"] for node in TREEDOC.xml_select(xpath)]
        pushtree(TREE1, xpath, self.callback)
        push_ids = self.results
        self.assertEquals(select_ids, push_ids)

    def test_relative_single(self):
        self.compare_matches("a")
        self.compare_matches("b")
        self.compare_matches("c")
        
if __name__ == '__main__':
    x = TestPushTree()
    x.setUp()
    x.testattribute()
    x.tearDown()
    del x
    #unittest.main()
