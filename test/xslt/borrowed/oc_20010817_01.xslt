<?xml version="1.0" encoding="ISO-8859-1"?>

<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:output method="html"
            version="4.0" 
            encoding="ISO-8859-1" 
            indent="yes" 
            doctype-public="-//W3C//DTD HTML 4.0//EN"/>

<xsl:template match="/">
  <html>
    <head/>
    <body>
      <p>&#160;</p>
      <p> &#160;</p>
      <p>&#160; </p>
      <p> &#160;*</p>
      <p>*&#160; </p>
      <p>*&#160;*</p>
      <p>*</p>
      <table width="100%" border="1">
       <tr>
        <td bgcolor="blue">&#160;</td>
        <td bgcolor="blue"> &#160;</td>
        <td bgcolor="blue">&#160; </td>
        <td bgcolor="blue"> &#160;*</td>
        <td bgcolor="blue">*&#160; </td>
        <td bgcolor="blue">*&#160;*</td>
        <td bgcolor="blue">*</td>
       </tr>
      </table>
    </body>
  </html>
</xsl:template>
</xsl:stylesheet>
