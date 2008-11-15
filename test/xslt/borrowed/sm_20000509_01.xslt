<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output indent="yes"/>
  <xsl:key name="xxx" match="/Tasks/Task/Owner" use="."/>
  <xsl:template match="/">
  <Tasks>
    <xsl:for-each select="/Tasks/Task/Owner[generate-id(.)=generate-id(key('xxx',.))]">
      <xsl:sort select="."/>
      <Owner name="{.}">
        <xsl:for-each select="key('xxx',.)/..">
          <xsl:copy-of select="."/>
        </xsl:for-each>
      </Owner>
    </xsl:for-each>
  </Tasks>
  </xsl:template>
</xsl:stylesheet>
