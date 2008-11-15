<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:ft="http://xmlns.4suite.org/ext"
  xmlns:ot='http://namespaces.opentechnology.org/talk'
  xmlns:dc='http://purl.org/metadata/dublin_core'
  extension-element-prefixes='ft'
  version="1.0"
>
  <xsl:output method="html" encoding="ISO-8859-1"/>
  <xsl:param name='user-mode' select='"full-story"'/>

  <xsl:template match="/">
  <HTML><HEAD><TITLE>Test Skin</TITLE></HEAD><BODY>
    <ft:apply-templates mode='{$user-mode}'/>
  </BODY></HTML>
  </xsl:template>

  <xsl:template match="ot:story" mode="front-page">

   <DIV ALIGN="CENTER">

    <DIV ALIGN="CENTER">
       <xsl:value-of select="dc:title"/>
    </DIV>

    <TABLE WIDTH="100%" BORDER="0">
      <TR>
        <TD ALIGN="LEFT" WIDTH="33%">
          <xsl:value-of select="dc:creator"/>
        </TD>
        <TD ALIGN="CENTER" WIDTH="33%">
          <xsl:value-of select="dc:datetime"/>
        </TD>
        <TD ALIGN="RIGHT" WIDTH="33%">
          <xsl:value-of select="ot:link"/>
        </TD>
      </TR>
    </TABLE>

    <DIV ALIGN="JUSTIFY">
        <xsl:apply-templates select="dc:description"/>
    </DIV>
   </DIV>

  </xsl:template>

  <xsl:template match="ot:story" mode="full-story">

    <DIV ALIGN="CENTER">
       <xsl:value-of select="dc:title"/>
    </DIV>

    <TABLE WIDTH="100%" BORDER="0">
      <TR>
        <TD ALIGN="LEFT" WIDTH="50%">
          <xsl:value-of select="dc:creator"/>
        </TD>
        <TD ALIGN="RIGHT" WIDTH="50%">
          <xsl:value-of select="dc:datetime"/>
        </TD>
      </TR>
    </TABLE>

    <DIV ALIGN="JUSTIFY">
       <xsl:apply-templates select="dc:content"/>
       <BR/><BR/>
    </DIV>

    <DIV ALIGN="JUSTIFY">
       <xsl:apply-templates select="dc:description"/>
       <BR/><BR/>
    </DIV>

  </xsl:template>

  <xsl:template match="ot:comment">
    <DIV ALIGN="JUSTIFY">
     <xsl:for-each select="dc:title"/>
    </DIV>
  </xsl:template>

</xsl:stylesheet>
