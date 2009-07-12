########################################################################
# test/xslt/test_text.py

from xslt_support import _run_html

def test_text_1():
    """<xsl:text> with disable-output-escaping='yes'"""
    _run_html(
        source_xml = """<noescape>dummy</noescape>""",
        transform_xml = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="html"/>

  <xsl:template match="/">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="noescape">
    <html><p><xsl:text disable-output-escaping='yes'>&amp;nbsp;</xsl:text></p></html>
  </xsl:template>

</xsl:stylesheet>
""",
        expected ="""<html>
  <p>&nbsp;</p>
</html>""")

if __name__ == '__main__':
    raise SystemExit("Use nosetests")
