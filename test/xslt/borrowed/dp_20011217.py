########################################################################
# test/xslt/dp_20011217.py
#Dave's Pawson's identity transform problem
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

source_1 = stringsource("""<elem xmlns="http:default.com" xmlns:foo="http://foo.com">
  <foo:child/>
</elem>""")

transform_1 = stringsource("""<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version="1.0"
>
<!-- identity transforms. -->
<xsl:template match="*">
  <xsl:element name="{name(.)}" namespace="http://www.w3.org/1999/xhtml">
    <xsl:apply-templates select="@*" />
    <xsl:apply-templates />
    </xsl:element>
</xsl:template>


<xsl:template match="@*">
  <xsl:copy-of select="." />
</xsl:template>
</xsl:stylesheet>""")

transform_2 = stringsource("""<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:foo="http://foo.com"
  version="1.0"
>
<!-- identity transforms. -->
<xsl:template match="*">
  <xsl:element name="{name(.)}" xmlns="http://www.w3.org/1999/xhtml">
    <xsl:apply-templates select="@*" />
    <xsl:apply-templates />
    </xsl:element>
</xsl:template>
<xsl:template match="@*">
  <xsl:copy-of select="." />
</xsl:template>
</xsl:stylesheet>""")

source_2 = stringsource("""<html>
    <head>
        <title>The TCS Review 2000/2001 - Working Together</title>
        <meta name="NCC:Format" content="Daisy 2.0"/>
        <meta name="NCC:Publisher" content="RNIB"/>
        <meta name="NCC:Identifier" content="UK:RNIB:6DCA50D0-E4E2-4472-A2DA-"/>
        <meta name="NCC:Charset" content="ISO-8859-1"/>
        <meta name="dc:title" content="The TCS Review 2000/2001 - Working Together"/>
        <meta name="dc:format" content="Daisy 2.0"/>
        <meta name="dc:creator" content="David Gordon - RNIB"/>
        <meta name="dc:subject" content="Factual"/>
        <meta name="ncc:narrator" content="mixed voices"/>
        <meta name="ncc:generator" content="LpStudioGen 1.5"/>
        <meta name="ncc:tocitems" content="70"/>
        <meta name="ncc:page-front" content="0"/>
        <meta name="ncc:page-normal" content="0"/>
        <meta name="ncc:page-special" content="0"/>
        <meta name="ncc:totaltime" content="01:23:19"/>
    </head>
</html>""")

class test_xslt_id_transform_1_dp_20011217(xslt_test):
    source = source_1
    transform = transform_1
    params = {}
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<elem xmlns='http://www.w3.org/1999/xhtml'>
  <foo:child xmlns:foo='http://www.w3.org/1999/xhtml'/>
</elem>"""

class test_xslt_id_transform_2_dp_20011217(xslt_test):
    source = source_1
    transform = transform_2
    params = {}
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<elem xmlns='http://www.w3.org/1999/xhtml'>
  <foo:child xmlns:foo='http://foo.com'/>
</elem>"""

class test_xslt_id_transform_3_dp_20011217(xslt_test):
    source = source_2
    transform = transform_1
    params = {}
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<html xmlns='http://www.w3.org/1999/xhtml'>
    <head>
        <title>The TCS Review 2000/2001 - Working Together</title>
        <meta name='NCC:Format' content='Daisy 2.0'/>
        <meta name='NCC:Publisher' content='RNIB'/>
        <meta name='NCC:Identifier' content='UK:RNIB:6DCA50D0-E4E2-4472-A2DA-'/>
        <meta name='NCC:Charset' content='ISO-8859-1'/>
        <meta name='dc:title' content='The TCS Review 2000/2001 - Working Together'/>
        <meta name='dc:format' content='Daisy 2.0'/>
        <meta name='dc:creator' content='David Gordon - RNIB'/>
        <meta name='dc:subject' content='Factual'/>
        <meta name='ncc:narrator' content='mixed voices'/>
        <meta name='ncc:generator' content='LpStudioGen 1.5'/>
        <meta name='ncc:tocitems' content='70'/>
        <meta name='ncc:page-front' content='0'/>
        <meta name='ncc:page-normal' content='0'/>
        <meta name='ncc:page-special' content='0'/>
        <meta name='ncc:totaltime' content='01:23:19'/>
    </head>
</html>"""

class test_xslt_id_transform_4_dp_20011217(xslt_test):
    source = source_2
    transform = transform_2
    params = {}
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<html xmlns='http://www.w3.org/1999/xhtml'>
    <head>
        <title>The TCS Review 2000/2001 - Working Together</title>
        <meta name='NCC:Format' content='Daisy 2.0'/>
        <meta name='NCC:Publisher' content='RNIB'/>
        <meta name='NCC:Identifier' content='UK:RNIB:6DCA50D0-E4E2-4472-A2DA-'/>
        <meta name='NCC:Charset' content='ISO-8859-1'/>
        <meta name='dc:title' content='The TCS Review 2000/2001 - Working Together'/>
        <meta name='dc:format' content='Daisy 2.0'/>
        <meta name='dc:creator' content='David Gordon - RNIB'/>
        <meta name='dc:subject' content='Factual'/>
        <meta name='ncc:narrator' content='mixed voices'/>
        <meta name='ncc:generator' content='LpStudioGen 1.5'/>
        <meta name='ncc:tocitems' content='70'/>
        <meta name='ncc:page-front' content='0'/>
        <meta name='ncc:page-normal' content='0'/>
        <meta name='ncc:page-special' content='0'/>
        <meta name='ncc:totaltime' content='01:23:19'/>
    </head>
</html>"""

if __name__ == '__main__':
    test_main()
