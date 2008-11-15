<?xml version="1.0" encoding="iso-8859-1"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exslt="http://exslt.org/common"
>
  <xsl:output method="text"/>
  <xsl:variable name="tree">
    <x id="0">foo</x>
    <x id="1">foo<y/>bar</x>
    <x id="2">
      <y>hello world</y>
    </x>
    <x id="3">      <y/>
    </x>
    <x id="4">
      <y>
        <z>hrrmmmm</z>
      </y>
    </x>
  </xsl:variable>
  <xsl:variable name="all-non-empty-x" select="exslt:node-set($tree)/*[string()]"/>

  <xsl:template match="/">
    <xsl:for-each select="$all-non-empty-x">
      <xsl:text>current element: '</xsl:text>
      <xsl:value-of select="name()"/>
      <xsl:text>' with id '</xsl:text>
      <xsl:value-of select="@id"/>
      <xsl:text>'&#10;</xsl:text>
      <xsl:text>string-value: '</xsl:text>
      <xsl:value-of select="."/>
      <xsl:text>'&#10;--------------------&#10;</xsl:text>
    </xsl:for-each>
  </xsl:template>
</xsl:stylesheet>