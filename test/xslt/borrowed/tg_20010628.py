########################################################################
# test/xslt/tg_20010628.py
# Thomas Guettler <guettli@thomas-guettler.de> wants to use XInclude in 
# his stylesheets

import os

from amara.test.xslt.xslt_support import _run_html

from amara.lib import iri
INCLUDE_URI = iri.os_path_to_uri(os.path.join(os.path.dirname(__file__),
                                              "resources", "tg_20010628-include.xml"))

def test_xslt_xinclude_tg_20010628():
    _run_html(
        source_xml = """\
<?xml version="1.0" encoding="iso-8859-1"?>
<html xmlns:xinclude="http://www.w3.org/2001/XInclude">
<head>
<title>MyTitle</title>
</head>
<body>
<xinclude:include href="%(uri)s"/>
</body>
</html>""" % {'uri' : INCLUDE_URI},
        transform_xml = """\
<?xml version="1.0" encoding="iso-8859-1"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xinclude="http://www.w3.org/2001/XInclude">

<xsl:output method="html" indent="yes" encoding="iso-8859-1"/>

<!-- copy source nodes to result nodes -->
<xsl:template match="@*|node()">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

<xsl:template match="body">
  <body bgcolor='#ffbf00'>
    <xsl:apply-templates/>
    <xinclude:include href="%(uri)s"/> 
  </body>
</xsl:template>

</xsl:stylesheet>
""" % {'uri' : INCLUDE_URI},
        expected = """\
<html xmlns:xinclude="http://www.w3.org/2001/XInclude">
  <head>
    <meta http-equiv='Content-Type' content='text/html; charset=iso-8859-1'>
    <title>MyTitle</title>
  </head>
  <body bgcolor='#ffbf00'>
  <p xml:base="%(base)s">
 some text
</p>
    <p xml:base="%(base)s">
 some text
</p>
  </body>
</html>""" % {'base' : INCLUDE_URI},
        )
if __name__ == '__main__':
    raise SystemExit("Use nosetests")
