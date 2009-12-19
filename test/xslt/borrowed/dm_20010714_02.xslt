<?xml version="1.0"?>
<!--
# Dieter Maurer <dieter@handshake.de> reports problems with xsl:text and 
# pre tag output
-->
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version='1.0'>

  <xsl:output method="html"/>
  <xsl:strip-space elements="*"/>
  
  <xsl:template match="/">
    <html><xsl:apply-templates/></html>
  </xsl:template>

  <xsl:template match="cmdsynopsis/command[1]">
    <xsl:call-template name="inline.monoseq"/>
    <xsl:text> </xsl:text>
  </xsl:template>

  <xsl:template name="inline.monoseq">
    <tt>if</tt>
  </xsl:template>

</xsl:stylesheet>
