<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
version="1.0">

<xsl:template match="/">
<html>
  <head/>
  <body>
  <xsl:apply-templates/>
  </body>
</html>
</xsl:template>

<xsl:template match="p">
<p><xsl:apply-templates/></p>
</xsl:template>

<xsl:template match="programlisting">
  <span style="font-family:monospace">
  <xsl:apply-templates/>
  </span>
</xsl:template>

<xsl:template match="programlisting/text()[contains(.,'&#xA;')]">
  <xsl:call-template name="br-replace">
    <xsl:with-param name="text" select="."/>
  </xsl:call-template>
</xsl:template>

<xsl:template name="br-replace">
  <xsl:param name="text"/>
  <!-- </xsl:text> on next line on purpose to get newline -->
  <xsl:choose>
  <xsl:when test="contains($text, '&#xA;')">
    <xsl:value-of select="substring-before($text, '&#xA;')"/>
    <br/>
    <xsl:call-template name="br-replace">
      <xsl:with-param name="text" select="substring-after($text, '&#xA;')"/>
    </xsl:call-template>
  </xsl:when>
  <xsl:otherwise>
    <xsl:value-of select="$text"/>
  </xsl:otherwise>
 </xsl:choose>
</xsl:template>

</xsl:stylesheet>