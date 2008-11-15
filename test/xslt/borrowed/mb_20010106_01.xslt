<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="xml" indent="yes"/>

  <xsl:template match="/">
    <result>
      <xsl:apply-templates/>
      <xsl:apply-templates mode="m"/>
    </result>
  </xsl:template>

  <xsl:template match="foo[@bar]" mode="m">
    <bar>matched foo[@bar] (mode m)</bar>
  </xsl:template>

  <xsl:template match="foo[@baz]" mode="m">
    <baz>matched foo[@baz] (mode m)</baz>
  </xsl:template>    

  <xsl:template match="foo[@bar]">
    <bar>matched foo[@bar]</bar>
  </xsl:template>

  <xsl:template match="foo[@baz]">
    <baz>matched foo[@baz]</baz>
  </xsl:template>    

</xsl:stylesheet>


