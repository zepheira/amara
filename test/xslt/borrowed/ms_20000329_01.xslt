<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/>
  <xsl:template match="Record">
    <TestRecord>
      <xsl:apply-templates/>
    </TestRecord>
  </xsl:template>
  <xsl:template match="Field[@No='606']/Subfield[@No='x']">
    <GotAMatch><xsl:apply-templates/></GotAMatch>
  </xsl:template>
</xsl:stylesheet>