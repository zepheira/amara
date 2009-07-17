<xsl:stylesheet
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:boo="http://banquo.com"
 xmlns="http://duncan.com"
 version="1.0"
>

<xsl:template match="/boo:a">
  <foo><xsl:value-of select="translate(.,'&#10; ','')"/></foo>
</xsl:template>

</xsl:stylesheet>
