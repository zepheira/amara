<?xml version='1.0'?>
<!--
# Uche gets nasty with nested copies and other arcana (too bad we had to ixnay the namespace axis hacking)
# jkloth: 2002-01-22
#   Fixed test to expect null-namespace on unprefixed attributes
-->
<xsl:stylesheet version='1.0'
  xmlns:xsl='http://www.w3.org/1999/XSL/Transform'
  xmlns:es='http://www.snowboard-info.com/EndorsementSearch.wsdl'
  xmlns:esxsd='http://schemas.snowboard-info.com/EndorsementSearch.xsd'
  xmlns:soap='http://schemas.xmlsoap.org/wsdl/soap/'
  xmlns:wsdl='http://schemas.xmlsoap.org/wsdl/'
  xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
>

  <xsl:output method='xml' indent='yes'/>

  <!-- template 1 -->
  <xsl:template match='wsdl:definitions'>
    <xsl:copy>
      <xsl:apply-templates select='@*'/>
      <xsl:apply-templates select='*'/>
      <rdf:RDF>
        <xsl:apply-templates select='*' mode='convert-to-rdf'/>
      </rdf:RDF>
    </xsl:copy>
  </xsl:template>

  <!-- template 2 -->
  <xsl:template match='wsdl:message|wsdl:portType|wsdl:binding|wsdl:service|wsdl:operation|wsdl:port' mode='convert-to-rdf'>
    <xsl:copy>
      <xsl:attribute name='rdf:ID' namespace='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
        <xsl:value-of select='@name'/>
      </xsl:attribute>
      <xsl:apply-templates select='@*' mode='convert-to-rdf'/>
      <xsl:apply-templates select='*'/>
      <xsl:apply-templates select='*' mode='convert-to-rdf'/>
    </xsl:copy>
  </xsl:template>

  <!-- template 3 -->
  <xsl:template match='wsdl:part' mode='convert-to-rdf'>
    <xsl:copy>
      <xsl:apply-templates select='@*' mode='convert-to-rdf'/>
      <xsl:apply-templates select='*'/>
      <xsl:apply-templates select='*' mode='convert-to-rdf'/>
    </xsl:copy>
  </xsl:template>

  <!-- template 4 -->
  <xsl:template match='wsdl:message|wsdl:portType|wsdl:binding|wsdl:service|wsdl:operation|wsdl:port|wsdl:part'/>

  <!-- template 5 -->
  <xsl:template match='@*' mode='convert-to-rdf'>
    <xsl:attribute name="{concat('wsdl', ':', name())}"
                   namespace='{namespace-uri()}'>
      <xsl:value-of select='.'/>
    </xsl:attribute>
  </xsl:template>

  <!-- template 6 -->
  <xsl:template match='*' mode='convert-to-rdf'/>

  <!-- template 7 -->
  <xsl:template match='*|@*'>
    <xsl:copy>
      <xsl:apply-templates select='@*|node()'/>
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
