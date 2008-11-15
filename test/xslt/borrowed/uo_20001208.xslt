<!--
#Uche Ogbuji exercises format-number on Brad Marshall's behalf
-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:template match = "/">
    <xsl:value-of select='format-number(10000000000.75 + 10000000000.50, "##.##")'/>
  </xsl:template>

</xsl:stylesheet>
