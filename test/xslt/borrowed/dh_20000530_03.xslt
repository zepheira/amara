<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text"/>

<xsl:template match="/nodes/node[last()]">
  <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="text()"/>

<xsl:template match="/nodes/*" priority="-10">
<xsl:text>Hello</xsl:text>
</xsl:template>

</xsl:stylesheet>