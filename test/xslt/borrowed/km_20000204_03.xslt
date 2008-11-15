<?xml version="1.0" standalone="yes"?> 
<xsl:stylesheet
      xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
      version="1.0">
<xsl:output method="text"/>

<xsl:template match="element">
  <xsl:if test=".//y"> 
    <xsl:variable name="yvalue"><xsl:value-of select=".//y"/></xsl:variable>
     <xsl:if test="$yvalue = 'z'">
       <xsl:number count="element" format="1." level="any"/>
     </xsl:if>
  </xsl:if>
</xsl:template>
</xsl:stylesheet>
