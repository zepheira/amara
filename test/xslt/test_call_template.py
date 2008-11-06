########################################################################
# test/xslt/test_call_template.py
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_call_template_1(xslt_test):
    """`xsl:call-template"""
    source = stringsource("""<?xml version="1.0"?>
<data>
 <item>b</item>
 <item>a</item>
 <item>d</item>
 <item>c</item>
</data>
""")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
<xsl:template match="/">
<root>
  <xsl:apply-templates/>
</root>
</xsl:template>

<xsl:template name="do-the-rest">
  <xsl:param name="start"/>
  <xsl:param name="count"/>
  <tr>
  <xsl:for-each select="item[position()&gt;=$start and position()&lt;$start+$count]">
    <td>
    <xsl:value-of select="."/>
    </td>
  </xsl:for-each>
  </tr>
  <xsl:if test="$start + $count - 1 &lt; count(child::item)">
  <xsl:call-template name="do-the-rest">
    <xsl:with-param name="start" select="$start + $count"/>
    <xsl:with-param name="count" select="$count"/>
  </xsl:call-template>
  </xsl:if>  
</xsl:template>

<xsl:template match="data">
  <xsl:call-template name="do-the-rest">
    <xsl:with-param name="start" select="1"/>
    <xsl:with-param name="count" select="2"/>
  </xsl:call-template>
</xsl:template>
</xsl:stylesheet>
""")
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<root><tr><td>b</td><td>a</td></tr><tr><td>d</td><td>c</td></tr></root>"""


if __name__ == '__main__':
    test_main()
