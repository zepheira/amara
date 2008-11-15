<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes" encoding="us-ascii"/>
  <xsl:template match="data">
    <table>
      <xsl:for-each select="current()//file">
      <xsl:sort select="@num" order="ascending" case-order="lower-first" data-type="number"/>
        <tr>
          <th align="left"><xsl:value-of select="@num"/></th>
          <td width="99%"><xsl:value-of select="@name"/></td>
        </tr>
      </xsl:for-each>
    </table>
  </xsl:template>
</xsl:stylesheet>