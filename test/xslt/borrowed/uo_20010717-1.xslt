<!--
#Uche Ogbuji tries out some wickedness with namespace

# essentially just tests xsl:attribute with a namespace URI
# that comes from a top-level param, derived from hard-coded
# top-level variables
-->
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exslt="http://exslt.org/common"
  xmlns:ora="http://www.oracle.com/XSL/Transform/java/"
  >

  <xsl:variable name="exslt-ns" select="'http://exslt.org/common'"/>
  <xsl:variable name="ora-ns" select="'http://www.oracle.com/XSL/Transform/java/'"/>

  <xsl:param name="from" select="$exslt-ns"/>
  <xsl:param name="to">
    <xsl:choose>
      <xsl:when test="$from=$exslt-ns"><xsl:value-of select="$ora-ns"/></xsl:when>
      <xsl:otherwise><xsl:value-of select="$exslt-ns"/></xsl:otherwise>
    </xsl:choose>
  </xsl:param>

  <xsl:template match="/">
    <xsl:apply-templates mode="convert"/>
  </xsl:template>

  <xsl:template match="@*|node()" mode="convert">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()" mode="convert"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="/*" mode="convert" priority="10">
    <xsl:copy>
      <xsl:attribute name="exslt:dummy" namespace="{$to}"/>
      <xsl:apply-templates select="@*|node()" mode="convert"/>
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
