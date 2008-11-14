########################################################################
# test/xslt/dc_19991210.py
#Example from David Carlisle to Mark Anderson on 10 Dec 1999
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_xslt_head_select_dc_19991210(xslt_test):
    source = stringsource("""
<doc xmlns="http://one">
<head>test</head>
<section>
<head>one</head>
<p>this paragraph
this paragraph</p>
<p>another paragraph
another paragraph</p>
</section>
</doc>""")
    transform = stringsource("""
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0"
                xmlns:one="http://one"
                xmlns:two="http://two"
                >

<xsl:output method="xml" indent="yes"/>

<xsl:template match="one:doc">
<two:html>
<two:head>
  <two:title><xsl:value-of select="one:head"/></two:title>
</two:head>
<two:body>
  <two:h1><xsl:value-of select="one:head"/></two:h1>
<xsl:apply-templates select="one:section"/>
</two:body>
</two:html>
</xsl:template>

<xsl:template match="one:section">
  <two:h2><xsl:value-of select="one:head"/></two:h2>
<xsl:apply-templates select="*[not(self::one:head)]"/>
</xsl:template>

<xsl:template match="one:p">
  <two:p><xsl:apply-templates/></two:p>
</xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected="""<?xml version='1.0' encoding='UTF-8'?>
<two:html xmlns:one='http://one' xmlns:two='http://two'>
  <two:head>
    <two:title>test</two:title>
  </two:head>
  <two:body>
    <two:h1>test</two:h1>
    <two:h2>one</two:h2>
    <two:p>this paragraph
this paragraph</two:p>
    <two:p>another paragraph
another paragraph</two:p>
  </two:body>
</two:html>"""

if __name__ == '__main__':
    test_main()
