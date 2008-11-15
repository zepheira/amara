
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    <xsl:template match='top'>
        <top><xsl:apply-templates/></top>
    </xsl:template>
    <xsl:template match='prev'>
        <prev val='{@val}'/>
    </xsl:template>
    <xsl:template match='target'>
        <output>
            <xsl:copy-of select='preceding-sibling::*[1]'/>
        </output>
    </xsl:template>
</xsl:stylesheet>
