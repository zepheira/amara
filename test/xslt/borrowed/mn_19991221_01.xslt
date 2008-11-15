<xsl:transform
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 version="1.0"
>

<xsl:template match="text()">
<xsl:value-of select="translate(.,'{}','&lt;&gt;')"/>
</xsl:template>

<xsl:template match="/">
<xhtml><body>
<xsl:apply-templates/>
</body></xhtml>
</xsl:template>

<xsl:template match="description|doc">
<xsl:apply-templates/>
</xsl:template>

<xsl:template match="*">
<xsl:element name="{name()}"/>
<xsl:apply-templates/>
</xsl:template>

<xsl:template match="error">
<SPAN class="error"><xsl:apply-templates/></SPAN>
</xsl:template>
</xsl:transform>