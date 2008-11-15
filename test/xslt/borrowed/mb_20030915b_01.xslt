<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="no"/>
  <xsl:template match="/">
    <b>
      <xsl:copy-of select="*"/>
    </b>
  </xsl:template>
</xsl:stylesheet>