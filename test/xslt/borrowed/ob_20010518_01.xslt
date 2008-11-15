<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="el">
   <xsl:copy>
      <xsl:copy-of select="@*" />
      <xsl:attribute name="prefix:att2" 
                     namespace="uri2">bar</xsl:attribute>
   </xsl:copy>
</xsl:template>

</xsl:stylesheet>