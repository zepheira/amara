<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:foo="http://foo.com"
  version="1.0"
>
<!-- identity transforms. -->
<xsl:template match="*">
  <xsl:element name="{name(.)}" xmlns="http://www.w3.org/1999/xhtml">
    <xsl:apply-templates select="@*" />
    <xsl:apply-templates />
    </xsl:element>
</xsl:template>
<xsl:template match="@*">
  <xsl:copy-of select="." />
</xsl:template>
</xsl:stylesheet>