<?xml version="1.0"?>
<!-- #Uche Ogbuji's docbook test: pretty much just checking one small plot of
performance scale -->

<!--

 Original File Name:            docbook_html1.xslt

 Documentation:        http://docs.4suite.org/stylesheets/docbook_html1.xslt.html

 Simple DocBook Stylesheet
 WWW: http://4suite.org/4XSLT        e-mail: support@4suite.org

 Copyright (c) 1999-2001 Fourthought Inc, USA.   All Rights Reserved.
 See  http://4suite.org/COPYRIGHT  for license and copyright information
-->

<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:doc="http://docbook.org/docbook/xml/4.0/namespace"
  version="1.0"
>

  <xsl:output method="html" encoding="ISO-8859-1"/>

  <xsl:param name="top-level-html" select="1"/>

  <xsl:template match="/">
    <xsl:choose>
      <xsl:when test="$top-level-html">
        <HTML>
        <HEAD>
          <TITLE><xsl:value-of select='doc:article/doc:artheader/doc:title'/></TITLE>
          <META HTTP-EQUIV="content-type" CONTENT="text/html" charset="UTF-8"/>
          <META NAME="author" CONTENT="{doc:article/doc:artheader/doc:author}"/>
        </HEAD>
        <BODY>
          <H1><xsl:value-of select='doc:article/doc:artheader/doc:title'/></H1>
          <xsl:apply-templates/>
        </BODY>
        </HTML>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:attribute-set name="doc:ol-style">
    <xsl:attribute name="start">1</xsl:attribute>
    <xsl:attribute name="type">1</xsl:attribute>
  </xsl:attribute-set>

  <xsl:template match="doc:sect1">
    <H3><xsl:value-of select="doc:title"/></H3>
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="doc:sect2">
    <H4><xsl:value-of select="doc:title"/></H4>
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="doc:orderedlist">
    <OL xsl:use-attribute-sets="doc:ol-style"><xsl:apply-templates/></OL>
  </xsl:template>

  <xsl:template match="doc:itemizedlist">
    <UL><xsl:apply-templates/></UL>
  </xsl:template>

  <xsl:template match="doc:listitem">
    <LI><xsl:apply-templates/></LI>
  </xsl:template>

  <xsl:template match="doc:para">
    <P><xsl:apply-templates/></P>
  </xsl:template>

  <xsl:template match="doc:computeroutput">
    <SAMP><xsl:apply-templates/></SAMP>
  </xsl:template>

  <xsl:template match="doc:filename">
    <SAMP><xsl:apply-templates/></SAMP>
  </xsl:template>

  <xsl:template match="doc:screen">
    <PRE><xsl:apply-templates/></PRE>
  </xsl:template>

  <xsl:template match="doc:glosslist">
    <DL><xsl:apply-templates/></DL>
  </xsl:template>

  <xsl:template match="doc:glossentry">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="doc:glossterm">
    <DT><I><xsl:apply-templates/></I></DT>
  </xsl:template>

  <xsl:template match="doc:glossdef">
    <DD><xsl:apply-templates/></DD>
  </xsl:template>

  <xsl:template match='doc:emph'>
    <I><xsl:apply-templates/></I>
  </xsl:template>

  <xsl:template match='doc:mediaobject'>
    <IMG SRC='{doc:imageobject/@fileref}' ALT='{doc:textobject/doc:phrase}'></IMG>
  </xsl:template>

  <xsl:template match='doc:strong'>
    <B><xsl:apply-templates/></B>
  </xsl:template>

  <xsl:template match='doc:link'>
    <A HREF="{@linkend}"><xsl:apply-templates/></A>
  </xsl:template>

  <xsl:template match='doc:align'>
    <DIV ALIGN="{@style}"><xsl:apply-templates/></DIV>
  </xsl:template>

  <xsl:template match='doc:separator'>
    <HR/>
  </xsl:template>

  <xsl:template match='doc:simplelist'>
    <DL><xsl:apply-templates/></DL>
  </xsl:template>
  
  <xsl:template match='doc:member'>
    <DD><xsl:apply-templates/></DD>
  </xsl:template>
  
  <xsl:template match='doc:note'>
    <BLOCKQUOTE>
      <I><B>
      <!-- Emphasize the title -->
      <xsl:choose>
        <xsl:when test='doc:title'>
          <xsl:value-of select='doc:title'/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>Note</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
      </B></I>
      <xsl:apply-templates/>
    </BLOCKQUOTE>
  </xsl:template>

  <!-- ignore any other docbook tags -->
  <xsl:template match="doc:*" priority="-1.0">
    <!-- <xsl:message>Hi!</xsl:message> -->
    <xsl:apply-templates select="doc:*"/>
  </xsl:template>

</xsl:stylesheet>
