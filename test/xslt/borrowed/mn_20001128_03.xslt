<xsl:stylesheet xmlns:xsl = "http://www.w3.org/1999/XSL/Transform"
 version =
 "1.0" > 
    <xsl:output method="text"/>

    <xsl:key name="elements" match="*" use="name()"/>
    <xsl:key name="attributes" match="@*"
 use="concat(name(parent::*),':::',name())"/>
    <xsl:key name="allSameAttributes" match="@*" use="name(parent::*)"/>

    <xsl:template match="/">
      <xsl:apply-templates select="//*">
        <xsl:sort select="name()"/>
      </xsl:apply-templates>
    </xsl:template>

    <xsl:template match = "*" >
      <xsl:if test="generate-id() = generate-id(key('elements',name()))">
        <xsl:text>&#xA;</xsl:text>
        <xsl:value-of select="name()"/>
        <xsl:apply-templates select="key('allSameAttributes',name())">
          <xsl:sort select="name()"/>
        </xsl:apply-templates>
      </xsl:if>
    </xsl:template> 

    <xsl:template match="@*">
      <xsl:if test="generate-id() =
 generate-id(key('attributes',concat(name(parent::*),':::',name())))">
        <xsl:text>&#xA;     </xsl:text>
        <xsl:value-of select="name()"/>
        <xsl:text>: </xsl:text>
        <xsl:apply-templates
 select="key('attributes',concat(name(parent::*),':::',name()))"
 mode="values">
          <xsl:sort/>
        </xsl:apply-templates>
      </xsl:if>
    </xsl:template>

    <xsl:template match="@*" mode="values">
      <xsl:variable name="sameValues" 
        select="key('attributes',concat(name(parent::*),':::',name()))[.
 = current()]" />

        <xsl:if test="generate-id() = generate-id($sameValues)">
          <xsl:value-of select="."/>
          <xsl:text>(</xsl:text>
          <xsl:value-of select="count($sameValues)"/>
          <xsl:text>) </xsl:text>
        </xsl:if>

    </xsl:template>

    <xsl:template match="text()"/>
  </xsl:stylesheet>