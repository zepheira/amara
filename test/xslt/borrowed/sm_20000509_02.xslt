<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <!-- Slower.xsl -->
  <xsl:output indent="yes"/>
  <xsl:template match="/">
  <Tasks>
    <xsl:for-each
        select="/Tasks/Task[not(preceding-sibling::Task/Owner=./Owner)]/Owner">
      <xsl:sort select="."/>
      <xsl:variable name="owner" select="."/>
      <Owner name="{.}">
        <xsl:for-each select="/Tasks/Task[Owner = $owner ]">
          <xsl:copy-of select="."/>
        </xsl:for-each>
      </Owner>
    </xsl:for-each>
  </Tasks>
  </xsl:template>
</xsl:stylesheet>