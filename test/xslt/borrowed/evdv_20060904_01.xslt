<?xml version='1.0' encoding='UTF-8'?>
<xsl:transform
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:dyn="http://exslt.org/dynamic"
  exclude-result-prefixes="dyn"
  version="1.0"
>

  <xsl:template match="Invoice">
    <result>
      <xsl:value-of select="sum(dyn:map(InvoiceRow/RowAmount, 'string(.)'))"/>
    </result>
  </xsl:template>

</xsl:transform>
