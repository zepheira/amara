<!--
Example from David Carlisle <davidc@nag.co.uk> to John Robert Gardner 
<jrgardn@emory.edu> on 10 Jan 2000
-->
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