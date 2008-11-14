########################################################################
# test/xslt/dc_20000510.py
#David Carlisle's <> Grammatical Decorator example, 10 May 2000
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_xslt_grammatical_decorator_dc_20000510(xslt_test):
    source = stringsource("""  <exp>
      <add-exp>
        <add-exp>
          <mult-exp>
            <primary-exp>
              <literal value="2"/>
            </primary-exp>
          </mult-exp>
        </add-exp>
        <op-add/>
        <mult-exp>
          <primary-exp>
            <literal value="3"/>
          </primary-exp>
        </mult-exp>
      </add-exp>
    </exp>""")
    transform = stringsource("""<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0"
                >

<xsl:output method="xml" indent="yes"/>


<xsl:template match="add-exp[op-add]" mode="value">
<xsl:variable name="x">
<xsl:apply-templates select="*[1]" mode="value"/>
</xsl:variable>
<xsl:variable name="y">
<xsl:apply-templates select="*[3]" mode="value"/>
</xsl:variable>
<xsl:value-of select="$x + $y"/>
</xsl:template>

<xsl:template match="add-exp[op-sub]" mode="value">
<xsl:variable name="x">
<xsl:apply-templates select="*[1]" mode="value"/>
</xsl:variable>
<xsl:variable name="y">
<xsl:apply-templates select="*[3]" mode="value"/>
</xsl:variable>
<xsl:value-of select="$x - $y"/>
</xsl:template>


<xsl:template match="primary-exp[op-mult]" mode="value">
<xsl:variable name="x">
<xsl:apply-templates select="*[1]" mode="value"/>
</xsl:variable>
<xsl:variable name="y">
<xsl:apply-templates select="*[3]" mode="value"/>
</xsl:variable>
<xsl:value-of select="$x * $y"/>
</xsl:template>


<xsl:template match="literal" mode="value">
<xsl:value-of select="number(@value)"/>
</xsl:template>

<xsl:template match="*" mode="value">
<xsl:apply-templates select="*" mode="value"/>
</xsl:template>

<xsl:template match="*">
<xsl:copy>
<xsl:attribute name="value">
<xsl:apply-templates select="." mode="value"/>
</xsl:attribute>
<xsl:apply-templates/>
</xsl:copy>
</xsl:template>

<xsl:template match="op-add|op-sub|op-mult">
<xsl:copy>
<xsl:apply-templates/>
</xsl:copy>
</xsl:template>


</xsl:stylesheet>
""")
    parameters = {}
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<exp value='5'>
      <add-exp value='5'>
        <add-exp value='2'>
          <mult-exp value='2'>
            <primary-exp value='2'>
              <literal value='2'/>
            </primary-exp>
          </mult-exp>
        </add-exp>
        <op-add/>
        <mult-exp value='3'>
          <primary-exp value='3'>
            <literal value='3'/>
          </primary-exp>
        </mult-exp>
      </add-exp>
    </exp>"""

if __name__ == '__main__':
    test_main()
