<xsl:stylesheet version='1.0'
                xmlns:xsl='http://www.w3.org/1999/XSL/Transform'>

  <xsl:template match='condition'>
    <xsl:element name='template'>
      <xsl:attribute name='match'>
        <xsl:value-of select='.'/>
      </xsl:attribute>
      <xsl:text>This is a good one</xsl:text>
    </xsl:element>
  </xsl:template>
</xsl:stylesheet>
