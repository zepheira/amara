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
  <xsl:call-template name="br-replace">
    <xsl:with-param name="word" select="."/>
  </xsl:call-template>
  </span>
</xsl:template>

<xsl:template name="br-replace">
  <xsl:param name="word"/>
   <!-- </xsl:text> on next line on purpose to get newline -->
  <xsl:variable name="cr"><xsl:text>
</xsl:text></xsl:variable>
  <xsl:choose>
  <xsl:when test="contains($word,$cr)">
      <xsl:value-of select="substring-before($word,$cr)"/>
      <br/>
      <xsl:call-template name="br-replace">
        <xsl:with-param name="word" select="substring-after($word,$cr)"/>
      </xsl:call-template>
  </xsl:when>
  <xsl:otherwise>
    <xsl:value-of select="$word"/>
  </xsl:otherwise>
 </xsl:choose>
</xsl:template>

</xsl:stylesheet>