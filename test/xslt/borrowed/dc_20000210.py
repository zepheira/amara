########################################################################
# test/xslt/dc_20000210.py
#Example from David Carlisle to ??? on 10 Feb 2000, with well-formedness corrections
#With a few added variations for more testing
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_xslt_wff_1_dc_20000210(xslt_test):
    source = stringsource("""<?xml version="1.0"?>
<a>
1 2
3 4
5 6
</a>""")
    transform = stringsource("""<xsl:stylesheet
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 version="1.0"
>

<xsl:template match="/a">
  <foo><xsl:value-of select="translate(.,'&#10; ','')"/></foo>
</xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<foo>123456</foo>"""

class test_xslt_wff_2_dc_20000210(xslt_test):
    source = stringsource("""<?xml version="1.0"?>
<boo:a xmlns:boo="http://banquo.com">
1 2
3 4
5 6
</boo:a>""")
    #Note: this one is tricky.  We have the default namespace in exclude-result
    #So it shouldn't appear, right?  Wrong.  The literal result element output
    #by the template is actually in the http://duncan.com ns by virtue of default
    #So it must be declared as such in the output.
    transform = stringsource("""<xsl:stylesheet
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:boo="http://banquo.com"
 xmlns="http://duncan.com"
 exclude-result-prefixes='#default boo'
 version="1.0"
>

<xsl:template match="/boo:a">
  <foo><xsl:value-of select="translate(.,'&#10; ','')"/></foo>
</xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<foo xmlns='http://duncan.com'>123456</foo>"""

class test_xslt_wff_3_dc_20000210(xslt_test):
    source = stringsource("""<?xml version="1.0"?>
<boo:a xmlns:boo="http://banquo.com">
1 2
3 4
5 6
</boo:a>""")
    transform = stringsource("""<xsl:stylesheet
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:boo="http://banquo.com"
 xmlns="http://duncan.com"
 version="1.0"
>

<xsl:template match="/boo:a">
  <foo><xsl:value-of select="translate(.,'&#10; ','')"/></foo>
</xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<foo xmlns:boo='http://banquo.com' xmlns='http://duncan.com'>123456</foo>"""

if __name__ == '__main__':
    test_main()
