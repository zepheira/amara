<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:doc="http://docbook.org/docbook/xml/4.0/namespace"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  version="1.0"
>

  <xsl:import href="docbook_html1.xslt"/>

  <xsl:output method="html" encoding="ISO-8859-1"/>

  <xsl:template name="CSS">
    <STYLE type='text/css'>
      <xsl:comment>        
        body { font-family: sans-serif }
        H1, H2, H3, H4, H5 { font-style: bold; color: #336699 }
        .abstract { font-style: italic; color: maroon }
      </xsl:comment>
    </STYLE>
  </xsl:template>

</xsl:stylesheet>
