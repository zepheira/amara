<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match="/doc">
    <output>
      <xsl:apply-templates
        select="a[@b = '1' and @b!=preceding-sibling::a/@b]"/>
    </output>
  </xsl:template>
  <xsl:template match="a">
    <got-one>!</got-one>
  </xsl:template>
</xsl:stylesheet>