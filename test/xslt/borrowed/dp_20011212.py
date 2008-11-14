########################################################################
# test/xslt/dp_20011212.py
#Dave's Pawson's exsl:node-set problems
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_xslt_rtf_root_nodes_dp_20011212(xslt_test):
    source = stringsource('<h4 id="bajw_000e"><a href="bajw000E.smil#bajw_000e">Helen Sismore.</a></h4>')
    transform = stringsource("""\
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exslt="http://exslt.org/common"
  exclude-result-prefixes="exslt"
  version="1.0"
>

<xsl:template match="/">
  <xsl:variable name="smilFiles">
    <xsl:for-each select="//*[contains(@href,'smil')]">
     <xsl:copy-of select="."/>
    </xsl:for-each>
  </xsl:variable>
  <xsl:message><xsl:copy-of select="exslt:node-set($smilFiles)"/></xsl:message>

  <xsl:for-each select="exslt:node-set($smilFiles)/a">
    <ref title="{.}" src="{substring-before(@href,'#')}" id="{substring-before(@href,'.')}"/>
    </xsl:for-each>
</xsl:template>

</xsl:stylesheet>
""")
    parameters = {}
    expected = """\
<?xml version='1.0' encoding='UTF-8'?>\n<ref title='Helen Sismore.' id='bajw000E' src='bajw000E.smil'/>"""

    
if __name__ == '__main__':
    test_main()
