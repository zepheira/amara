<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:param name="currentLanguage" select="'en'"/>

  <!-- Removed definition for charEncoding variable. -->

  <xsl:output method="html" encoding="utf-8"/>

  <xsl:template match="/">
  <!--
    <xsl:message><xsl:value-of select="$currentLanguage"/></xsl:message>
  -->
    <xsl:apply-templates select="*[lang($currentLanguage) or not(@xml:lang)]"/>
  </xsl:template>

  <xsl:template match="*">
  <!--
    <xsl:message>Processing: <xsl:value-of select="name()"/></xsl:message>
  -->
    <xsl:copy>
      <xsl:for-each select="@*[name() != 'id']">
	<xsl:copy/>
      </xsl:for-each>
      <xsl:apply-templates
	select="*[lang($currentLanguage) or not(@xml:lang)] | text()"/>
    </xsl:copy>
  </xsl:template>
    
</xsl:stylesheet>