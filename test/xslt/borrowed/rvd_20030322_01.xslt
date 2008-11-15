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

    <!-- Gets the groups -->
    <xsl:variable name="groups">
      <xsl:apply-templates select="$sorted-tree-fragment"/>
    </xsl:variable>

    <!-- Iterate through all the groups -->
    <xsl:for-each select="exsl:node-set($groups)/*">
      <xsl:variable name="country" select="@id"/>
      <xsl:copy>
        <xsl:copy-of select="@*"/>
        <!-- Copy the nodes with the same country -->
        <xsl:copy-of select="$sorted-tree-fragment[@country = $country]"/>
      </xsl:copy>
    </xsl:for-each>
  </xsl:template>

  <xsl:template match="city">
    <xsl:variable name="preceding" select="./preceding-sibling::*[1]"/>
    <xsl:if test="not(./@country = $preceding/@country)">
      <group id="{./@country}"/>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>