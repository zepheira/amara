# -*- encoding: utf-8 -*-
########################################################################
# test/xslt/d_20010308.py

# From original 4Suite cvs:
# Dan (hitt@charybdis.zembu.com) reports non-conformance with XSLT w.r.t. variable shadowing

import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_apply_import1(xslt_test):
    transform = stringsource("""\
<xsl:transform version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>

<xsl:import href="cs_20070210-1.xslt"/>

<xsl:template match="/">
  <xsl:apply-templates mode="foo"/>
</xsl:template>

<xsl:template match="example" mode="foo">
  <div>
    <span>b</span>
    <xsl:apply-imports/>
  </div>
</xsl:template>

</xsl:transform>""")
    source = stringsource("<example><spam/></example>")
    parameters = {}
    expected = """<div><span>b</span><span>a</span></div>"""

if __name__ == '__main__':
    test_main()

