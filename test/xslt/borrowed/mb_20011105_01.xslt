<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

  <xsl:output method="xml" indent="no"/>

  <xsl:template match="/">
    <rootnode stringvalue="{.}"/>
  </xsl:template>

</xsl:stylesheet>