<!--
#Uche Ogbuji tries a substitute reader

# jkloth 2002-09-26:
#   Removed unused substitute reader code as this is now done through
#   InputSources and is tested in other locations (not to mention the code
#   was *really* out of date)
-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:output method='text'/>

  <xsl:template match = "/">
    <xsl:value-of select='name(/*)'/>
    <xsl:text>&#10;</xsl:text>
    <xsl:value-of select='name(document("resources/4Suite.xsa")/*)'/>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>

</xsl:stylesheet>
