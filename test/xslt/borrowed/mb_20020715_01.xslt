<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="text" indent="yes" encoding="us-ascii"/>

  <xsl:template match="/">
    <result>
      <xsl:apply-templates select="//node()"/>
    </result>
  </xsl:template>

  <xsl:template match="*">
    <xsl:text>Element: </xsl:text>
    <xsl:value-of select="name()"/>
    <xsl:call-template name="report"/>
    <xsl:apply-templates select="@*"/>
  </xsl:template>
  <xsl:template match="@*">
    <xsl:text>Attribute: </xsl:text>
    <xsl:value-of select="name()"/>
    <xsl:call-template name="report"/>
  </xsl:template>

  <xsl:template match="text()">
    <xsl:text>Text node: </xsl:text>
    <xsl:value-of select="."/>
    <xsl:call-template name="report"/>
  </xsl:template>

  <xsl:template match="comment()">
    <xsl:text>Comment: </xsl:text>
    <xsl:value-of select="."/>
    <xsl:call-template name="report"/>
  </xsl:template>

  <xsl:template match="processing-instruction()">
    <xsl:text>P.I. node: </xsl:text>
    <xsl:value-of select="."/>
    <xsl:call-template name="report"/>
  </xsl:template>

  <xsl:template name="report">
    <xsl:text>&#10;# of descendants: </xsl:text>
    <xsl:value-of select="count(descendant::node())"/>
    <xsl:text>&#10;-----------------------------&#10;</xsl:text>
  </xsl:template>

</xsl:stylesheet>
