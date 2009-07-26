<!-- John L. Clark: http://lists.fourthought.com/pipermail/4suite-dev/2009-February/002272.html -->
<xsl:stylesheet
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
</xsl:stylesheet>
