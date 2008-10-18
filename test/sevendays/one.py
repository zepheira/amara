# -*- encoding: utf-8 -*-
# Testing new amara.tree API

# Testing quick reference examples

import unittest
import cStringIO
import amara
from amara.lib import testsupport
from amara import tree, xml_print
from amara import bindery

import sys, datetime
from amara.writers.struct import *
from amara.namespaces import *

class TestStructWriter(unittest.TestCase):
    def setUp(self):
        self.updated1 = datetime.datetime.now().isoformat()
        self.output = cStringIO.StringIO()
        tags = [u"xml", u"python", u"atom"]
        w = structwriter(indent=u"yes", stream=self.output)
        self.updated2 = datetime.datetime.now().isoformat()
        w.feed(
            ROOT(
                E((ATOM_NAMESPACE, u'feed'), {(XML_NAMESPACE, u'xml:lang'): u'en'},
                  E(u'id', u'urn:bogus:myfeed'),
                  E(u'title', u'MyFeed'),
                  E(u'updated', self.updated1),
                  E(u'name',
                    E(u'title', u'Uche Ogbuji'),
                    E(u'uri', u'http://uche.ogbuji.net'),
                    E(u'email', u'uche@ogbuji.net'),
                    ),
                  E(u'link', {u'href': u'/blog'}),
                  E(u'link', {u'href': u'/blog/atom1.0', u'rel': u'self'}),
                  E(u'entry',
                    E(u'id', u'urn:bogus:myfeed:entry1'),
                    E(u'title', u'Hello world'),
                    E(u'updated', self.updated2),
                    ( E(u'category', {u'term': t}) for t in tags ),
                    ),
                  E(u'content', {u'type': u'xhtml'},
                    E((XHTML_NAMESPACE, u'div'),
                      E(u'p', u'Happy to be here')
                      )
                    )
                  ))
        )
    def test_structwriter(self):
        XML_output="""\
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en">
  <id>urn:bogus:myfeed</id>
  <title>MyFeed</title>
  <updated>%s</updated>
  <name>
    <title>Uche Ogbuji</title>
    <uri>http://uche.ogbuji.net</uri>
    <email>uche@ogbuji.net</email>
  </name>
  <link href="/blog"/>
  <link rel="self" href="/blog/atom1.0"/>
  <entry>
    <id>urn:bogus:myfeed:entry1</id>
    <title>Hello world</title>
    <updated>%s</updated>
    <category term="xml"/>
    <category term="python"/>
    <category term="atom"/>
  </entry>
  <content type="xhtml">
    <div xmlns="http://www.w3.org/1999/xhtml">
      <p>Happy to be here</p>
    </div>
  </content>
</feed>\
"""
        self.assertEqual(self.output.getvalue(), XML_output % (self.updated1, self.updated2))
        
if __name__ == '__main__':
    unittest.main()
        
            
            
                
