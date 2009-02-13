<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:y="http://spam.com/y">

  <xsl:key name='k1' match='y:*' use='@id'/>

</xsl:stylesheet>
