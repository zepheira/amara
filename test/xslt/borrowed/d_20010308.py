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

class test_xslt_variable_shadowing_d_20010308(xslt_test):
    transform = """\
<?xml version="1.0"?> 

<!-- 
     Thu Mar  8 03:17:39 PST 2001

     This attempts to count the children of the root by
     visiting each one and incrementing a counter.
-->

<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>
  <xsl:output omit-xml-declaration="yes"/>
  <xsl:strip-space elements="*"/>

  <xsl:variable name="node_count" select="0"/>

  <xsl:template match="/">
      <xsl:apply-templates/>
    node_count has value <xsl:copy-of select="$node_count"/>
  </xsl:template>

  <xsl:template match="*">
     <xsl:variable name="node_count" select="1+$node_count"/>
  </xsl:template>
  
</xsl:stylesheet>
"""
    source = stringsource("<a><b/><c/><d/></a>")
    parameters = {}
    expected = """
    node_count has value 0"""

if __name__ == '__main__':
    test_main()
