########################################################################
# test/xslt/st_20000324.py
# Steve Tinney's conformance test, 24 Mar 2000

import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

from Ft.Lib import Uri
uri = Uri.OsPathToUri(os.path.abspath(__file__))

class test_xslt_baseuri_conformance_st_20000324(xslt_test):
    source = stringsource("""<dummy/>""")
    transform = stringsource("""<?xml version='1.0'?>
<xsl:stylesheet version="1.0" 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text"/>

<xsl:variable name="textnode">Text node</xsl:variable>

<xsl:template match="/">
  <xsl:for-each select="document('')/*/xsl:variable">
    <xsl:text>child::text() = </xsl:text>
      <xsl:choose><xsl:when test="child::text()">true</xsl:when>
                  <xsl:otherwise>false</xsl:otherwise></xsl:choose>
    <xsl:text>&#xa;</xsl:text>
  </xsl:for-each>
  <xsl:for-each select="document('')/*/xsl:variable/text()">
    <xsl:text>self::text() = </xsl:text>
      <xsl:choose><xsl:when test="self::text()">true</xsl:when>
                  <xsl:otherwise>false</xsl:otherwise></xsl:choose>
    <xsl:text>&#xa;</xsl:text>
  </xsl:for-each>
</xsl:template>

</xsl:stylesheet>""", uri = uri)
    parameters = {}
    expected = """child::text() = true
self::text() = true
"""

if __name__ == '__main__':
    test_main()
