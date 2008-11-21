########################################################################
# test/xslt/dm_20010506.py
# Dieter Maurer <dieter@handshake.de> reports problems with xsl:import 
# and variables
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource, XsltError

raise Exception, "FAIL, incomplete port, specific errors not tested"

commonsource = stringsource("""<ignored/>""")

class test_xslt_import_with_variables_dm_20010506(xslt_test):
    source = commonsource
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version='1.0'>

  <xsl:import href="dm_20010506.xslt"/>

  <xsl:variable name="section.autolabel" select="1" />
  <xsl:variable name="html.stylesheet">book.xsl</xsl:variable>
  <xsl:variable name="html.stylesheet.type">text/css</xsl:variable>
    
</xsl:stylesheet>""")
    parameters = {}
    expected = """\
<html>\n    START\n    <link type='text/css' rel='stylesheet' href='book.xsl'>\n    END\n    </html>"""

class test_xslt_import_with_params_dm_20010506(xslt_test):
    source = commonsource
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version='1.0'>

  <xsl:import href="dm_20010506.xslt"/>

  <xsl:param name="section.autolabel" select="1" />
  <xsl:param name="html.stylesheet">book.xsl</xsl:param>
  <xsl:param name="html.stylesheet.type">text/css</xsl:param>

</xsl:stylesheet>""")

class test_xslt_include_with_variables_dm_20010506(xslt_error):
    error_code = XsltError.DUPLICATE_TOP_LEVEL_VAR
    source = commonsource
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version='1.0'>

  <xsl:include href="dm_20010506.xslt"/>

  <xsl:variable name="section.autolabel" select="1" />
  <xsl:variable name="html.stylesheet">book.xsl</xsl:variable>
  <xsl:variable name="html.stylesheet.type">text/css</xsl:variable>

</xsl:stylesheet>""")
    parameters = {}
    expected = ""

class test_xslt_include_with_params_dm_20010506(xslt_error):
    error_code = XsltError.DUPLICATE_TOP_LEVEL_VAR
    source = commonsource
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version='1.0'>

  <xsl:include href="dm_20010506.xslt"/>

  <xsl:param name="section.autolabel" select="1" />
  <xsl:param name="html.stylesheet">book.xsl</xsl:param>
  <xsl:param name="html.stylesheet.type">text/css</xsl:param>

</xsl:stylesheet>""")
    parameters = {}
    expected= ""

if __name__ == '__main__':
    test_main()
