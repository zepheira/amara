<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>

  <xsl:key name='k1' match='xsl:*' use='name()'/>
  <xsl:key name='k2' match='x:*' use='@id'/>

</xsl:stylesheet>
