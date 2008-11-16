<!--
#Exercise some uniquification/grouping tricks
-->
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version="1.0"
>

  <xsl:key name='k' match='datum' use='.'/>

  <xsl:template match="data">
    <data>
      <xsl:copy-of select='datum[generate-id(.)=generate-id(key("k",.)[1])]'/>
    </data>
  </xsl:template>

</xsl:stylesheet>
