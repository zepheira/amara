########################################################################
# test/xslt/dm_20010714.py
# Dieter Maurer <dieter@handshake.de> reports problems with xsl:text and 
# pre tag output
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_xslt_xsl_text_in_html_mode_dm_20010714(xslt_test):
    source = stringsource("""\
<cmdsynopsis sepchar=" ">
  <command>if</command>
  <arg choice="plain" rep="norepeat">true_body</arg>
  <text> ... </text>
</cmdsynopsis>""")
    transform = stringsource("""\
<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version='1.0'>

  <xsl:output method="html"/>
  <xsl:strip-space elements="*"/>
  
  <xsl:template match="/">
    <html><xsl:apply-templates/></html>
  </xsl:template>

  <xsl:template match="cmdsynopsis/command[1]">
    <xsl:call-template name="inline.monoseq"/>
    <xsl:text> </xsl:text>
  </xsl:template>

  <xsl:template name="inline.monoseq">
    <tt>if</tt>
  </xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = """\
<html><tt>if</tt> true_body ... </html>"""

class test_xslt_xsl_text_in_xml_mode_dm_20010714(xslt_test):
    source = stringsource("""\
<cmdsynopsis sepchar=" ">
  <command>if</command>
  <arg choice="plain" rep="norepeat">true_body</arg>
  <text> ... </text>
</cmdsynopsis>""")
    transform = stringsource("""\
<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version='1.0'>

  <xsl:output method="xml"/>
  <xsl:strip-space elements="*"/>
  
  <xsl:template match="/">
    <html><xsl:apply-templates/></html>
  </xsl:template>

  <xsl:template match="cmdsynopsis/command[1]">
    <xsl:call-template name="inline.monoseq"/>
    <xsl:text> </xsl:text>
  </xsl:template>

  <xsl:template name="inline.monoseq">
    <tt>if</tt>
  </xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = """\
<?xml version='1.0' encoding='UTF-8'?>
<html><tt>if</tt> true_body ... </html>"""

class test_xslt_problems_with_PRE_tags_dm_20010714(xslt_test):
    source = stringsource("<dummy/>")
    transform = stringsource("""\
<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version='1.0'>

  <xsl:output method="html"/>
  
  <xsl:template match="/">
    <html>
    <head><title>Hello</title></head>
    <body><p>
      <pre>
Testing
Testing
123
      </pre>
    </p></body>
    </html>
  </xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = """\
<html>
  <head>
    <meta http-equiv='Content-Type' content='text/html; charset=iso-8859-1'>
    <title>Hello</title>
  </head>
  <body>
    <p>
      <pre>\nTesting\nTesting\n123\n      </pre>
    </p>
  </body>
</html>"""

if __name__ == '__main__':
    test_main()
