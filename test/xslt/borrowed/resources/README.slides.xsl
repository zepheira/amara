slides.xsl is a creation of Elliotte Rusty Harold, as explained in the message
below.  

Note that one of the links in the message is wrong.

"http://metalab.unc.edu/xml/slides/xmlsig0899/xml.xll"

should read

"http://metalab.unc.edu/xml/slides/xmlsig0899/xll.xml"



===========
From: Elliotte Rusty Harold [mailto:elharo@metalab.unc.edu]
Sent: Wednesday, August 25, 1999 9:06 AM
To: xsl-list@mulberrytech.com
Subject: PowerPoint is dead. Long live XML!


Last night I gave a talk on XLinks and XPointers to the XML SIG of the
Object Developers' Group. The slides are available here:

http://metalab.unc.edu/xml/slides/xmlsig0899/

This was adapted from Chapters 16 and 17 of The XML Bible.

http://metalab.unc.edu/xml/books/bible/updates/16.html
http://metalab.unc.edu/xml/books/bible/updates/17.html

These chapters were originally written in Microsoft Word, then
saved as HTML. Some hand editing had to be done to fix Word's
exscessively presentational approach to HTML.

For this talk, I started with the HTMLized version of
those chapters as posted at the above URLs. I added various XML
markup to split them into individual slides, bullet points, and
examples while simultaneously cutting them down to a size
appropriate for a presentation. I also had to clean up the
original HTML so it would be well-formed XML. An XSL style sheet
and James Clark's XT were used to generate the actual slides in
HTML. The presentation itself was delivered from a Web browser
reading the HTML files off the local hard disk. It would have
been equally easy to do it straight from the Web.
If you're curious you can see the original XML document at
http://metalab.unc.edu/xml/slides/xmlsig0899/xml.xll and the
stylesheet I used at
http://metalab.unc.edu/xml/slides/xmlsig0899/slides.xsl
I'm not proposing this as a general tag set for presentations, though.
It's mostly just a neat hack that allowed me to prepare this one
presentation a lot more easliy than would otherwise have been
the case.

They key developments that made this possible were the HTML
output method in the latest draft of XSL (so I didn't have to
worry about whether browsers could understand constructs like
<br/> or <hr></hr>) and the xt:document extension function (so I
could put each slide element in the input document into a
separate file). This also made it very straight-forward to
generate differently styled versions of the presentation for
printing transparencies, reading directly on the Web, projecting
onto a wall, and speaker's notes. For example, the online
version simply uses the browser's default fonts. However, the
versions designed for projecting onto a wall use 16-point body
text and bold monospaced fonts so they can more easily be read
from the back of the room. The print versions don't include
navigation links. The onscreen versions do.

With some additional work I think I can probably generate both
the book chapter and the slides from one XML document. The
speaker's notes already include a lot more text than what the
audience sees. I just need to mark certain parts "book only" or
"slides only", possibly using modes. I think I'm going to do all
my presentations this way in the future. PowerPoint is dead.
Long live XML!


+-----------------------+------------------------+-------------------+
| Elliotte Rusty Harold | elharo@metalab.unc.edu | Writer/Programmer |
+-----------------------+------------------------+-------------------+
|               Java I/O (O'Reilly & Associates, 1999)               |
|            http://metalab.unc.edu/javafaq/books/javaio/            |
|   http://www.amazon.com/exec/obidos/ISBN=1565924851/cafeaulaitA/   |
+----------------------------------+---------------------------------+
|  Read Cafe au Lait for Java News:  http://metalab.unc.edu/javafaq/ |
|  Read Cafe con Leche for XML News: http://metalab.unc.edu/xml/     |
+----------------------------------+---------------------------------+



 XSL-List info and archive:  http://www.mulberrytech.com/xsl/xsl-list


 XSL-List info and archive:  http://www.mulberrytech.com/xsl/xsl-list
