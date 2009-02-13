<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:x="http://spam.com"
>

  <xsl:variable name="sty-doc" select="document('')"/>
  <xsl:key name='k1' match='ENTRY' use='@ID'/>
  <xsl:key name='k2' match='x:*' use='@id'/>

  <x:grail id="ein"/>
  <x:grail id="zwo"/>
  <x:knicht id="drei"/>
  <x:knicht id="vier"/>

</xsl:stylesheet>
