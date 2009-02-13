########################################################################
# test/xslt/test_text.py
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_text_1(xslt_test):
    """<xsl:text> with disable-output-escaping='yes'"""
    source = stringsource("""<noescape>dummy</noescape>""")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="html"/>

  <xsl:template match="/">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="noescape">
    <html><p><xsl:text disable-output-escaping='yes'>&amp;nbsp;</xsl:text></p></html>
  </xsl:template>

</xsl:stylesheet>
""")
    expected ="""<html>
  <p>&nbsp;</p>
</html>"""


if __name__ == '__main__':
    test_main()
