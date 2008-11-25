<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:f="http://xmlns.4suite.org/ext"
  extension-element-prefixes="f">

  <xsl:output method="xml" encoding="us-ascii" indent="yes"/>

  <xsl:key name="foo" match="*" use="."/>

  <xsl:template match="/">
    <f:dump-keys force-update="yes"/>
  </xsl:template>

</xsl:stylesheet>
