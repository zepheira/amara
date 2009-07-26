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
<xsl:apply-templates select="verse[@id='rv1.84.10']/mantra"/>
</verse>
</xsl:template>

<xsl:template match="verse[@id='rv1.84.10']/mantra">
<xsl:copy-of select="."/>
<xsl:variable name="x" select="position()"/>
<xsl:copy-of select="../../verse[@id='rv1.16.1']/mantra[position()=$x]"/>
</xsl:template>

</xsl:stylesheet>
