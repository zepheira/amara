########################################################################
# test/xslt/borrowed/jlc_20090204.py
# John L. Clark: http://lists.fourthought.com/pipermail/4suite-dev/2009-February/002272.html

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_jlc_20090204(xslt_test):
    source = transform = stringsource("""<xsl:stylesheet
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
</xsl:stylesheet>""")
    #source = stringsource("<doc/>")
    parameters = {}
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:test="tag:jlc6@po.cwru.edu,2009-02-04:testNS"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">current</xsl:stylesheet>"""

if __name__ == '__main__':
    test_main()
