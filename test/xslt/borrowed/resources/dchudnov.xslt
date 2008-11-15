<?xml version="1.0"?>

<!-- Identify transformation -->
<xsl:stylesheet version="1.1"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="html" indent="no"/>
  <xsl:strip-space elements="*"/>

  <xsl:include href="dchudnov-basic.xslt"/>
  <xsl:include href="dchudnov-urlpattern.xslt"/>


  <xsl:variable name="dataurl" select="//request/dataurl"/>
  <xsl:variable name="searchurl" select="//request/searchurl"/>

  <xsl:template match="/">
    <html>
      <xsl:apply-templates/>
    </html>
  </xsl:template>

  <xsl:template match="search">
    <xsl:apply-templates select="request"/>
    <xsl:apply-templates select="results"/>
  </xsl:template>

  <xsl:template match="request">
    <xsl:variable name="count" select="count( //results/authrecord ) +
                                       count( //results/titlerecord )"/>
    <p>Your search:
      <xsl:choose>
        <xsl:when test="@type='issn'">
          <b><xsl:value-of select="terms/@issn"/></b>
        </xsl:when>
        <xsl:when test="@type='title'">
          <b><xsl:value-of select="terms"/></b>
        </xsl:when>
        <xsl:when test="@type='subject'">
          <b><xsl:value-of select="terms/@class"/>:
             <xsl:value-of select="terms"/></b>
        </xsl:when>
        <xsl:when test="@type='jakeid'">
          <b><xsl:value-of select="terms/@jakeid"/></b>
        </xsl:when>
      </xsl:choose>
      <font size="-1"> (<xsl:value-of select="@type"/>)</font>
      <xsl:choose>
        <xsl:when test="$count=1">
          <xsl:text> (1 match)</xsl:text>
        </xsl:when>
        <xsl:when test="$count>1">
          <xsl:text> (</xsl:text>
          <xsl:value-of select="$count"/>
          <xsl:text> matches)</xsl:text>
        </xsl:when>
        <xsl:when test="$count=0">
          <xsl:text> (0 matches)</xsl:text>
        </xsl:when>
      </xsl:choose>
    </p>
  </xsl:template>

  <xsl:template match="results">
    <table border="0" width="100%" cellspacing="0" cellpadding="1" bgcolor="cccccc">
      <tr><td>
        <xsl:choose>
          <xsl:when test="boolean( //request/localurl )">
            <xsl:variable name="indexurl" select="concat( //request/localurl, //results/index )"/>
            <xsl:variable name="localinfo" select="document( $indexurl )"/>
            <xsl:apply-templates select="authrecord">
              <xsl:with-param name="localinfo"/>
            </xsl:apply-templates>
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates select="authrecord"/>
          </xsl:otherwise>
        </xsl:choose>
        <xsl:apply-templates select="titlerecord"/>
      </td></tr>
    </table>
  </xsl:template>


</xsl:stylesheet>
