########################################################################
# test/xslt/og_20010503.py
# Oliver Graf <ograf@oli-ver-ena.de> has indentation probs with 
# ft:write-file

import os, tempfile
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

from Ft.Lib.Uri import OsPathToUri

BASENAME = tempfile.mktemp()
BASENAME_URI = OsPathToUri(BASENAME)

file_expected = """<?xml version="1.0" encoding="ISO-8859-1"?>
<datatree>
  <name>%s</name>
  <what>test</what>
</datatree>"""


class test_xslt_ft_write_file_og_20010503(xslt_test):
    source = stringsource("""\
<?xml version="1.0" encoding="ISO-8859-1"?>

<test>
  <data>11</data>
  <data>12</data>
  <data>13</data>
  <data>14</data>
  <data>15</data>
</test>
""")
    transform = stringsource("""\
<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:exsl="http://exslt.org/common"
    extension-element-prefixes="exsl">

<xsl:output method="text" encoding="ISO-8859-1"/>

<xsl:template match="/">
  <xsl:apply-templates select="test/data"/>
</xsl:template>

<xsl:template match="data">
  <xsl:variable name="file" select="concat('%s',.,'.xml')"/>
  <exsl:document href="{$file}" method="xml" indent="yes" encoding="ISO-8859-1">
    <datatree>
      <name><xsl:value-of select="."/></name>
      <what>test</what>
    </datatree>
  </exsl:document>
</xsl:template>

</xsl:stylesheet>""" % BASENAME_URI)
    parameters = {}
    expected = ""

    # def test_transform(self):
    #     import sys
    #     from amara.xslt import transform
    #     result = transform(self.source, self.transform, output=io)
    #     
    #     for num in range(11,16):
    #         file = '%s%d.xml' % (BASENAME, num)
    #         if os.path.exists(file):
    #             actual = open(file).read()
    #             os.unlink(file)
    #             self.assert_(treecompare.html_compare(file_expected % num, actual))
    #         else:
    #             tester.error("ft:write-file %d.xml doesn't exist" % num)
    # 
    #     return

if __name__ == '__main__':
    test_main()

