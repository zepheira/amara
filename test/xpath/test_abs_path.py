from amara import parse
from amara.xpath.util import abspath

import unittest

class test_sb060223(unittest.TestCase):
    #Samuel L Bayer-inspired test for default namespace handling
    #http://lists.fourthought.com/pipermail/4suite/2006-February/007757.html
    XML1 = '<foo xmlns:bar="http://bar.com"><baz/><bar:baz/></foo>'
    XML2 = '<foo xmlns="http://bax.com" xmlns:bar="http://bar.com"><baz/><bar:baz/></foo>'
    
    def test_abspath_with_ns(self):
        doc = parse(self.XML1)
        baz2 = doc.xml_first_child.xml_first_child
        ap = abspath(baz2)
        self.assertEqual(ap, u'/foo[1]/baz[1]')
        ap = abspath(baz2.xml_following_sibling)
        self.assertEqual(ap, u'/foo[1]/bar:baz[1]')

    def test_abspath_with_default_ns(self):
        doc = parse(self.XML2)
        baz = doc.xml_first_child.xml_first_child
        ap = abspath(baz)
        self.assertEqual(ap, u'/*[namespace-uri()="http://bax.com" and local-name()="foo"][1]/*[namespace-uri()="http://bax.com" and local-name()="baz"][1]')
        self.assertEqual([baz], list(doc.xml_select(ap)))
        ap = abspath(baz.xml_following_sibling)
        self.assertEqual(ap, u'/*[namespace-uri()="http://bax.com" and local-name()="foo"][1]/bar:baz[1]')
        self.assertEqual([baz.xml_following_sibling], list(doc.xml_select(ap)))
        ap = abspath(baz, {u'bax': u'http://bax.com'})
        self.assertEqual(ap, u'/bax:foo[1]/bax:baz[1]')
        ap = abspath(baz.xml_following_sibling, {u'bax': u'http://bax.com'})
        self.assertEqual(ap, u'/bax:foo[1]/bar:baz[1]')

if __name__ == "__main__":
    unittest.main()
