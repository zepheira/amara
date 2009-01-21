<?xml version="1.0"?>
<!--

 File Name:            docbook_html1.xslt

 Simple DocBook Stylesheet
 WWW: http://4suite.com/4XSLT        e-mail: support@4suite.com

 Copyright 2002 Fourthought Inc, USA.
 See  http://4suite.com/COPYRIGHT  for license and copyright information

-->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:doc="http://docbook.org/docbook/xml/4.0/namespace"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  exclude-result-prefixes="doc dc"
>

  <xsl:output method="html" encoding="ISO-8859-1"/>

  <xsl:param name="top-level-html" select="1"/>
  <xsl:param name="number-sections" select="'yes'"/>
  <xsl:param name="mark-untitled-sections" select="'yes'"/>
  <xsl:param name="css-file"/>
  <xsl:param name="literal-css"/>
  <xsl:variable name="colspan"/>

  <dc:Creator>Fourthought</dc:Creator>
  <dc:Title>docbook_html1.xslt</dc:Title>

  <xsl:variable name='authorname'>
    <xsl:for-each select="/doc:article/doc:articleinfo/doc:author">
      <xsl:value-of select="concat(doc:firstname,' ')"/>
      <xsl:if test="normalize-space(doc:othername)">
        <xsl:value-of select="concat(doc:othername,' ')"/>
      </xsl:if>
      <xsl:value-of select="doc:surname"/>
      <xsl:if test="position() != last()">, </xsl:if>
    </xsl:for-each>
  </xsl:variable>

  <xsl:template match="/">
    <xsl:choose>
      <xsl:when test="$top-level-html = 1">
        <HTML>
        <HEAD>
          <xsl:apply-templates mode='HEADING'/>
          <xsl:call-template name='CSS'/>
        </HEAD>
        <BODY>
          <xsl:apply-templates/>
        </BODY>
        </HTML>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="doc:article|doc:book">
    <xsl:choose>
      <xsl:when test="$top-level-html = 1">
        <xsl:if test="doc:title">
          <H1><xsl:apply-templates select='doc:title' mode='SHOW'/></H1>
        </xsl:if>
        <xsl:apply-templates select="doc:articleinfo|doc:bookinfo" mode="BODY"/>
        <HR/>
        <xsl:call-template name='toc'/>
        <xsl:apply-templates/>
      </xsl:when>
      <xsl:otherwise>
        <H1><xsl:apply-templates select='doc:articleinfo/doc:title|doc:title|doc:bookinfo/doc:title' mode='SHOW'/></H1>
        <xsl:apply-templates/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name='toc'>
    <xsl:if test="descendant::doc:section|descendant::doc:sect1|descendant::doc:sect2">
      <TABLE BORDER='0'>
        <xsl:apply-templates select='*' mode='toc'/>
      </TABLE>
      <HR/>
    </xsl:if>
  </xsl:template>

  <xsl:template match="doc:articleinfo|doc:bookinfo" mode="HEADING">
    <META NAME="author" CONTENT="{$authorname}"/>
    <META NAME="keywords" CONTENT="{doc:keywordset/doc:keyword}"/>
    <META NAME="description" CONTENT="{normalize-space(doc:keywordset/doc:keyword)}"/>
    <TITLE><xsl:apply-templates select='doc:title/child::node()|../doc:title/child::node()'/></TITLE>
  </xsl:template>

  <xsl:template match="doc:articleinfo|doc:bookinfo" mode="BODY">
    <xsl:if test="doc:title">
      <H1><xsl:apply-templates select='doc:title' mode='SHOW'/></H1>
    </xsl:if>
    <xsl:if test="doc:author|doc:revhistory|doc:revision">
      <DIV>
        <xsl:apply-templates select='doc:author' mode='HEADING'/>
        <BR/>
        <xsl:apply-templates select='doc:revhistory/doc:revision[1]' mode='HEADING'/>
      </DIV>
    </xsl:if>
    <xsl:apply-templates select='doc:abstract'/>
  </xsl:template>

  <xsl:template match="doc:articleinfo|doc:bookinfo"/>

  <xsl:template match="doc:title" mode="SHOW">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="doc:title"/>

  <xsl:template match="doc:abstract">
    <DIV CLASS='abstract'>
      <xsl:apply-templates/>
    </DIV>
  </xsl:template>

  <xsl:template match='text()' mode='toc'/>
  <xsl:template match='text()' mode='HEADING'/>

  <xsl:template match='doc:sect1' mode='toc'>
    <TR VALIGN='top'>
      <TD WIDTH='5%'><xsl:number format='1.' count='doc:sect1' level='multiple'/></TD>
      <TD>
        <xsl:call-template name='section-title-and-link'/>
        <xsl:if test="doc:sect2">
          <BR/>
          <TABLE BORDER='0'>
            <xsl:apply-templates select='doc:sect2' mode='toc'/>
          </TABLE>
        </xsl:if>
      </TD>
    </TR>
  </xsl:template>

  <xsl:template match='doc:sect2' mode='toc'>
    <TR VALIGN='top'>
      <TD WIDTH='5%'><xsl:number format='1.' count='doc:sect1|doc:sect2' level='multiple'/></TD>
      <TD>
        <xsl:call-template name='section-title-and-link'/>
      </TD>
    </TR>
    <xsl:apply-templates select='doc:sect2' mode='toc'/>
  </xsl:template>

  <xsl:template match='doc:section' mode='toc'>
    <xsl:if test='doc:title or $mark-untitled-sections = "yes"'>
      <TR VALIGN='top'>
        <TD WIDTH='5%'>
          <xsl:if test='$number-sections = "yes"'>
            <xsl:number format='1.' count='doc:section' level='multiple'/>
          </xsl:if>
          <xsl:text>&#160;</xsl:text>
        </TD>
        <TD>
          <xsl:call-template name='section-title-and-link'/>
          <xsl:if test="doc:section">
            <BR/>
            <TABLE BORDER='0'>
              <xsl:apply-templates select='doc:section' mode='toc'/>
            </TABLE>
          </xsl:if>
        </TD>
      </TR>
    </xsl:if>
  </xsl:template>

  <xsl:template name='section-title-and-link'>
    <xsl:choose>
      <xsl:when test="doc:title/doc:anchor">
        <A>
          <xsl:attribute name="HREF">
            <xsl:value-of select="concat('#',doc:title/doc:anchor/@id|doc:title/doc:anchor/@ID)"/>
          </xsl:attribute>
          <xsl:choose>
            <xsl:when test='doc:title/doc:anchor/child::node()|doc:title/text()'>
              <xsl:value-of select='doc:title/doc:anchor/child::node()|doc:title/text()'/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:text>[No title]</xsl:text>
            </xsl:otherwise>
          </xsl:choose>
        </A>
      </xsl:when>
      <xsl:otherwise>
        <A>
          <xsl:attribute name="HREF">
            <xsl:value-of select="concat('#',generate-id())"/>
          </xsl:attribute>
          <xsl:choose>
            <xsl:when test='normalize-space(doc:title)'>
              <xsl:value-of select='doc:title'/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:text>[No title]</xsl:text>
            </xsl:otherwise>
          </xsl:choose>
        </A>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:attribute-set name="doc:ol-style">
    <xsl:attribute name="start">1</xsl:attribute>
    <xsl:attribute name="type">1</xsl:attribute>
  </xsl:attribute-set>

  <xsl:template match="doc:author" mode="HEADING">
    <xsl:variable name="thisauthorname">
      <xsl:value-of select="concat(doc:firstname,' ')"/>
      <xsl:if test="normalize-space(doc:othername)">
        <xsl:value-of select="concat(doc:othername,' ')"/>
      </xsl:if>
      <xsl:value-of select="doc:surname"/>
    </xsl:variable>
    <xsl:choose>
      <xsl:when test="doc:affiliation/doc:address/doc:email">
        <A HREF="mailto:{doc:affiliation/doc:address/doc:email}">
          <xsl:value-of select="$thisauthorname"/>
        </A>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$thisauthorname"/>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:if test='doc:affiliation/doc:orgname'>
      <xsl:text> (</xsl:text><xsl:apply-templates select='doc:affiliation/doc:orgname'/><xsl:text>)</xsl:text>
    </xsl:if>
    <xsl:if test="position() != last()">, </xsl:if>
  </xsl:template>

  <xsl:template match="doc:revision" mode="HEADING">
    <xsl:text>Revision </xsl:text><xsl:value-of select='doc:revnum'/>
    <xsl:text> (</xsl:text><xsl:value-of select='doc:revremark'/><xsl:text>)</xsl:text>
    <xsl:text> [</xsl:text><xsl:value-of select='doc:authorinitials'/><xsl:text>]</xsl:text>
  </xsl:template>

  <xsl:template match="doc:sect1">
    <DIV>
      <xsl:if test="@role">
        <xsl:attribute name='CLASS'><xsl:value-of select='@role'/></xsl:attribute>
      </xsl:if>
      <H3>
        <xsl:number format='1.' count='doc:sect1' level='multiple'/>
        <xsl:text>&#160;</xsl:text>
        <xsl:call-template name='section-title-and-anchor'/>
      </H3>
      <xsl:apply-templates/>
    </DIV>
  </xsl:template>

  <xsl:template match="doc:sect2">
    <DIV STYLE="margin-left: 1em">
      <xsl:if test="@role">
        <xsl:attribute name='CLASS'><xsl:value-of select='@role'/></xsl:attribute>
      </xsl:if>
      <H4>
        <xsl:number format='1.' count='doc:sect1|doc:sect2' level='multiple'/>
        <xsl:text>&#160;</xsl:text>
        <xsl:call-template name='section-title-and-anchor'/>
      </H4>
      <xsl:apply-templates/>
    </DIV>
  </xsl:template>

  <xsl:template match="doc:section">
    <DIV STYLE="margin-left: 1em">
      <xsl:if test="@role">
        <xsl:attribute name='CLASS'><xsl:value-of select='@role'/></xsl:attribute>
      </xsl:if>
      <xsl:if test='doc:title or $mark-untitled-sections = "yes"'>
        <xsl:variable name="section-level" select="count(ancestor::doc:section)"/>
        <xsl:variable name="hlevel">
          <xsl:choose>
            <xsl:when test="$section-level &gt; 1">4</xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="2 + $section-level"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <!-- H2, H3, H4 depending on depth -->
        <xsl:element name="{concat('H',$hlevel)}">
          <xsl:if test='$number-sections = "yes"'>
            <xsl:number format='1.' count='doc:section' level='multiple'/>
            <xsl:text>&#160;</xsl:text>
          </xsl:if>
          <xsl:call-template name='section-title-and-anchor'/>
        </xsl:element>
      </xsl:if>
      <xsl:apply-templates/>
    </DIV>
  </xsl:template>

  <xsl:template name='section-title-and-anchor'>
    <xsl:choose>
      <xsl:when test="doc:title/doc:anchor">
        <A>
          <xsl:attribute name="NAME">
            <xsl:value-of select="concat('#',doc:title/doc:anchor/@id|doc:title/doc:anchor/@ID)"/>
          </xsl:attribute>
          <xsl:apply-templates select="doc:title/doc:anchor/child::node()|doc:title/text()" mode="SHOW"/>
        </A>
      </xsl:when>
      <xsl:otherwise>
        <A>
          <xsl:attribute name="NAME">
            <xsl:value-of select="concat('#',generate-id())"/>
          </xsl:attribute>
          <xsl:apply-templates select="doc:title" mode="SHOW"/>
        </A>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="doc:orderedlist">
    <OL xsl:use-attribute-sets="doc:ol-style">
      <xsl:if test="@role">
        <xsl:attribute name='CLASS'><xsl:value-of select='@role'/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </OL>
  </xsl:template>

  <xsl:template match="doc:itemizedlist">
    <UL>
      <xsl:if test="@role">
        <xsl:attribute name='CLASS'><xsl:value-of select='@role'/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </UL>
  </xsl:template>

  <xsl:template match="doc:listitem">
    <LI><xsl:apply-templates/></LI>
  </xsl:template>

  <xsl:template match="doc:para">
    <DIV>
      <xsl:if test="@role">
        <xsl:attribute name='CLASS'><xsl:value-of select='@role'/></xsl:attribute>
      </xsl:if>
      <P><xsl:apply-templates/></P>
    </DIV>
  </xsl:template>

  <xsl:template match="doc:superscript">
    <SUP><SMALL><xsl:apply-templates/></SMALL></SUP>
  </xsl:template>

  <xsl:template match="doc:subscript">
    <SUB><SMALL><xsl:apply-templates/></SMALL></SUB>
  </xsl:template>

  <xsl:template match="doc:computeroutput">
    <SAMP><xsl:apply-templates/></SAMP>
  </xsl:template>

  <xsl:template match="doc:filename">
    <SAMP><xsl:apply-templates/></SAMP>
  </xsl:template>

  <xsl:template match="doc:screen">
    <DIV>
      <xsl:if test="@role">
        <xsl:attribute name='CLASS'><xsl:value-of select='@role'/></xsl:attribute>
      </xsl:if>
      <PRE><xsl:apply-templates/></PRE>
    </DIV>
  </xsl:template>

  <xsl:template match="doc:glosslist">
    <DL>
      <xsl:if test="@role">
        <xsl:attribute name='CLASS'><xsl:value-of select='@role'/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates select="doc:glossentry"/>
    </DL>
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
    <xsl:message>Error: It should be "doc:emphasis", not "doc:emph".  Please correct this document.</xsl:message>
    <I><xsl:apply-templates/></I>
  </xsl:template>

  <xsl:template match='doc:emphasis'>
    <xsl:choose>
      <xsl:when test="@role = 'bold'">
        <B><xsl:apply-templates/></B>
      </xsl:when>
      <xsl:when test="@role = 'full'">
        <I><B><xsl:apply-templates/></B></I>
      </xsl:when>
      <xsl:when test="not(@role)">
        <I><xsl:apply-templates/></I>
      </xsl:when>
      <xsl:otherwise>
        <SPAN>
          <xsl:if test="@role">
            <xsl:attribute name='CLASS'><xsl:value-of select='@role'/></xsl:attribute>
          </xsl:if>
          <xsl:apply-templates/>
        </SPAN>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match='doc:mediaobject'>
    <IMG SRC='{doc:imageobject/doc:imagedata/@fileref}' ALT='{doc:textobject/doc:phrase}'/>
  </xsl:template>

  <xsl:template match='doc:strong'>
    <B><xsl:apply-templates/></B>
  </xsl:template>

  <xsl:template match='doc:link'>
    <A HREF="#{@linkend}"><xsl:apply-templates/></A>
  </xsl:template>

  <xsl:template match='doc:anchor'>
    <xsl:variable name="id" select="@ID|@id"/>
    <A NAME="{$id}" ID="{$id}"><xsl:apply-templates/></A>
  </xsl:template>

  <xsl:template match='doc:ulink'>
    <xsl:if test="@linkend">
      <xsl:message>Warning: you probably meant to use the attribute "url" rather than "linkend", which is wrong and will soon no longer work.</xsl:message>
    </xsl:if>
    <A HREF="{@url|@linkend}"><xsl:apply-templates/></A>
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

  <xsl:template match='doc:table'>
    <TABLE>
          <xsl:if test="@role">
            <xsl:attribute name='CLASS'><xsl:value-of select='@role'/></xsl:attribute>
          </xsl:if>
      <xsl:if test="@frame='none'">
        <xsl:attribute name='border'>0</xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </TABLE>
  </xsl:template>

  <xsl:template match='doc:row'>
