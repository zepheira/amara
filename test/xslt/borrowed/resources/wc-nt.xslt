<!--
Date: Thu, 10 Feb 2000 09:31:44 -0500 (07:31 MST)
From: Steve Tinney <stinney@sas.upenn.edu>
To: "xsl-list@mulberrytech.com" <xsl-list@mulberrytech.com>
Subject: XSL Word-counter

By popular request...

This script probably counts the number of words in the node-set you pass
to the word-count template in the parameter 'in'.

Caveats: I wrote it a few months ago, and haven't used it much.  It uses
a pretty unsophisticated definition of 'word'.  I doubt it's even close
to perfect.  There is only an XT version just now.  I would not declare
myself 100% happy with it.

Still, it illustrates how to do some counting-type things in XSL.  I
allowed myself to use node-set in implementing it, but I daresay it
could be done without even in a single script.

To run the test 'suite' just use wctest.xsl for both xml and xsl
argument.

[...]
-->

<!--
Uche's Notes:

This is ported to 4XSLT.  Also see wc.xslt which does not
use proprietary extensions, again courtesy Steve Tinney.
-->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exsl="http://exslt.org/common"
  exclude-result-prefixes="exsl"
>

<xsl:template name="word-count">
  <xsl:param name="in" select="."/>
  <xsl:call-template name="words-in-text-list">
    <xsl:with-param name="text-nodes" select="$in//text()"/>
  </xsl:call-template>
</xsl:template>

<xsl:template name="words-in-text-list">
  <xsl:param name="text-nodes"/>
  <xsl:variable name="total-rtf">
    <xsl:for-each select="$text-nodes">
      <n>
        <xsl:call-template name="words-in-text">
          <xsl:with-param name="text" select="normalize-space(.)"/>
        </xsl:call-template>
      </n>
    </xsl:for-each>
  </xsl:variable>
  <xsl:value-of select="sum(exsl:node-set($total-rtf)/*)"/>
</xsl:template>

<xsl:template name="words-in-text">
  <xsl:param name="text" select="''"/>
  <xsl:param name="total" select="0"/>
  <xsl:choose>
    <xsl:when test="string-length($text) = 0">
      <xsl:value-of select="$total"/>
    </xsl:when>
    <xsl:when test="not(contains($text,' '))">
      <xsl:value-of select="$total+1"/>
    </xsl:when>
    <xsl:otherwise>
      <xsl:call-template name="words-in-text">
        <xsl:with-param name="total" select="$total+1"/>
        <xsl:with-param name="text" select="substring-after($text,' ')"/>
      </xsl:call-template>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

</xsl:stylesheet>
