<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:myns="http://my.netscape.com/rdf/simple/0.9/"
exclude-result-prefixes="myns"
>

<xsl:template match="/">
  <xsl:copy>
    <rss>
      <xsl:apply-templates select="//myns:channel"/>
    </rss>
  </xsl:copy>
</xsl:template>

<xsl:template match="myns:channel">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
    <xsl:apply-templates select="//myns:image"/>
    <xsl:apply-templates select="//myns:item"/>
  </xsl:copy>
</xsl:template>

<xsl:template match="myns:channel/myns:title">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

<xsl:template match="myns:channel/myns:link">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

<xsl:template match="myns:channel/myns:description">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

<xsl:template match="//myns:image">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

<xsl:template match="myns:image/myns:title">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

<xsl:template match="myns:image/myns:url">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

<xsl:template match="myns:image/myns:link">
<xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

<xsl:template match="myns:item">
 <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

<xsl:template match="myns:item/myns:title">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

<xsl:template match="myns:item/myns:link">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

</xsl:stylesheet>
