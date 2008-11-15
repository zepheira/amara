<!--
Date: Thu, 10 Feb 2000 10:56:22 -0500 (08:56 MST)
From: Steve Tinney <stinney@sas.upenn.edu>
To: xsl-list@mulberrytech.com
Subject: Re: XSL Word-counter

Steve Tinney wrote:
> allowed myself to use node-set in implementing it, but I daresay it
> could be done without even in a single script.

I shouldn't have started myself off.   Here's another version which is
leaner, meaner, pure XSL, and comes with no more guarantees than the
last one, i.e., none.

[...]
-->
<xsl:stylesheet version="1.0" 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template name="word-count">
  <xsl:param name="in" select="."/>
  <xsl:call-template name="words-in-text">
    <xsl:with-param name="texts" select="$in//text()"/>
  </xsl:call-template>
</xsl:template>

<xsl:template name="words-in-text">
  <xsl:param name="texts"/>
  <xsl:param name="words" select="''"/>
  <xsl:param name="total" select="0"/>
  <xsl:choose>
    <xsl:when test="string-length($words) > 0">
      <xsl:call-template name="words-in-text">
        <xsl:with-param name="texts" select="$texts"/>
        <xsl:with-param name="words" select="substring-after($words, ' ')"/>
        <xsl:with-param name="total" select="$total+1"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:when test="count($texts) > 0">
      <xsl:call-template name="words-in-text">
        <xsl:with-param name="texts" select="$texts[position() > 1]"/>
        <xsl:with-param name="words" select="normalize-space($texts[1])"/>
        <xsl:with-param name="total" select="$total"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:otherwise>
      <xsl:value-of select="$total"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

</xsl:stylesheet>
