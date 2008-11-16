<?xml version="1.0" encoding="UTF-8"?>
<!--
Behavior of node copy to result tree
-->
<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:func="http://exslt.org/functions"
    xmlns:str="http://exslt.org/strings"
    xmlns:js="http://muttmansion.com"
    extension-element-prefixes="func">
    
  <xsl:output method="text" />

  <func:function name="js:escape">
    <xsl:param name="text"/>
    <func:result select='str:replace($text, "&apos;", "\&apos;")'/>
  </func:function>

  <xsl:template match="/">
var g_books = [
<xsl:apply-templates/>
];
  </xsl:template>

  <xsl:template match="book">
<xsl:if test="position() > 1">,</xsl:if> {
id: <xsl:value-of select="@id" />,
name: '<xsl:value-of select="js:escape(title)"/>',
first: '<xsl:value-of select="js:escape(author/first)"/>',
last: '<xsl:value-of select="js:escape(author/last)"/>',
publisher: '<xsl:value-of select="js:escape(publisher)"/>'
}
  </xsl:template>

</xsl:transform>
