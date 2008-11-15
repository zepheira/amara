<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exsl="http://exslt.org/common"
  exclude-result-prefixes="exsl">

  <xsl:output method="xml" indent="yes"/>

  <xsl:template match="/">
    <result>
      <xsl:apply-templates/>
    </result>
  </xsl:template>

  <xsl:template match="cities">
    <xsl:variable name="sorted">
      <xsl:for-each select="./city">
        <xsl:sort select="@country"/>
        <xsl:copy-of select="."/>
      </xsl:for-each>
    </xsl:variable>

    <xsl:variable name="sorted-tree-fragment" select="exsl:node-set($sorted)/*"/>

    <xsl:variable name="groups">
      <xsl:apply-templates select="exsl:node-set($sorted)/*[1]"/>
    </xsl:variable>

    <xsl:apply-templates select="exsl:node-set($groups)/*"/>

  </xsl:template>

  <xsl:template match="city">
    <xsl:variable name="preceding" select="./preceding-sibling::*[1]"/>
    <xsl:choose>
      <xsl:when test="not(./@country = $preceding/@country)">
        <group id="{./@country}">
          <xsl:copy-of select="."/>
          <xsl:apply-templates select="./following-sibling::*[1]"/>
        </group>
      </xsl:when>
      <xsl:otherwise>
        <xsl:copy-of select="."/>
        <xsl:apply-templates select="./following-sibling::*[1]"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

<!-- bad: unoptimizable
  <xsl:template match="group">
    <xsl:copy>
      <xsl:copy-of select="@*"/>
      <xsl:copy-of select="./city"/>
    </xsl:copy>
    <xsl:apply-templates select="./group"/>
  </xsl:template>
-->

  <xsl:template match="group">
    <xsl:call-template name="process-group">
      <xsl:with-param name="group-node" select="."/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="process-group">
    <xsl:param name="group-node"/>
    <xsl:if test="$group-node">
      <xsl:copy>
        <xsl:copy-of select="$group-node/@*"/>
        <xsl:copy-of select="$group-node/city"/>
      </xsl:copy>
      <xsl:call-template name="process-group">
        <xsl:with-param name="group-node" select="$group-node/group"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>