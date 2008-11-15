<?xml version="1.0" encoding='iso-8859-1'?>
<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  >

<xsl:output indent="yes" encoding="iso-8859-1" method="text"/>

<xsl:template name="next">
    <xsl:param name="pos"/>
    <xsl:param name="hpos"/>
    <xsl:apply-templates select="/descendant-or-self::*[position()=($pos+1)]">
        <xsl:with-param name="pos" select="$pos+1"/>
        <xsl:with-param name="hpos" select="$hpos"/>
    </xsl:apply-templates>
</xsl:template>

<xsl:template name="spaces">
    <xsl:param name="number"/>
    <xsl:value-of select="' '"/>
    <xsl:if test="$number &gt; 1">
        <xsl:call-template name="spaces">
            <xsl:with-param name="number" select="$number - 1"/>
        </xsl:call-template>
    </xsl:if>
</xsl:template>

<xsl:template name="line-break">
    <xsl:param name="pos"/>
    <xsl:param name="word"/>
    <xsl:param name="depth"/>
    <xsl:value-of select="'&#10;'"/>
    <xsl:if test="$depth &gt; 0">
        <xsl:call-template name="spaces">
            <xsl:with-param name="number" select="$depth"/>
        </xsl:call-template>
    </xsl:if>
    <xsl:choose>
        <xsl:when test="$word!=''">
            <xsl:value-of select="concat($word, ' ')"/>
            <xsl:call-template name="next">
                <xsl:with-param name="pos" select="$pos"/>
                <xsl:with-param name="hpos" select="$depth + string-length($word)+1"/>
            </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
            <xsl:call-template name="next">
                <xsl:with-param name="pos" select="$pos"/>
                <xsl:with-param name="hpos" select="$depth"/>
            </xsl:call-template>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="*">
    <xsl:param name="pos" select="1"/>
    <xsl:param name="hpos" select="1"/>
    <xsl:param name="depth" select="sum(ancestor-or-self::b/@ident)"/>
    <xsl:choose>
        <xsl:when test="@cr=1">
            <xsl:call-template name="line-break">
                <xsl:with-param name="pos" select="$pos"/>
                <xsl:with-param name="depth" select="$depth"/>
            </xsl:call-template>
        </xsl:when>
        <xsl:when test="@value!=''">
            <xsl:choose>
                <xsl:when test="($depth + $hpos + string-length(@value) +1) &lt; 75">
                    <xsl:value-of select="concat(@value, ' ')"/>
                    <xsl:call-template name="next">
                        <xsl:with-param name="pos" select="$pos"/>
                        <xsl:with-param name="hpos" select="$hpos + string-length(@value)+1"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="line-break">
                        <xsl:with-param name="pos" select="$pos"/>
                        <xsl:with-param name="depth" select="$depth"/>
                        <xsl:with-param name="word" select="@value"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:when>
        <xsl:otherwise>
            <xsl:call-template name="next">
                <xsl:with-param name="pos" select="$pos"/>
                <xsl:with-param name="hpos" select="$hpos"/>
            </xsl:call-template>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>


</xsl:stylesheet>