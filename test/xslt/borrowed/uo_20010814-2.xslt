<!--
#Exercise some uniquification/grouping tricks
-->
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version="1.0"
>

  <xsl:key name='k' match='datum' use='.'/>

  <xsl:template match="data">
    <xsl:variable name="unique" select='datum[generate-id(.)=generate-id(key("k",.)[1])]'/>
    <data>
      <xsl:apply-templates select="$unique"/>
    </data>
  </xsl:template>

  <xsl:template match="datum">
    <xsl:copy>
      <xsl:value-of select="."/>
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
