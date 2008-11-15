<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exsl="http://exslt.org/common"
  exclude-result-prefixes="exsl">

  <xsl:output method="xml" indent="yes"/>

  <xsl:template match="/">
    <xsl:call-template name="partition-ranges">
      <xsl:with-param name="node" select="//node[1]"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="partition-ranges">
    <xsl:param name="node"/>
    <xsl:param name="s" select="(count($node/preceding-sibling::*)) + 1"/>
    <xsl:param name="e" select="(count($node/following-sibling::*)) + $s"/>

    <xsl:if test="$node">
      <xsl:element name="r">
        <xsl:attribute name="s">
          <xsl:value-of select="$s"/>
        </xsl:attribute>
        <xsl:attribute name="e">
          <xsl:value-of select="$e"/>
        </xsl:attribute>
        <xsl:choose>
          <xsl:when test="$s = $e">
            <xsl:copy-of select="$node"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:variable name="w" select="floor(($e - $s + 1) div 2)"/>
            <xsl:variable name="m" select="$s + $w"/>
            <xsl:call-template name="partition-ranges">
              <xsl:with-param name="node" select="$node"/>
              <xsl:with-param name="s" select="$s"/>
              <xsl:with-param name="e" select="$m - 1"/>
            </xsl:call-template>
            <xsl:call-template name="partition-ranges">
              <xsl:with-param name="node" select="$node/following-sibling::*[$w]"/>
              <xsl:with-param name="s" select="$m"/>
              <xsl:with-param name="e" select="$e"/>
            </xsl:call-template>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:element>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>