<!--
    <TR>
      <xsl:if test='@role'>
        <xsl:attribute name='class'><xsl:value-of select='@role'/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </TR>
-->
      <xsl:if test='@role'>
    <TR class='{@role}'>
      <xsl:apply-templates/>
    </TR>
      </xsl:if>
      <xsl:if test='not(@role)'>
    <TR>
      <xsl:apply-templates/>
    </TR>
      </xsl:if>
  </xsl:template>

  <xsl:template match='doc:entry'>
    <xsl:choose>
      <xsl:when test='@spanname'>
        <xsl:variable name="spanspec" select="ancestor::doc:table[1]/doc:spanspec[@spanname=current()/@spanname]"/>
        <!-- FIXME: This logic will break if a colspec has a colnum attr out of sequence -->
        <xsl:variable name="colspecs" select="ancestor::doc:table[1]/doc:colspec"/>
        <xsl:variable name="start" select="count($colspecs[@colname=$spanspec/@namest]/preceding-sibling::doc:colspec)+1"/>
        <xsl:variable name="end" select="count($colspecs[@colname=$spanspec/@nameend]/preceding-sibling::doc:colspec)+1"/>
        <xsl:variable name="colspan" select="$end - $start"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="colspan"/>
      </xsl:otherwise>
    </xsl:choose>
    <TD>
      <xsl:if test="$colspan">
        <xsl:attribute name='COLSPAN'><xsl:value-of select="$colspan"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </TD>
  </xsl:template>

  <!-- ignore any other docbook tags -->
  <xsl:template match="doc:*" priority="-1.0">
    <xsl:apply-templates select="doc:*"/>
  </xsl:template>

  <xsl:template name="CSS">
    <xsl:if test='$css-file'>
      <link rel='stylesheet' href='{$css-file}' type='text/css'/>
    </xsl:if>
    <xsl:if test='$literal-css'>
      <style type="text/css">
        <xsl:value-of select="$literal-css"/>
      </style>
    </xsl:if>
  </xsl:template>

  <xsl:template match="doc:trademark">
    <xsl:if test="@class='copyright'">&#169;&#160;</xsl:if>
    <xsl:apply-templates/>
    <xsl:choose>
      <xsl:when test="@class='registered'"><sup style="font-size: 75%; vertical-align: top">&#174;</sup></xsl:when>
      <xsl:when test="@class='service'"><sup style="font-size: 75%; vertical-align: top">&#8480;</sup></xsl:when>
      <xsl:when test="@class='copyright'"/> <!-- avoids falling into otherwise clause -->
      <xsl:otherwise><sup style="font-size: 75%; vertical-align: top">&#8482;</sup></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
