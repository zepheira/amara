<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
version="1.0">

<xsl:template match="/">
   <xsl:variable name="NaN" select="number('abc')" />
   String value of NaN: <xsl:value-of select="$NaN" />
   String value of boolean value of NaN: <xsl:value-of select="boolean($NaN)" />
   String value of boolean value of string value of NaN: <xsl:value-of select="boolean(string($NaN))" />
   String value of numerical value of boolean value of NaN: <xsl:value-of select="number(boolean($NaN))" />
   String value of numerical value of boolean value of string value of NaN: <xsl:value-of select="number(boolean(string($NaN)))" />
</xsl:template>

</xsl:stylesheet>