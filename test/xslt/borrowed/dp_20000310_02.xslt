<?xml version='1.0'?>

<xsl:stylesheet 
   version="1.0" 
   xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
   xmlns:ns-test="http://ns1.com"
   xmlns:ns1="http://ns1.com"
   xmlns:ns2="http://ns2.com"
   xmlns:long-namespace="http://ns3.com"
   exclude-result-prefixes="ns1 ns2 long-namespace"
>

<xsl:output method="xml" indent="yes"/>

<xsl:template match="*">
  <tag>Namespace:<xsl:choose><xsl:when test="namespace-uri(.)"><xsl:value-of select="namespace-uri(.)"/>
    </xsl:when>
    <xsl:otherwise> Null namespace</xsl:otherwise>
  </xsl:choose>

  <!-- namespaces are unordered, sort is needed for comparision only -->
    <xsl:for-each select="namespace::*">
      <xsl:sort select="name()"/>
      NS name: <xsl:value-of select="name(.)"/>
      NS value : <xsl:value-of select="."/>
    </xsl:for-each>

  </tag>
  <xsl:if test="./*"><xsl:apply-templates/></xsl:if>
</xsl:template>

</xsl:stylesheet>
