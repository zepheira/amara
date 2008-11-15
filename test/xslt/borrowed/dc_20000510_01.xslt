<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0"
                >

<xsl:output method="xml" indent="yes"/>


<xsl:template match="add-exp[op-add]" mode="value">
<xsl:variable name="x">
<xsl:apply-templates select="*[1]" mode="value"/>
</xsl:variable>
<xsl:variable name="y">
<xsl:apply-templates select="*[3]" mode="value"/>
</xsl:variable>
<xsl:value-of select="$x + $y"/>
</xsl:template>

<xsl:template match="add-exp[op-sub]" mode="value">
<xsl:variable name="x">
<xsl:apply-templates select="*[1]" mode="value"/>
</xsl:variable>
<xsl:variable name="y">
<xsl:apply-templates select="*[3]" mode="value"/>
</xsl:variable>
<xsl:value-of select="$x - $y"/>
</xsl:template>


<xsl:template match="primary-exp[op-mult]" mode="value">
<xsl:variable name="x">
<xsl:apply-templates select="*[1]" mode="value"/>
</xsl:variable>
<xsl:variable name="y">
<xsl:apply-templates select="*[3]" mode="value"/>
</xsl:variable>
<xsl:value-of select="$x * $y"/>
</xsl:template>


<xsl:template match="literal" mode="value">
<xsl:value-of select="number(@value)"/>
</xsl:template>

<xsl:template match="*" mode="value">
<xsl:apply-templates select="*" mode="value"/>
</xsl:template>

<xsl:template match="*">
<xsl:copy>
<xsl:attribute name="value">
<xsl:apply-templates select="." mode="value"/>
</xsl:attribute>
<xsl:apply-templates/>
</xsl:copy>
</xsl:template>

<xsl:template match="op-add|op-sub|op-mult">
<xsl:copy>
<xsl:apply-templates/>
</xsl:copy>
</xsl:template>


</xsl:stylesheet>
