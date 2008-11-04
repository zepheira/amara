# -*- encoding: utf-8 -*-
# Testing new amara.tree API

# Testing quick reference examples

import unittest
import cStringIO
import amara
from amara.lib import testsupport
from amara import tree, xml_print
from amara import bindery

TNBFEED = '''<?xml version="1.0"?><feed xmlns:gr="http://www.google.com/schemas/reader/atom/" xmlns:media="http://search.yahoo.com/mrss/" xmlns="http://www.w3.org/2005/Atom"><!--
Content-type: Preventing XSRF in IE.

--><generator uri="http://www.google.com/reader">Google Reader</generator><id>tag:google.com,2005:reader/feed/http://www.thenervousbreakdown.com/uogbuji/feed/</id><title>The Nervous Breakdown » Uche Ogbuji</title><link rel="self" href="http://www.google.com/reader/atom/feed/http://www.thenervousbreakdown.com/uogbuji/feed/"/><link rel="alternate" href="http://www.thenervousbreakdown.com" type="text/html"/><updated>2008-10-31T14:47:02Z</updated><entry gr:is-read-state-locked="true" gr:crawl-timestamp-msec="1225464422407"><id gr:original-id="http://www.thenervousbreakdown.com/?p=7421">tag:google.com,2005:reader/item/5f23a25960ac5e42</id><category term="user/15841987604404046553/state/com.google/read" scheme="http://www.google.com/reader/" label="read"/><category term="Education"/><category term="Family"/><category term="Friends"/><category term="Literature"/><category term="Love"/><category term="Memory"/><category term="Moving"/><category term="Music"/><category term="Philosophy"/><category term="Poetry"/><category term="Travel"/><category term="Writing"/><category term="Antigone"/><category term="Biafra"/><category term="Boulder"/><category term="Cleveland"/><category term="Colorado"/><category term="Dallas"/><category term="Ft. Collins"/><category term="Ganiesville"/><category term="Hip-Hop"/><category term="Milwaukee"/><category term="Nigeria"/><category term="Nsukka"/><category term="Okigbo"/><category term="Peoria"/><category term="Schopenhauer"/><category term="Sophocles"/><category term="University"/><category term="UNN"/><title type="html">“BEFORE you, mother Idoto, naked I stand”</title><published>2008-10-29T04:52:58Z</published><updated>2008-10-29T04:52:58Z</updated><link rel="alternate" href="http://www.thenervousbreakdown.com/uogbuji/2008/10/before-you-mother-idoto-naked-i-stand/" type="text/html"/><summary xml:base="http://www.thenervousbreakdown.com/" type="html">BOULDER, CO-
The title is the beginning of “Heavensgate”, by Christopher Okigbo, the greatest modern Nigerian poem, and I think the greatest modern African poem.  Okigbo is my patron saint, and my personal Janus (he died in the war that gave life to me), so it’s appropriate to pour out for him before I take a [...]</summary><author><name>Uche Ogbuji</name></author><source gr:stream-id="feed/http://www.thenervousbreakdown.com/uogbuji/feed/"><id>tag:google.com,2005:reader/feed/http://www.thenervousbreakdown.com/uogbuji/feed/</id><title type="html">The Nervous Breakdown » Uche Ogbuji</title><link rel="alternate" href="http://www.thenervousbreakdown.com" type="text/html"/></source></entry></feed>
'''

class Test_tnb_feed(unittest.TestSuite):
    doc = bindery.parse(TNBFEED)
    s = cStringIO.StringIO()
    xml_print(doc.feed.entry, stream=s)
    out = s.getvalue()
    doc2 = bindery.parse(out)

    
if __name__ == '__main__':
    testsupport.test_main()
