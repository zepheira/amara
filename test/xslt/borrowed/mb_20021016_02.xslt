<?xml version="1.0" encoding="utf-8"?>
<!--

  Fibonacci Numbers

  if n = 0, f(n) = 0
  if n = 1, f(n) = 1
  otherwise, f(n) = f(n-2) + f(n-1)

  tail-recursive version based on Scheme code by
  Ben Gum and John David Stone, at
  http://www.math.grin.edu/~gum/courses/151/readings/tail-recursion.xhtml
        
-->
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="text" indent="no"/>

  <xsl:param name="n" select="100"/>

  <xsl:template match="/">
    <xsl:value-of select="concat('f(',$n,') = ')"/>
    <xsl:call-template name="fibo">
      <xsl:with-param name="n" select="$n"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="fibo">
    <xsl:param name="n" select="0"/>
    <xsl:call-template name="fibo-guts">
      <xsl:with-param name="current" select="0"/>
      <xsl:with-param name="next" select="1"/>
      <xsl:with-param name="remaining" select="$n"/>
    </xsl:call-template>
  </xsl:template>
    
  <xsl:template name="fibo-guts">
    <xsl:param name="current" select="0"/>
    <xsl:param name="next" select="0"/>
    <xsl:param name="remaining" select="0"/>
    <xsl:choose>
      <xsl:when test="$remaining = 0">
        <xsl:value-of select="$current"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="fibo-guts">
          <xsl:with-param name="current" select="$next"/>
          <xsl:with-param name="next" select="$current + $next"/>
          <xsl:with-param name="remaining" select="$remaining - 1"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>