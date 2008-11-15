<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version="1.0"
  >

<xsl:output method="xml" indent="yes"/>

<xsl:template match="sample">
<verse>
<xsl:for-each select="verse/mantra">
<xsl:sort select="substring-after(@id,../@id)"/>
<xsl:sort select="../@id" order="descending"/>
<xsl:copy-of select="."/>
</xsl:for-each>
</verse>
</xsl:template>

</xsl:stylesheet>