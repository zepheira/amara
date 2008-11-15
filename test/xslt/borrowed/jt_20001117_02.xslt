<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:dem="http://www.democrat.org/"
                xmlns:rep="http://www.republican.org/">

<xsl:template match="vote">
   <xsl:copy>
      <xsl:attribute name="dem:count" namespace="http://www.democrat.org/">
        <xsl:value-of select="@rep:count - 432" />
      </xsl:attribute>
      <xsl:copy-of select="@*[not(self::dem:count)]" />
   </xsl:copy>
</xsl:template>

</xsl:stylesheet>