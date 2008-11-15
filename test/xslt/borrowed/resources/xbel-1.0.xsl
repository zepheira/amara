<?xml version="1.0" encoding="ISO-8859-1"?>

<!-- $Id: xbel-1.0.xsl,v 1.1 2001-09-15 21:31:01 molson Exp $ -->

<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns="http://www.w3.org/TR/xhtml1/strict">

  <xsl:variable name="nodes-mix" select="'bookmark|folder|alias|separator'"/>

  <xsl:output method="html" indent="yes" doctype-public="-//W3C//DTD HTML 4.0 Transitional//EN"/>

  <!-- XBEL ========================================================-->
  <xsl:template match="xbel">
    <html>
      <head>
        <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"/>
        <meta http-equiv="Pragma" content="no-cache"/>
        <meta http-equiv="Expires" content="0"/>
        <!-- !!! xbel/title is optional, should handle this -->
        <title><xsl:value-of select="title"/></title>
      </head>
      <body>
        <xsl:apply-templates/>
      </body>
    </html>
  </xsl:template>

  <!-- TITLE =======================================================-->
  <xsl:template match="xbel/title">
    <h1>
        <xsl:value-of select="."/>
        <!-- !!! handle xbel/@id, xbel/@added? -->
    </h1>
  </xsl:template>

  <xsl:template match="title">
    <!-- !!! use different tags according to depth instead of h3 -->
    <h3>
        <xsl:value-of select="."/>
    </h3>
  </xsl:template>

  <!-- INFO ========================================================-->
  <xsl:template match="info">
    <div>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <!-- INFO/METADATA ===============================================-->
  <xsl:template match="info/metadata">
    <em><xsl:value-of select="@owner"/></em><br/>
  </xsl:template>

  <!-- DESC ========================================================-->
  <xsl:template match="desc">
    <div>
      <small>
        <xsl:value-of select="."/>
      </small>
    </div>
  </xsl:template>

  <!-- FOLDER ======================================================-->
  <xsl:template match="folder">
    <!-- !!! handle @id, @added? -->
    <dl>
      <xsl:apply-templates/>
    </dl>
  </xsl:template>

  <!-- BOOKMARK ====================================================-->
  <xsl:template match="bookmark">
    <!-- !!! we ignore info, and expect a title! -->
    <dt>
      <a href="{@href}" target="_bookmark">
        <xsl:choose>
          <xsl:when test="string(title) != ''">
            <xsl:value-of select="title"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="@href"/>
          </xsl:otherwise>
        </xsl:choose>
      </a>
    </dt>
    <xsl:apply-templates select="desc"/>
  </xsl:template>

  <xsl:template match="bookmark/desc">
    <dd>
      <xsl:value-of select="."/>
    </dd>
  </xsl:template>

  <!-- ALIAS =======================================================-->
  <xsl:template match="alias">
    <b>!!! alias not supported !!!</b><br/>
  </xsl:template>

  <!-- SEPARATOR ===================================================-->
  <xsl:template match="separator">
    <hr size="1"/>
  </xsl:template>

</xsl:stylesheet>
