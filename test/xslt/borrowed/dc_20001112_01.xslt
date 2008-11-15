<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0"
                >

<xsl:output method="xml" indent="yes"/>

<xsl:key name="items-by-itemid"
         match="item"
         use="concat(generate-id(..), @itemid)"
/>

<xsl:template match="itemlist">
 <xsl:variable name="x" select="generate-id(.)"/>
  <xsl:for-each select="item[count(. |
                                   key('items-by-itemid',
                                       concat($x, @itemid))[1]) = 1]">

    <xsl:sort select="@itemid" />
    <tr>
      <td><xsl:value-of select="@itemid"/></td>
      <td><xsl:value-of select="sum(key('items-by-itemid',
                                          concat($x, @itemid))/@units)"/></td>
    </tr>
  </xsl:for-each>
</xsl:template>

<xsl:template match='text()'/>

</xsl:stylesheet>