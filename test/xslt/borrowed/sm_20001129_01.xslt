<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="text"/>
  <!-- Used for distinct allocation categories -->
  <xsl:key name="cat" match="allocCategory" use="."/>
  <!-- Used for distinct asset classes for an alloc category -->
  <xsl:key name="ucls" match="assetClass"   use="concat(.,'::',../allocCategory)"/>
  <!-- Used to find (not-distinct) asset classes for an alloc cat -->
  <xsl:key name="cls" match="assetClass" use="../allocCategory"/>
  <!-- Used to find funds in a (allocCat,assetClass) combination -->
  <xsl:key name="fnd" match="Fund" use="concat(allocCategory,'::',assetClass)"/>
  <xsl:template match="/">
    <xsl:for-each 
      select="/FundList/Fund/allocCategory[generate-id(.)=
                                           generate-id(key('cat',.)[1])]">
      <xsl:variable name="curcat" select="string(.)"/>
      <xsl:value-of select="$curcat"/>
      <xsl:text>&#x0a;</xsl:text>
      <xsl:for-each 
        select="key('cls',$curcat)[generate-id(.)=
                                   generate-id(key('ucls',
                                   concat(.,'::',$curcat))[1])]">
        <xsl:variable name="curclass" select="string(.)"/>
        <xsl:text>  </xsl:text>
        <xsl:value-of select="$curclass"/>
        <xsl:text>&#x0a;</xsl:text>
        <xsl:for-each select="key('fnd',concat($curcat,'::',$curclass))">
          <xsl:text>    </xsl:text>
          <xsl:value-of select="fundName"/>
          <xsl:text>&#x0a;</xsl:text>
        </xsl:for-each>
      </xsl:for-each>
    </xsl:for-each>
  </xsl:template>
</xsl:stylesheet>