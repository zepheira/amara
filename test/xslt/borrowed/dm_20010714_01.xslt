<?xml version="1.0"?>
<!--
# Dieter Maurer <dieter@handshake.de> reports problems with xsl:text and 
# pre tag output
-->
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version='1.0'>

  <xsl:output method="html"/>
  
  <xsl:template match="/">
    <html>
    <head><title>Hello</title></head>
    <body><p>
      <pre>
Testing
Testing
123
      </pre>
    </p></body>
    </html>
  </xsl:template>

</xsl:stylesheet>
