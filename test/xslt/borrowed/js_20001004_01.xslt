<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
version="1.0">
    <xsl:template match='p[@class="normal"]'>
       <p><xsl:apply-templates/></p>
    </xsl:template>
    <xsl:template match='p[@class="indent"]'>
       <blockquote><p><xsl:apply-templates/></p></blockquote>
    </xsl:template>
    <xsl:template match="*|@*" priority="-1">
        <xsl:copy>
            <xsl:apply-templates select="@*|*|text()"/>
        </xsl:copy>
    </xsl:template>
</xsl:stylesheet>