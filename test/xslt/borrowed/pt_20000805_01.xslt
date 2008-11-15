<xsl:stylesheet
xmlns:xsl='http://www.w3.org/1999/XSL/Transform' version="1.0">
<xsl:output method="xml" indent="yes"/>

<xsl:template match="/">
<doc>
 <xsl:for-each select="/doc/*">
      <xsl:sort select="code"/>
      <xsl:copy-of select="."/>
 </xsl:for-each>
</doc>
</xsl:template>
</xsl:stylesheet>