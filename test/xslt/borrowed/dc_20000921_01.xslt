<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:xsd="http://www.w3.org/1999/XMLSchema"
>

<xsl:strip-space elements="*"/>

<xsl:output method="text" />

<xsl:template match="xsd:element">
  <xsl:text>&#10;Schema Element</xsl:text>
  <xsl:text>&#10;  name: </xsl:text>
  <xsl:value-of select="@name"/>
  <xsl:text>&#10;  type: </xsl:text>

  <xsl:variable name="p">
    <xsl:if test="contains(@type, ':')">
      <xsl:value-of select="substring-before(@type, ':')"/>
    </xsl:if>
  </xsl:variable>

  <xsl:variable name="n">
    <xsl:choose>
      <xsl:when test="contains(@type, ':')">
        <xsl:value-of  select="substring-after(@type, ':')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of  select="@type"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:variable name="ns" select="namespace::*[name()=$p]"/>

  <xsl:text>{</xsl:text>
  <xsl:value-of select="$ns"/>
  <xsl:text>} </xsl:text>
  <xsl:value-of select="$n"/>

  <xsl:text>&#10;  Elements with the same type are:&#10;</xsl:text>

  <xsl:for-each select="//xsd:element">
    <xsl:variable name="p2">
      <xsl:if test="contains(@type, ':')">
        <xsl:value-of select="substring-before(@type, ':')"/>
      </xsl:if>
    </xsl:variable>

    <xsl:variable name="n2">
      <xsl:choose>
        <xsl:when test="contains(@type, ':')">
          <xsl:value-of select="substring-after(@type, ':')"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="@type"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>

    <xsl:variable name="ns2" select="namespace::*[name()=$p2]"/>

    <xsl:if test="$n=$n2 and $ns=$ns2">
      <xsl:text>    </xsl:text>
      <xsl:value-of select="@name"/>
      <xsl:text>&#10;</xsl:text>
    </xsl:if>
  </xsl:for-each>

</xsl:template>

</xsl:stylesheet>