<?xml version="1.0"?>
<xsl:stylesheet id="imported" version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  >

  <xsl:template match="doc">
    <xsl:param name="border-style" select="'solid'"/>
    <div style="border: {$border-style} red">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="example">
    <pre><xsl:apply-templates/></pre>
  </xsl:template>

  <xsl:template match="*">
    <element-incognito><xsl:value-of select="name()"/></element-incognito>
  </xsl:template>

</xsl:stylesheet>
