<?xml version='1.0'?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
version="1.0">
  <xsl:output method="html" indent="yes"/>

  <xsl:template match="/">
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template match="TASKS/TASK/COMPONENTS">
    <xsl:variable name="t-size" select="count(COMPONENT)"/>
    <xsl:variable name="half" select="ceiling($t-size div 2)"/>
   
    <TABLE>
      <xsl:for-each select="COMPONENT[position() &lt;= $half]">
      <xsl:variable name="here" select="position()"/>
      <TR>
        <TD><xsl:value-of select="."/></TD>
        <TD>
          <xsl:choose>
            <xsl:when test="../COMPONENT[$here+$half]">
              <xsl:value-of select="../COMPONENT[$here+$half]"/>
            </xsl:when>
            <xsl:otherwise></xsl:otherwise>
          </xsl:choose>
        </TD>
      </TR>
      </xsl:for-each>
    </TABLE>

  </xsl:template>

</xsl:stylesheet>