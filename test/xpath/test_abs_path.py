from amara import parse
from amara.xpath.util import abspath

import unittest

#Samuel L Bayer-inspired test for default namespace handling
#http://lists.fourthought.com/pipermail/4suite/2006-February/007757.html
XML1 = '<foo xmlns:bar="http://bar.com"><baz/><bar:baz/></foo>'
XML2 = '<foo xmlns="http://bax.com" xmlns:bar="http://bar.com"><baz/><bar:baz/></foo>'
    
def test_abspath_with_ns():
    doc = parse(XML1)
    baz2 = doc.xml_first_child.xml_first_child
    ap = abspath(baz2)
    assert ap == u'/foo[1]/baz[1]'
    ap = abspath(baz2.xml_following_sibling)
    assert ap == u'/foo[1]/bar:baz[1]'

def test_abspath_with_default_ns():
    doc = parse(XML2)
    baz = doc.xml_first_child.xml_first_child
    ap = abspath(baz)
    assert ap == u'/*[namespace-uri()="http://bax.com" and local-name()="foo"][1]/*[namespace-uri()="http://bax.com" and local-name()="baz"][1]'
    assert [baz] == list(doc.xml_select(ap))
    ap = abspath(baz.xml_following_sibling)
    assert ap == u'/*[namespace-uri()="http://bax.com" and local-name()="foo"][1]/bar:baz[1]'
    assert [baz.xml_following_sibling] == list(doc.xml_select(ap))
    ap = abspath(baz, {u'bax': u'http://bax.com'})
    assert ap == u'/bax:foo[1]/bax:baz[1]'
    ap = abspath(baz.xml_following_sibling, {u'bax': u'http://bax.com'})
    assert ap == u'/bax:foo[1]/bar:baz[1]'

if __name__ == "__main__":
    raise SystemExit("use nosetests")
