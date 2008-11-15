<total
  xsl:version="1.0"
  xsl:exclude-result-prefixes="exsl"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exsl="http://exslt.org/common"
>

<xsl:variable name="x">
  <xsl:for-each select="x/thing">
    <a><xsl:value-of select="quantity * price"/></a>
  </xsl:for-each>
</xsl:variable>

<xsl:value-of select="sum(exsl:node-set($x)/*)"/>

</total>
