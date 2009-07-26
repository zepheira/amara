<!--
 XT Bug Report from David Hunter <david.hunter@mobileQ.COM> on 30 May 
 2000, with additional checks
-->
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text"/>

<xsl:template match="/nodes/node[1]">
  <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="/nodes/node[2]">
  <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="/nodes/node[3]">
  <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="text()"/>
</xsl:stylesheet>
