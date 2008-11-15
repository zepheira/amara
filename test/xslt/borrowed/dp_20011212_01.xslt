<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exslt="http://exslt.org/common"
  exclude-result-prefixes="exslt"
  version="1.0"
>

<xsl:template match="/">
  <xsl:variable name="smilFiles">
    <xsl:for-each select="//*[contains(@href,'smil')]">
     <xsl:copy-of select="."/>
    </xsl:for-each>
  </xsl:variable>
  <xsl:message><xsl:copy-of select="exslt:node-set($smilFiles)"/></xsl:message>

  <xsl:for-each select="exslt:node-set($smilFiles)/a">
    <ref title="{.}" src="{substring-before(@href,'#')}" id="{substring-before(@href,'.')}"/>
    </xsl:for-each>
</xsl:template>

</xsl:stylesheet>
