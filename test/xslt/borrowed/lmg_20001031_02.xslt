<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:foo="http://foo.org/xslt/extensions"
                extension-element-prefixes="foo"
                version="1.0">

<xsl:output indent="yes"
    doctype-system="http://www.python.org/topics/xml/dtds/xbel-1.0.dtd"
    doctype-public="+//IDN python.org//DTD XML Bookmark Exchange
    Language 1.0//EN//XML" />

  <xsl:template match = "/">
    <spam/>
  </xsl:template>

</xsl:stylesheet>