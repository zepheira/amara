<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

  <xsl:output method="xml" indent="yes"/>

  <!-- take a wrapper with a header and an appStatus -->
  <xsl:template match="/">
    <header>
      <status><xsl:value-of select="//status"/></status>
      <!-- now the rest of the simple itemStatus elements -->
      <xsl:apply-templates select="*"/>
    </header>
  </xsl:template>

  <!-- kill the itemStatus/status since we've already output it -->
  <xsl:template match="status" />
  <xsl:template match="itemStatus/status" priority="1.0"/>

  <!-- and generate "attribute" elements with the rest... -->
  <xsl:template match="itemStatus/*">
    <attribute name="{name(.)}"><xsl:value-of
select="text()"/></attribute>
  </xsl:template>

</xsl:stylesheet>