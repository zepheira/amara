<xsl:transform
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 version="1.0"
>

<xsl:output method='text'/>

<xsl:variable name="pos">
  <xsl:for-each select="//element[descendant::y[.='z']][1]">
    <xsl:number/>
  </xsl:for-each>
</xsl:variable>

<xsl:template match="/">
result: <xsl:value-of select='$pos'/>
</xsl:template>

</xsl:transform>