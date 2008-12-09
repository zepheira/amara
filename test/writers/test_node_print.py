# -*- encoding: utf-8 -*-
# Testing new amara.tree API

# Testing quick reference examples

import unittest
import cStringIO
import amara
from amara.test import test_case, test_main
from amara.lib import testsupport
from amara.lib import inputsource, iri, treecompare
from amara import tree, xml_print
from amara import bindery

TNBFEED = '''<?xml version="1.0"?><feed xmlns:gr="http://www.google.com/schemas/reader/atom/" xmlns:media="http://search.yahoo.com/mrss/" xmlns="http://www.w3.org/2005/Atom"><!--
Content-type: Preventing XSRF in IE.

--><generator uri="http://www.google.com/reader">Google Reader</generator><id>tag:google.com,2005:reader/feed/http://www.thenervousbreakdown.com/uogbuji/feed/</id><title>The Nervous Breakdown » Uche Ogbuji</title><link rel="self" href="http://www.google.com/reader/atom/feed/http://www.thenervousbreakdown.com/uogbuji/feed/"/><link rel="alternate" href="http://www.thenervousbreakdown.com" type="text/html"/><updated>2008-10-31T14:47:02Z</updated><entry gr:is-read-state-locked="true" gr:crawl-timestamp-msec="1225464422407"><id gr:original-id="http://www.thenervousbreakdown.com/?p=7421">tag:google.com,2005:reader/item/5f23a25960ac5e42</id><category term="user/15841987604404046553/state/com.google/read" scheme="http://www.google.com/reader/" label="read"/><category term="Education"/><category term="Family"/><category term="Friends"/><category term="Literature"/><category term="Love"/><category term="Memory"/><category term="Moving"/><category term="Music"/><category term="Philosophy"/><category term="Poetry"/><category term="Travel"/><category term="Writing"/><category term="Antigone"/><category term="Biafra"/><category term="Boulder"/><category term="Cleveland"/><category term="Colorado"/><category term="Dallas"/><category term="Ft. Collins"/><category term="Ganiesville"/><category term="Hip-Hop"/><category term="Milwaukee"/><category term="Nigeria"/><category term="Nsukka"/><category term="Okigbo"/><category term="Peoria"/><category term="Schopenhauer"/><category term="Sophocles"/><category term="University"/><category term="UNN"/><title type="html">“BEFORE you, mother Idoto, naked I stand”</title><published>2008-10-29T04:52:58Z</published><updated>2008-10-29T04:52:58Z</updated><link rel="alternate" href="http://www.thenervousbreakdown.com/uogbuji/2008/10/before-you-mother-idoto-naked-i-stand/" type="text/html"/><summary xml:base="http://www.thenervousbreakdown.com/" type="html">BOULDER, CO-
The title is the beginning of “Heavensgate”, by Christopher Okigbo, the greatest modern Nigerian poem, and I think the greatest modern African poem.  Okigbo is my patron saint, and my personal Janus (he died in the war that gave life to me), so it’s appropriate to pour out for him before I take a [...]</summary><author><name>Uche Ogbuji</name></author><source gr:stream-id="feed/http://www.thenervousbreakdown.com/uogbuji/feed/"><id>tag:google.com,2005:reader/feed/http://www.thenervousbreakdown.com/uogbuji/feed/</id><title type="html">The Nervous Breakdown » Uche Ogbuji</title><link rel="alternate" href="http://www.thenervousbreakdown.com" type="text/html"/></source></entry></feed>
'''

ATOMENTRY1 = '<entry xmlns=\'http://www.w3.org/2005/Atom\'><id>urn:bogus:x</id><title>boo</title></entry>'

class Test_tnb_feed(test_case):
    doc = bindery.parse(TNBFEED)
    s = cStringIO.StringIO()
    xml_print(doc.feed.entry, stream=s)
    out = s.getvalue()
    doc2 = bindery.parse(out)

#python -c "import amara; doc=amara.parse('<entry xmlns=\'http://www.w3.org/2005/Atom\'><id>urn:bogus:x</id><title>boo</title></entry>'); amara.xml_print(doc)"
class Test_parse_print_roundtrips(unittest.TestSuite):
    class Test_simple_atom_entry(test_case):
        def test_simple_atom_entry(self):
            '''Basic ns fixup upon mutation'''
            doc = bindery.parse(ATOMENTRY1)
            s = cStringIO.StringIO()
            xml_print(doc, stream=s)
            out = s.getvalue()
            #self.assertEqual(out, ATOMENTRY1)
            diff = treecompare.xml_diff(out, ATOMENTRY1)
            diff = '\n'.join(diff)
            self.assertFalse(diff, msg=(None, diff))
            #Make sure we can parse the result
            doc2 = bindery.parse(out)
            return


#from Ft.Xml import EMPTY_NAMESPACE

DOCTYPE_EXPECTED_1 = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo PUBLIC "myPub" "mySys">
<foo/>"""

JABBERWOCKY = """One, two! One, two! And through and through
  The vorpal blade went snicker-snack!
