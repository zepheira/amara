from amara import parse
from amara.xpath.util import abspath

import unittest

#Samuel L Bayer-inspired test for default namespace handling
#http://lists.fourthought.com/pipermail/4suite/2006-February/007757.html
XML1 = '<foo xmlns:bar="http://bar.com"><baz/><bar:baz/><baz/></foo>'
XML2 = '<foo xmlns="http://bax.com" xmlns:bar="http://bar.com"><baz/><bar:baz/><dup/><dup/></foo>'
    
def test_abspath_with_ns():
    doc = parse(XML1)
    baz2 = doc.xml_first_child.xml_first_child
    ap = abspath(baz2)
    assert ap == u'/foo/baz'
    ap = abspath(baz2.xml_following_sibling)
    assert ap == u'/foo/bar:baz'
    ap = abspath(baz2.xml_following_sibling.xml_following_sibling)
    assert ap == u'/foo/baz[2]'

def test_abspath_with_default_ns():
    doc = parse(XML2)
    baz = doc.xml_first_child.xml_first_child
    ap = abspath(baz)
    assert ap == u'/*[namespace-uri()="http://bax.com" and local-name()="foo"]/*[namespace-uri()="http://bax.com" and local-name()="baz"]'
    assert [baz] == list(doc.xml_select(ap))
    ap = abspath(baz.xml_following_sibling)
    assert ap == u'/*[namespace-uri()="http://bax.com" and local-name()="foo"]/bar:baz'
    assert [baz.xml_following_sibling] == list(doc.xml_select(ap))
    ap = abspath(baz, {u'bax': u'http://bax.com'})
    assert ap == u'/bax:foo/bax:baz'
    ap = abspath(baz.xml_following_sibling, {u'bax': u'http://bax.com'})
    assert ap == u'/bax:foo/bar:baz'
    dup1 = baz.xml_following_sibling.xml_following_sibling
    dup2 = dup1.xml_following_sibling
    ap = abspath(dup2, {u'bax': u'http://bax.com'})
    assert ap == u'/bax:foo/bax:dup[2]'

if __name__ == "__main__":
    raise SystemExit("use nosetests")
