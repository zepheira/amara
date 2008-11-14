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

if __name__ == '__main__':
    test_main()

