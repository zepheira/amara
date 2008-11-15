<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
version="1.0">
  <xsl:output method="xml" indent="yes"/>
  <xsl:template match="/">

    <xsl:variable name="set1" select="/foo/set1"/>
    <xsl:variable name="set2" select="/foo/set2"/>
    <xsl:variable name="set3" select="/foo/set3"/>

    <result>

      <r><xsl:copy-of select="$set1/x[not(. = $set2/y)]"/></r>
      <r><xsl:copy-of select="$set1/x[not(. = $set3/z)]"/></r>
      <r><xsl:copy-of select="$set2/y[not(. = $set1/x)]"/></r>
      <r><xsl:copy-of select="$set2/y[not(. = $set3/z)]"/></r>
      <r><xsl:copy-of select="$set3/z[not(. = $set1/x)]"/></r>
      <r><xsl:copy-of select="$set3/z[not(. = $set2/y)]"/></r>

    </result>

  </xsl:template>
</xsl:stylesheet>