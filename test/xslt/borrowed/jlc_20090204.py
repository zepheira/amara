########################################################################
# test/xslt/borrowed/jlc_20090204.py
# John L. Clark: http://lists.fourthought.com/pipermail/4suite-dev/2009-February/002272.html

from amara.test.xslt.xslt_support import _run_xml

def test_jlc_20090204():
    source = """<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:test="tag:jlc6@po.cwru.edu,2009-02-04:testNS"
    version="1.0">
  <test:foo>bar</test:foo>

  <xsl:template match="*">
    <xsl:copy>
      <xsl:for-each select="*"/>
      <xsl:if test="current()[test:foo = 'bar']">current</xsl:if>
    </xsl:copy>
  </xsl:template>
</xsl:stylesheet>"""
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:test="tag:jlc6@po.cwru.edu,2009-02-04:testNS"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">current</xsl:stylesheet>"""

    _run_xml(
        source_xml = source,
        transform_xml = source,
        expected = expected)

if __name__ == '__main__':
    raise SystemExit("Use nosetests")
