<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:myns="http://stuff.foo"
  xmlns:func="http://exslt.org/functions"
  extension-element-prefixes="func"
  exclude-result-prefixes="myns">

  <func:function name="myns:toUpperCase">
    <xsl:param name="stringToConvert"/>
    <func:result select="translate($stringToConvert,
                         'abcdefghijklmnopqrstuvwxyz',
                         'ABCDEFGHIJKLMNOPQRSTUVWXYZ')"/>
  </func:function>

</xsl:stylesheet>
