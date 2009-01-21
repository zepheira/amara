<?xml version="1.0"?>

<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:doc="http://docbook.org/docbook/xml/4.0/namespace"
  xmlns:f="http://xmlns.4suite.org/ext"
  exclude-result-prefixes="f"
  version="1.0"
>
  <xsl:output method="text" encoding="us-ascii"/>
  <xsl:strip-space elements="doc:*"/>

  <!-- max width to wrap to -->
  <xsl:param name="maxwidth" select="78"/>

  <!-- flag to suppress whitespace around all doc:para elements -->
  <xsl:param name="noparaspace" select="0"/>

  <xsl:template match="/">
    <!-- build up the output doc with no width restrictions -->
    <xsl:variable name="output-buffer">
      <xsl:variable name='title'><xsl:apply-templates select='doc:article/doc:articleinfo/doc:title/child::node()|doc:book/doc:bookinfo/doc:title/child::node()|doc:book/doc:title/child::node()'/></xsl:variable>
      <xsl:value-of select="substring('                                                                               ', 1, (72 - string-length($title)) div 2)"/>
      <xsl:value-of select='$title'/>
      <xsl:text>&#10;</xsl:text>
      <xsl:value-of select="substring('                                                                               ', 1, (72 - string-length($title)) div 2)"/>
      <xsl:value-of select="substring('===============================================================================', 1, string-length($title))"/>
      <xsl:text>&#10;</xsl:text>
      <xsl:apply-templates/>
    </xsl:variable>
    <xsl:value-of select="f:wrap($output-buffer, $maxwidth)"/>
  </xsl:template>

  <xsl:template match="doc:author">
    <xsl:variable name="thisauthorname">
      <xsl:value-of select="concat(doc:firstname,' ')"/>
      <xsl:if test="normalize-space(doc:othername)">
        <xsl:value-of select="concat(doc:othername,' ')"/>
      </xsl:if>
      <xsl:value-of select="doc:surname"/>
    </xsl:variable>
    <xsl:value-of select="concat('Author: ',$thisauthorname)"/>
    <xsl:if test="doc:affiliation/doc:address/doc:email">
      <xsl:value-of select="concat(' &lt;',doc:affiliation/doc:address/doc:email,'&gt;')"/>
    </xsl:if>
    <xsl:if test='doc:affiliation/doc:orgname'>  
      <xsl:text> (</xsl:text><xsl:apply-templates select='doc:affiliation/doc:orgname'/><xsl:text>)</xsl:text>
    </xsl:if>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>

  <xsl:template match="doc:sect1|doc:section[not(ancestor::doc:section)]">
    <xsl:variable name='title'><xsl:apply-templates select='doc:title' mode='SHOW'/></xsl:variable>
    <xsl:if test='normalize-space($title)'>
      <xsl:text>&#10;</xsl:text>
      <xsl:value-of select="substring('                                                                               ', 1, (72 - string-length($title)) div 2)"/>
      <xsl:value-of select='normalize-space($title)'/>
      <xsl:text>&#10;</xsl:text>
      <xsl:value-of select="substring('                                                                               ', 1, (72 - string-length($title)) div 2)"/>
      <xsl:value-of select="substring('-------------------------------------------------------------------------------', 1, string-length($title))"/>
      <xsl:text>&#10;</xsl:text>
    </xsl:if>
    <xsl:apply-templates/>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>

  <xsl:template match="doc:sect2|doc:section[ancestor::doc:section]">
    <xsl:variable name='title'><xsl:apply-templates select='doc:title' mode='SHOW'/></xsl:variable>
    <xsl:if test='normalize-space($title)'>
      <xsl:text>&#10;:::</xsl:text>
      <xsl:variable name="depth" select="count(ancestor::doc:section)"/>
      <xsl:for-each select="document('')/xsl:stylesheet/xsl:template[position() &lt; $depth]">:</xsl:for-each>
      <xsl:value-of select="concat(' ',normalize-space($title),' ')"/>
      <xsl:text>&#10;</xsl:text>
    </xsl:if>
    <xsl:apply-templates/>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>

  <xsl:template match="doc:title"/>

  <xsl:template match="doc:title" mode="SHOW">
    <xsl:variable name="title">
      <xsl:apply-templates/>
    </xsl:variable>
    <xsl:value-of select="normalize-space($title)"/>
  </xsl:template>

  <xsl:template match="doc:itemizedlist">
    <!--<xsl:text>&#10;&#10;</xsl:text>-->
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="doc:listitem">
    <xsl:text>&#10;</xsl:text>
    <xsl:text>   *  </xsl:text><xsl:apply-templates/>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>

  <xsl:template match='doc:simplelist'>
    <xsl:apply-templates/>
  </xsl:template>
  
  <xsl:template match='doc:member'>
    <xsl:text>&#10;</xsl:text>
    <xsl:text>   *  </xsl:text><xsl:apply-templates select='*'/>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>

  <xsl:template match="doc:para">
    <xsl:choose>
      <xsl:when test="local-name(parent::*)='listitem' and count(../doc:para)=1">
        <xsl:apply-templates/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:if test="not($noparaspace)">
          <xsl:text>&#10;</xsl:text>
        </xsl:if>
        <xsl:apply-templates/>
        <xsl:text>&#10;</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="doc:emphasis">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="doc:superscript">
    <xsl:text>(</xsl:text><xsl:apply-templates/><xsl:text>)</xsl:text>
  </xsl:template>

  <xsl:template match="doc:subscript">
    <xsl:text>[</xsl:text><xsl:apply-templates/><xsl:text>]</xsl:text>
  </xsl:template>

  <xsl:template match="doc:link">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="doc:ulink">
    <xsl:apply-templates/>
    <xsl:value-of select="concat(' &lt;',@url,'&gt;')"/>
  </xsl:template>

  <xsl:template match="doc:glosslist">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="doc:glossentry">
    <xsl:text>   *  </xsl:text><xsl:apply-templates select="doc:glossterm"/><xsl:text> - </xsl:text><xsl:apply-templates select="doc:glossdef"/>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>

  <xsl:template match="doc:glossterm">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="doc:glossdef">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="doc:screen">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="doc:computeroutput">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- ignore any other docbook tags -->
  <xsl:template match="doc:*" priority="-1.0">
    <!-- <xsl:message>Hi!</xsl:message> -->
    <xsl:apply-templates select="doc:*"/>
  </xsl:template>


</xsl:stylesheet>
