<?xml version='1.0'?>
<xsl:stylesheet version="1.0" 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text"/>

<xsl:variable name="textnode">Text node</xsl:variable>

<xsl:template match="/">
  <xsl:for-each select="document('')/*/xsl:variable">
    <xsl:text>child::text() = </xsl:text>
      <xsl:choose><xsl:when test="child::text()">true</xsl:when>
                  <xsl:otherwise>false</xsl:otherwise></xsl:choose>
    <xsl:text>&#xa;</xsl:text>
  </xsl:for-each>
  <xsl:for-each select="document('')/*/xsl:variable/text()">
    <xsl:text>self::text() = </xsl:text>
      <xsl:choose><xsl:when test="self::text()">true</xsl:when>
                  <xsl:otherwise>false</xsl:otherwise></xsl:choose>
    <xsl:text>&#xa;</xsl:text>
  </xsl:for-each>
</xsl:template>

</xsl:stylesheet>