<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:param name="currentLanguage" select="'en'"/>

  <xsl:output method="html" encoding="utf-8"/>

  <xsl:template match="*">
    <xsl:choose>
      <xsl:when test="@xml:lang">
        <!-- Don't shift context -->
        <xsl:apply-templates select="." mode="select-lang"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:copy>
          <xsl:for-each select="@*[name() != 'id']">
            <xsl:copy/>
          </xsl:for-each>
          <xsl:apply-templates/>
        </xsl:copy>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="*" mode="select-lang">
    <xsl:if test="lang($currentLanguage)">
      <xsl:copy>
        <xsl:for-each select="@*[name() != 'id']">
          <xsl:copy/>
        </xsl:for-each>
        <xsl:apply-templates mode="select-lang"/>
      </xsl:copy>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>