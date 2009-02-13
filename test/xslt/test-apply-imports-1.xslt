<?xml version="1.0"?>
<xsl:stylesheet id="imported" version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  >

  <xsl:template match="example">
    <pre><xsl:apply-templates/></pre>
  </xsl:template>

  <xsl:template match="example" mode="foo">
    <span>imported</span>
  </xsl:template>

</xsl:stylesheet>
