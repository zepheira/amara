<xsl:transform
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 version="1.0"
>
<xsl:template match="/">
    <top>
    <xsl:apply-templates select="/FORMS/CONTAINERS"/>
    </top>
</xsl:template>
<xsl:template match="/FORMS/CONTAINERS"> 
    <xsl:for-each select="CONTAINER"> 

        <xsl:copy-of select="//*[name(.)=current()/PRE_HTML]" /> 
        <xsl:value-of select="TITLE"/>
        <xsl:comment>Do some more things here</xsl:comment>

        <xsl:copy-of select="//*[name(.)=current()/POST_HTML]" /> 

    </xsl:for-each> 
</xsl:template> 
</xsl:transform>