########################################################################
# test/xslt/og_20010507.py
# Oliver Graf <ograf@oli-ver-ena.de>:
# ft:output cdata-section-elements is not used

import os, tempfile
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

from Ft.Lib.Uri import OsPathToUri

FILESTEM = tempfile.mktemp()
FILESTEM_URI = OsPathToUri(FILESTEM)

file_expected_1 = """\
<?xml version="1.0" encoding="ISO-8859-1"?>
<datatree>
  <content>
    <num><![CDATA[1000]]></num>
    <str><![CDATA[test]]></str>
  </content>
  <what>test</what>
</datatree>"""

class test_xslt_cdata_section_elements_og_20010507(xslt_test):
    source = stringsource("""\
<?xml version="1.0" encoding="ISO-8859-1"?>

<test>
  <data>
    <num>1000</num>
    <str>test</str>
  </data>
</test>""")
    transform = stringsource("""\
<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:exsl="http://exslt.org/common"
    extension-element-prefixes="exsl">

<xsl:output method="text" encoding="ISO-8859-1"/>

<xsl:template match="/">
  <xsl:variable name="file" select="'%s'"/>
  <exsl:document href="{$file}" method="xml" indent="yes" encoding="ISO-8859-1"
                 cdata-section-elements="str num">
    <datatree>
      <content><xsl:copy-of select="test/data/*"/></content>
      <what>test</what>
    </datatree>
  </exsl:document>
</xsl:template>

</xsl:stylesheet>"""%(FILESTEM_URI))
    parameters = {}
    expected = """\
"""

    # def test_transform(self):
    #     if os.path.exists(FILESTEM):
    #         os.unlink(FILESTEM)
    #     import sys
    #     from amara.xslt import transform
    #     result = transform(self.source, self.transform, output=io)
    # 
    #     tester.compare(1, os.path.exists(FILESTEM))
    #     fileData = open(FILESTEM,'r').read()
    #     tester.compare(file_expected_1, fileData)
    #     tester.testDone()
    #     if os.path.exists(FILESTEM):
    #         os.unlink(FILESTEM)
    # 
    #     return

if __name__ == '__main__':
    test_main()
