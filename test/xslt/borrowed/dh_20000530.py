########################################################################
# test/xslt/dh_20000530.py
# XT Bug Report from David Hunter <david.hunter@mobileQ.COM> on 30 May 
# 2000, with additional checks
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

commonsource = stringsource("""<nodes>
  <node>a</node>
  <node>b</node>
  <node>c</node>
</nodes>""")

class test_xslt_1_dh_20000530(xslt_test):
    source = commonsource
    transform = stringsource("""<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text"/>

<xsl:template match="/nodes/node[last()]">
  <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="text()"/>
</xsl:stylesheet>""")
    parameters = {}
    expected ="""c"""

class test_xslt_2_dh_20000530(xslt_test):
    source = commonsource
    transform = stringsource("""<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text"/>

<xsl:template match="/nodes/node[1]">
  <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="/nodes/node[2]">
  <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="/nodes/node[3]">
  <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="text()"/>
</xsl:stylesheet>""")
    parameters = {}
    expected = """abc"""

class test_xslt_node_text_dh_20000530(xslt_test):
    source = commonsource
    transform = stringsource("""<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text"/>

<xsl:template match="/nodes/node[last()]">
  <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="text()"/>

<xsl:template match="/nodes/*" priority="-10">
<xsl:text>Hello</xsl:text>
</xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = """HelloHelloc"""

if __name__ == '__main__':
    test_main()
