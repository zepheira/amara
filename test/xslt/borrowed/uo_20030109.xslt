<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:ns="http://stuff.foo"
  exclude-result-prefixes="ns"
  >

  <xsl:import href="uo_20030109-1.xsl"/>

  <xsl:template match="/">
    <result><xsl:value-of select="ns:toUpperCase('Hello World')"/></result>
  </xsl:template>

</xsl:stylesheet>
