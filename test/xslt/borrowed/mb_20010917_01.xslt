<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
version="1.0">
  <xsl:output method="xml" indent="yes"/>
  <xsl:template match="/">

    <xsl:variable name="set1" select="/foo/set1/*"/>
    <xsl:variable name="set2" select="/foo/set2/*"/>
    <xsl:variable name="set3" select="/foo/set3/*"/>

    <result>

      <r><xsl:value-of select="concat('set1 = set1: ',$set1=$set1)"/></r>
      <r><xsl:value-of select="concat('set2 = set2: ',$set2=$set2)"/></r>
      <r><xsl:value-of select="concat('set3 = set3: ',$set3=$set3)"/></r>
      <r><xsl:value-of select="concat('set1 = set2: ',$set1=$set2)"/></r>
      <r><xsl:value-of select="concat('set1 = set3: ',$set1=$set3)"/></r>
      <r><xsl:value-of select="concat('set2 = set3: ',$set2=$set3)"/></r>
      <r><xsl:value-of select="concat('set1 != set1: ',$set1 != $set1)"/></r>
      <r><xsl:value-of select="concat('set2 != set2: ',$set2 != $set2)"/></r>
      <r><xsl:value-of select="concat('set3 != set3: ',$set3 != $set3)"/></r>
      <r><xsl:value-of select="concat('set1 != set2: ',$set1 != $set2)"/></r>
      <r><xsl:value-of select="concat('set1 != set3: ',$set1 != $set3)"/></r>
      <r><xsl:value-of select="concat('set2 != set3: ',$set2 != $set3)"/></r>
      <r><xsl:value-of select="concat('not(set1 = set1): ',not($set1 = $set1))"/></r>
      <r><xsl:value-of select="concat('not(set2 = set2): ',not($set2 = $set2))"/></r>
      <r><xsl:value-of select="concat('not(set3 = set3): ',not($set3 = $set3))"/></r>
      <r><xsl:value-of select="concat('not(set1 = set2): ',not($set1 = $set2))"/></r>
      <r><xsl:value-of select="concat('not(set1 = set3): ',not($set1 = $set3))"/></r>
      <r><xsl:value-of select="concat('not(set2 = set3): ',not($set2 = $set3))"/></r>

    </result>

  </xsl:template>
</xsl:stylesheet>