He left it dead, and with its head
  He went galumphing back."""

# as XML, with Print
XHTML_EXPECTED_1 = """<?xml version="1.0" encoding="UTF-8"?>\n<html><head><title>test</title></head><body><h1>xhtml test</h1><hr noshade="noshade"/><pre>%s</pre></body></html>""" % JABBERWOCKY

# as HTML, with Print
XHTML_EXPECTED_2 = """<html><head><title>test</title></head><body><h1>xhtml test</h1><hr noshade><pre>%s</pre></body></html>""" % JABBERWOCKY

# as XML, with PrettyPrint
XHTML_EXPECTED_3 = """<?xml version="1.0" encoding="UTF-8"?>
<html>
  <head>
    <title>test</title>
  </head>
  <body>
    <h1>xhtml test</h1>
    <hr noshade="noshade"/>
    <pre>%s</pre>
  </body>
</html>
""" % JABBERWOCKY

# as HTML, with PrettyPrint
XHTML_EXPECTED_4 = """<html>
  <head>
    <title>test</title>
  </head>
  <body>
    <h1>xhtml test</h1>
    <hr noshade>
    <pre>%s</pre>
  </body>
</html>
""" % JABBERWOCKY


class Test_4suite1_tests(unittest.TestSuite):
    class Test_domlette_serialization(test_case):
        'Domlette serialization'
        def test_minimal_document(self):
            'minimal document with DOCTYPE'
            doc = amara.tree.entity()
            doc.xml_append(amara.tree.element(None, u'foo'))
            doc.publicId = u'myPub'
            doc.systemId = u'mySys'
            s = cStringIO.StringIO()
            xml_print(doc, stream=s)
            out = s.getvalue()
            #self.assertEqual(out, ATOMENTRY1)
            diff = treecompare.xml_diff(out, DOCTYPE_EXPECTED_1)
            diff = '\n'.join(diff)
            self.assertFalse(diff, msg=(None, diff))
            #Make sure we can parse the result
            doc2 = bindery.parse(out)
            return

        def _build_namespace_free_xhtml(self):
            doc = amara.tree.entity()
            html = amara.tree.element(None, u'html')
            head = amara.tree.element(None, u'head')
            title = amara.tree.element(None, u'title')
            titletext = amara.tree.text(u'test')
            body = amara.tree.element(None, u'body')
            h1 = amara.tree.element(None, u'h1')
            h1text = amara.tree.text(u'xhtml test')
            hr = amara.tree.element(None, u'hr')
            hr.xml_attributes[None, u'noshade'] = u'noshade'
            pre = amara.tree.element(None, u'pre')
            pretext = amara.tree.text(JABBERWOCKY)
            pre.xml_append(pretext)
            h1.xml_append(h1text)
            body.xml_append(h1)
            body.xml_append(hr)
            body.xml_append(pre)
            title.xml_append(titletext)
            head.xml_append(title)
            html.xml_append(head)
            html.xml_append(body)
            doc.xml_append(html)
            return doc

        def test_namespace_free_xhtml1(self):
            'namespace-free XHTML' + '...as XML with Print'
            doc = self._build_namespace_free_xhtml()
            s = cStringIO.StringIO()
            xml_print(doc, stream=s)
            out = s.getvalue()
            #self.assertEqual(out, ATOMENTRY1)
            diff = treecompare.xml_diff(out, XHTML_EXPECTED_1)
            diff = '\n'.join(diff)
            self.assertFalse(diff, msg=(None, diff))
            #Make sure we can parse the result
            doc2 = bindery.parse(out)
            return

        def test_namespace_free_xhtml2(self):
            'namespace-free XHTML' + '...as HTML with Print'
            doc = self._build_namespace_free_xhtml()
            s = cStringIO.StringIO()
            xml_print(doc, stream=s, is_html=True)
            out = s.getvalue()
            #self.assertEqual(out, ATOMENTRY1)
            diff = treecompare.xml_diff(out, XHTML_EXPECTED_2)
            diff = '\n'.join(diff)
            self.assertFalse(diff, msg=(None, diff))
            #Make sure we can parse the result
            doc2 = bindery.parse(out)
            return

        def test_namespace_free_xhtml3(self):
            'namespace-free XHTML' + '...as XML with pretty print'
            doc = self._build_namespace_free_xhtml()
            s = cStringIO.StringIO()
            xml_print(doc, stream=s, indent=True)
            out = s.getvalue()
            #self.assertEqual(out, ATOMENTRY1)
            diff = treecompare.xml_diff(out, XHTML_EXPECTED_3)
            diff = '\n'.join(diff)
            self.assertFalse(diff, msg=(None, diff))
            #Make sure we can parse the result
            doc2 = bindery.parse(out)
            return

        def test_namespace_free_xhtml4(self):
            'namespace-free XHTML' + '...as HTML with pretty print'
            doc = self._build_namespace_free_xhtml()
            s = cStringIO.StringIO()
            xml_print(doc, stream=s, is_html=True, indent=True)
            out = s.getvalue()
            #self.assertEqual(out, ATOMENTRY1)
            diff = treecompare.xml_diff(out, XHTML_EXPECTED_4)
            diff = '\n'.join(diff)
            self.assertFalse(diff, msg=(None, diff))
            #Make sure we can parse the result
            doc2 = bindery.parse(out)
            return

if __name__ == '__main__':
    test_main()

