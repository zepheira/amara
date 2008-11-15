<!--
# exact same test as #1, but param values are derived from namespace
# nodes in the stylesheet.
-->
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exslt="http://exslt.org/common"
  xmlns:ora="http://www.oracle.com/XSL/Transform/java/"
  xmlns:u="http://uche.ogbuji.net/tmp/20010717"
  >

  <!-- Just for documentation of which files need it right now -->
  <u:files>
    <u:file>heroic</u:file>
    <u:file>couplets</u:file>
  </u:files>

  <xsl:variable name="this" select="document('')"/>
  <xsl:variable name="exslt-ns" select="$this/*/namespace::exslt"/>
  <xsl:variable name="ora-ns" select="$this/*/namespace::ora"/>

  <xsl:variable name="files" select="$this/*/u:files/u:file"/>

  <xsl:param name="file"/>
  <xsl:param name="from" select="$exslt-ns"/>
  <xsl:param name="to">
    <xsl:choose>
      <xsl:when test="$from=$exslt-ns"><xsl:value-of select="$ora-ns"/></xsl:when>
      <xsl:otherwise><xsl:value-of select="$exslt-ns"/></xsl:otherwise>
    </xsl:choose>
  </xsl:param>

  <xsl:template match="/">
    <xsl:apply-templates mode="convert"/>
    <!--
    <xsl:for-each select="$files">
      <xsl:message>
        Processing: <xsl:value-of select="."/>
      </xsl:message>
      <xsl:apply-templates select="document(.)" mode="convert"/>
    </xsl:for-each>
    -->
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
