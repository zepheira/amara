<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
version="1.0">

<xsl:template match="list">
    <xsl:apply-templates select="item[@include='yes']"/>
</xsl:template>

<xsl:template match="item">
    *<xsl:value-of select="@a"/>*
    position = <xsl:value-of select="position()"/>
    last = <xsl:value-of select="last()"/>
</xsl:template>

</xsl:stylesheet>