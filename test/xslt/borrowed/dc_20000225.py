########################################################################
# test/xslt/dc_20000205.py
#Example from David Carlisle to John Lam on 25 Feb 2000, with 
# well-formedness and XSLT semantics corrections
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_xslt_node_set_dc_20000205(xslt_test):
    source = stringsource("""<x>
<thing><quantity> 1</quantity><price> 2</price></thing>
<thing><quantity> 4</quantity><price> 5</price></thing>
<thing><quantity> 3</quantity><price>10</price></thing>
<thing><quantity> 2</quantity><price> 1</price></thing>
</x>
""")
    transform = stringsource("""<total
  xsl:version="1.0"
  xsl:exclude-result-prefixes="exsl"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exsl="http://exslt.org/common"
>

<xsl:variable name="x">
  <xsl:for-each select="x/thing">
    <a><xsl:value-of select="quantity * price"/></a>
  </xsl:for-each>
</xsl:variable>

<xsl:value-of select="sum(exsl:node-set($x)/*)"/>

</total>
""")
    parameters = {}
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<total>54</total>"""

if __name__ == '__main__':
    test_main()
