<?xml version="1.0" encoding="ISO-8859-1"?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:import href="resources/pool-comm.xsl"/>

  <xsl:output method="html" 
              version="4.0" 
              encoding="ISO-8859-1" 
              indent="yes" 
              doctype-public="-//W3C//DTD HTML 4.0//EN"/>

  <xsl:template match="/">
<html>
 <head>
  <title>Cars Pool Management</title>
  <meta http-equiv="content-type" content="text/html"/>
 </head>

 <body bgcolor="#FFFFFF">
  <h1>Cars Pool Management</h1>
  <table border="1" cellpadding="3">
   <tr>
    <td>State</td>
    <td>Brand</td>
    <td>Type</td>
    <td>Registration Number</td>
   </tr>

    <xsl:apply-templates select="pool/car"/>

  </table>
 </body>
</html>
  </xsl:template>

  <xsl:template match="car">
<tr>
 <td>
    <xsl:call-template name="state-value"/>
 </td>
 <td>
    <xsl:value-of select="brand"/>
 </td>
 <td>
    <xsl:value-of select="type"/>
 </td>
 <td>
    <xsl:value-of select="number"/>
 </td>
</tr>
  </xsl:template>

</xsl:stylesheet>
