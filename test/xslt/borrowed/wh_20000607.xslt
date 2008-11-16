<?xml version="1.0" encoding="UTF-8"?>
<!--
#Further analysis, by Warren Hedley <w.hedley@auckland.ac.nz> on 7 June 2000, of the XT bug report
-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

<xsl:template match="doc/div[last()=1]">
  <xsl:value-of select="." />
  <xsl:text> (</xsl:text>
  <xsl:value-of select="position()" />
  <xsl:text> - </xsl:text>
  <xsl:value-of select="last()" />
  <xsl:text>)
</xsl:text>
</xsl:template>

<xsl:template match="text()" />

</xsl:stylesheet>
