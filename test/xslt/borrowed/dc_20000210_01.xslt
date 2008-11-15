<xsl:stylesheet
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 version="1.0"
>

<xsl:template match="/a">
  <foo><xsl:value-of select="translate(.,'&#10; ','')"/></foo>
</xsl:template>

</xsl:stylesheet>