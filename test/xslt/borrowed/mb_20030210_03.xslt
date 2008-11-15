<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="html" indent="yes"/>

  <xsl:template match="/">
    <html>
      <body>
        <h1>indented html</h1>
        <p>html indented 1&#10;html indented 2&#10;html indented 3</p>
        <div class="screen">
          <pre>html not indented 1&#10;html not indented 2<span xmlns="http://foo/bar"><i><b>xml span, i, b, this text, br, p.i., not indented</b></i><br/><xsl:processing-instruction name="foo">bar</xsl:processing-instruction></span><p>still xml, no indenting here either</p>
            <span xmlns="">html not indented 3<br/><p>html still not indented</p>&#10;html on new line but still not indented</span>
          </pre>
          <p>html indented<span xmlns="http://foo/bar"><i><b>xml indented<pre xmlns="">html not indented 1&#10;and 2</pre> back to xml indented</b></i></span>html indented again&#10;and again</p>
        </div>
      </body>
    </html>
  </xsl:template>

</xsl:stylesheet>