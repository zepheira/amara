<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
version='1.0'>

<xsl:template name="pad">
    <xsl:param name="String"/>
    <xsl:param name="length"/>
    <xsl:variable name="spaces"
                  select="'                                      '"/>
    <xsl:value-of select="substring(concat($String,$spaces),1,$length)"/>
</xsl:template>

<xsl:variable name="stuff">
  <xsl:call-template name="pad">
    <xsl:with-param name="String" select="/outer/inner/deep/@att2"/>
    <xsl:with-param name="length" select="15"/>
  </xsl:call-template>
</xsl:variable>

<xsl:template match='/'>
        <xsl:value-of select="$stuff"/>
</xsl:template>

</xsl:stylesheet>
