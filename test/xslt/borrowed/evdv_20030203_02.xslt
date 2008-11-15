<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="foo">
    <res>
      <xsl:apply-templates select="@*"/>
    </res>
  </xsl:template>

  <xsl:template match="@bar[. = 'xxx']">
    <ok>
      <xsl:copy-of select="."/>
    </ok>
  </xsl:template>

</xsl:stylesheet>
