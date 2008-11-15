<?xml version="1.0" encoding="ISO-8859-1"?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:template name="state-value">
    <xsl:choose>
      <xsl:when test="@state=1">
        <b>Free</b>
      </xsl:when>
      <xsl:when test="@state=2">
        Used
      </xsl:when>
      <xsl:when test="@state=3">
        <i>Getting repaired</i>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
