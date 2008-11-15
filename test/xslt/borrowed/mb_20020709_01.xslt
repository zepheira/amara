<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:output method="xml" indent="no"/>

<xsl:template match="/">
<result xmlns:new="urn:added-by-stylesheet">
<xsl:text>&#10;</xsl:text>
<r>total nodes: <xsl:value-of select="count(//node()
|//node()/namespace::node())"/></r>
<xsl:text>&#10;</xsl:text>
<r>copy:&#10;<xsl:copy-of select="."/></r>
</result>
</xsl:template>

</xsl:stylesheet>
