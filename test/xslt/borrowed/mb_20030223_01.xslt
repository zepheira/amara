<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="html" indent="yes"/>

  <xsl:key name="skills-by-mark" match="skill" use="@mark"/>
  <xsl:template match="skills">
    <table>
      <!-- process a set consisting of the first skill element for each mark -->
      <xsl:for-each select="skill[count(.|key('skills-by-mark',@mark)[1])=1]">
        <tr>
          <td><b><xsl:value-of select="concat(@mark,' skills:')"/></b></td>
          <td>
            <!-- process all skill elements having the current skill's mark -->
            <xsl:for-each select="key('skills-by-mark',@mark)">
              <xsl:value-of select="@name"/>
              <xsl:if test="position()!=last()"><br/></xsl:if>
            </xsl:for-each>
          </td>
        </tr>
      </xsl:for-each>
    </table>
  </xsl:template>

</xsl:stylesheet>