########################################################################
# test/xslt/mb_20021016.py
# Just some general recursion stress tests:
# 1. Ackermann's Function
# 2. Fibonacci Numbers

import os
import sys
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

from Ft import MAX_PYTHON_RECURSION_DEPTH
sys.setrecursionlimit(MAX_PYTHON_RECURSION_DEPTH)

class test_xslt_call_template_ed_20010101(xslt_test):
    source = stringsource("""<dummy/>""")
    transform = stringsource("""<?xml version="1.0" encoding="utf-8"?>
<!--

  Ackermann's function
  http://pweb.netcom.com/~hjsmith/Ackerman/AckeWhat.html

  1. If x = 0 then  A(x, y) = y + 1
  2. If y = 0 then  A(x, y) = A(x-1, 1)
  3. Otherwise,     A(x, y) = A(x-1, A(x, y-1))

  A(3,4) = 125
  A(3,5) = 253
  A(3,6) = 509; template called 172233 times, nested up to 511 calls deep
  A(3,7) will call the template 693964 times (good luck)

-->
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="text" indent="no"/>

  <xsl:param name="x" select="3"/>
  <xsl:param name="y" select="6"/>

  <xsl:template match="/">
    <xsl:value-of select="concat('A(',$x,',',$y,') = ')"/>
    <xsl:variable name="c" select="0"/>
    <xsl:call-template name="A">
      <xsl:with-param name="x" select="$x"/>
      <xsl:with-param name="y" select="$y"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="A">
    <xsl:param name="x" select="0"/>
    <xsl:param name="y" select="0"/>
    <xsl:choose>
      <xsl:when test="$x = 0">
        <xsl:value-of select="$y + 1"/>
      </xsl:when>
      <xsl:when test="$y = 0">
        <xsl:call-template name="A">
          <xsl:with-param name="x" select="$x - 1"/>
          <xsl:with-param name="y" select="1"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="A">
          <xsl:with-param name="x" select="$x - 1"/>
          <xsl:with-param name="y">
            <xsl:call-template name="A">
              <xsl:with-param name="x" select="$x"/>
              <xsl:with-param name="y" select="$y - 1"/>
            </xsl:call-template>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>""")
    parameters = {'x': 3, 'y': 4}
    expected = """A(3,4) = 125"""

if __name__ == '__main__':
    test_main()


