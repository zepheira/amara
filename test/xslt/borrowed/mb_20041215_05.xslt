<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exsl="http://exslt.org/common"
  xmlns:f="http://xmlns.4suite.org/ext"
  extension-element-prefixes="f"
  exclude-result-prefixes="exsl">

  <xsl:output method="xml" encoding="us-ascii" indent="yes"/>

  <xsl:key name="foo" match="node()" use="."/>
  <xsl:key name="bar" match="z:*" use="." xmlns:z="planetz"/>

  <xsl:template match="/">
    <xsl:variable name="keys">
      <f:dump-keys force-update="yes"/>
    </xsl:variable>
    <zz:KeyDump xmlns:zz="http://xmlns.4suite.org/reserved">
      <xsl:for-each select="exsl:node-set($keys)//zz:Key">
        <xsl:sort select="@name"/>
        <xsl:copy-of select="."/>
      </xsl:for-each>
    </zz:KeyDump>
  </xsl:template>

</xsl:stylesheet>
