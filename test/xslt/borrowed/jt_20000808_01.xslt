<xsl:stylesheet
xmlns:xsl='http://www.w3.org/1999/XSL/Transform' version="1.0">

<xsl:output method="text"/>

<xsl:template match="items">
  <xsl:for-each select="item">
    <xsl:sort
      select="concat(
              substring(concat('Mac', substring-after(., 'Re Mc'), ', Re'),
                        1 div starts-with(., 'Re Mc')),
              substring(concat(substring-after(., 'Re '), ', Re'),
                        1 div (starts-with(., 'Re ') and
                        not(starts-with(., 'Re Mc')))),
              substring(concat('Mac', substring-after(., 'Mc')),
                        1 div (not(starts-with(., 'Re ')) and
                        starts-with(., 'Mc'))),
              substring(.,
                        1 div not(starts-with(.,'Mc') or
                        starts-with(., 'Re '))))" />
    <xsl:copy-of select="." />
  </xsl:for-each>
</xsl:template>

</xsl:stylesheet>