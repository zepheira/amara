<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:output method="text" encoding="ISO-8859-1"/>

<xsl:param name="what" select="'this'"/>

<xsl:template match="/">
  <xsl:apply-templates select="test">
        <xsl:with-param name="what" select="concat($what,',root')"/>
  </xsl:apply-templates>
</xsl:template>

<xsl:template match="test">
  <xsl:param name="what" select="''"/>
  <xsl:apply-templates select="data">
        <xsl:with-param name="what" select="concat($what,',test')"/>
  </xsl:apply-templates>
  <xsl:apply-templates select="data">
        <xsl:with-param name="what" select="concat($what,',rerun')"/>
  </xsl:apply-templates>
</xsl:template>

<xsl:template match="data">
  <xsl:param name="what" select="''"/>
  <xsl:value-of select="."/>
  <xsl:text> </xsl:text>
  <xsl:value-of select="$what"/>
  <xsl:text>
</xsl:text>
</xsl:template>

</xsl:stylesheet>