<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">
    <xsl:output indent="yes"/>

    <xsl:template match="/">
        <root>
            <xsl:apply-templates>
                <xsl:with-param name="param">List</xsl:with-param>
            </xsl:apply-templates>
        </root>
    </xsl:template>

    <xsl:template match="chapter">
      <xsl:param name="param">Unset</xsl:param>
      <chap>
        <xsl:attribute name="title"><xsl:value-of
select="@name"/></xsl:attribute>
        <xsl:attribute name="cat"><xsl:value-of
select="$param"/></xsl:attribute>
      </chap>
    </xsl:template>

    <xsl:template match="text()" />
</xsl:stylesheet>