<?xml version='1.0'?>
<!-- wctest.xsl -->
<xsl:stylesheet version="1.0" 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:output method="text"/>
<xsl:include href="resources/wc.xslt"/>

<xsl:variable name="nwords">
  <xsl:call-template name="word-count">
    <xsl:with-param name="in" select="/"/>
  </xsl:call-template>
</xsl:variable>

<xsl:template match="/">
  Word count = <xsl:value-of select="$nwords"/>
</xsl:template>

</xsl:stylesheet>
