<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exsl="http://exslt.org/common"
  exclude-result-prefixes="exsl">

  <xsl:output method="text"/>

  <xsl:template match="/">
    <xsl:variable name="btree">
        <xsl:call-template name="partition">
          <xsl:with-param name="nodes" select="//node"/>
        </xsl:call-template>
    </xsl:variable>

    <xsl:call-template name="sum-binary-tree">
      <xsl:with-param name="bnode" select="exsl:node-set($btree)/*"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="sum-binary-tree">
    <xsl:param name="bnode"/>

    <xsl:choose>
      <xsl:when test="$bnode/node">
        <xsl:value-of select="$bnode/node/@v"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="first">
          <xsl:call-template name="sum-binary-tree">
            <xsl:with-param name="bnode" select="$bnode/b[1]"/>
          </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="second">
          <xsl:call-template name="sum-binary-tree">
            <xsl:with-param name="bnode" select="$bnode/b[2]"/>
          </xsl:call-template>
        </xsl:variable>
        <xsl:value-of select="$first + $second"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="partition">
    <xsl:param name="nodes"/>

    <xsl:variable name="half" select="floor(count($nodes) div 2)"/>

    <b>
      <xsl:choose>
        <xsl:when test="count($nodes) &lt;= 1">
          <!-- There is only one node left: stop dividing problem -->
          <xsl:copy-of select="$nodes"/>
        </xsl:when>
        <xsl:otherwise>
          <!-- divide in first half of nodes (left) -->
          <xsl:call-template name="partition">
            <xsl:with-param name="nodes" select="$nodes[position() &lt;= $half]"/>
          </xsl:call-template>
          <!-- divide in second half of nodes (right) -->
          <xsl:call-template name="partition">
            <xsl:with-param name="nodes" select="$nodes[position() &gt; $half]"/>
          </xsl:call-template>
        </xsl:otherwise>
      </xsl:choose>
    </b>
  </xsl:template>

</xsl:stylesheet>