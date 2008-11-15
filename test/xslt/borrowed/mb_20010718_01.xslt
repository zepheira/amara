<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exslt="http://exslt.org/common"
  exclude-result-prefixes="exslt">

  <xsl:output method="xml" indent="yes"/>

  <!--
    This template processes the root node of an arbitrary source tree
  -->
  <xsl:template match="/">

    <!-- a result tree fragment containing a root node and an element -->
    <xsl:variable name="myTree">
      <myElement/>
    </xsl:variable>

    <!--
      The output should be a myResult element that contains the result
      of processing the nodes in the $myTree fragment.
    -->
    <myResult>
      <xsl:apply-templates select="exslt:node-set($myTree)" mode="foo">
        <xsl:with-param name="myParameter" select="'hello world'"/>
      </xsl:apply-templates>
    </myResult>

  </xsl:template>

  <!-- This template processes the root node of the fragment -->
  <xsl:template match="/" mode="foo">
    <xsl:param name="myParameter"/>
    <note>
      <xsl:text>Processing the root node of the fragment. </xsl:text>
      <xsl:value-of select="$myParameter"/>
    </note>
    <xsl:apply-templates mode="foo"/> <!-- note we do not pass the parameter -->
  </xsl:template>

  <!-- This template processes the 'myElement' node of the fragment -->  
  <xsl:template match="myElement" mode="foo">
    <xsl:param name="myParameter"/>
    <note>
      <xsl:text>Processing the 'myElement' node of the fragment. </xsl:text>
      <xsl:value-of select="$myParameter"/>
    </note>
    <note>
      <xsl:text>This element has </xsl:text>
      <xsl:value-of select="count(ancestor::node())"/>
      <xsl:text> ancestor(s).</xsl:text>
    </note>
  </xsl:template>

</xsl:stylesheet>