
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0"
                xmlns:one="http://one"
                xmlns:two="http://two"
                >

<xsl:output method="xml" indent="yes"/>

<xsl:template match="one:doc">
<two:html>
<two:head>
  <two:title><xsl:value-of select="one:head"/></two:title>
</two:head>
<two:body>
  <two:h1><xsl:value-of select="one:head"/></two:h1>
<xsl:apply-templates select="one:section"/>
</two:body>
</two:html>
</xsl:template>

<xsl:template match="one:section">
  <two:h2><xsl:value-of select="one:head"/></two:h2>
<xsl:apply-templates select="*[not(self::one:head)]"/>
</xsl:template>

<xsl:template match="one:p">
  <two:p><xsl:apply-templates/></two:p>
</xsl:template>

</xsl:stylesheet>