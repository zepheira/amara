import unittest
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
        self.assertEquals(len(self.results),2)
        expected_names = [
            (u'http://spam.com/',u'a'),
            (None, u'a')
        ]
        for node,ename in zip(self.results,expected_names):
            self.assertEquals(node.xml_name,ename)

    def testnestedelement(self):
        pushtree(self.infile,"a/c",self.callback)
        self.assertEquals(len(self.results),1)
        self.assertEquals(self.results[0].xml_name,(None,u'c'))

    def testattribute(self):
        pushtree(self.infile,"a/@b",self.callback)
        self.assertEquals(len(self.results),1)
        self.assertEquals(self.results[0].xml_name,(u'http://spam.com/',u'a'))

    def testnamespaces(self):
        # This is currently broken.  Possible bug in matching code
        pushtree(self.infile,"/a//q:a",self.callback,
                 namespaces = {"q":"http://spam.com/"})
        self.assertEquals(len(self.results),1)
        self.assertEquals(self.results[0].xml_name,(u'http://spam.com/',u'a'))

    def testprocessing(self):
        # Currently broken.  Possible bug in matching code
        pushtree(self.infile,"processing-instruction('xml-stylesheet')",
                 self.callback)


if __name__ == '__main__':
    unittest.main()

    

