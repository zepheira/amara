<?xml version="1.0" encoding="utf-8"?>
<!--
Behavior of node copy to result tree
-->
<xsl:transform
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:b1="urn:bogus-1"
>

  <xsl:output method="xml" encoding="iso-8859-1" indent="yes"
    doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"
    doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN"/>

  <xsl:template match="/">
    <html xmlns="http://www.w3.org/1999/xhtml" lang="en-US" xml:lang="en-US">
      <xsl:apply-templates/>
    </html>
  </xsl:template>

  <xsl:template match="b1:elem">
    <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
      <rdf:Description ID="spam"/>
    </rdf:RDF>
  </xsl:template>

</xsl:transform>
