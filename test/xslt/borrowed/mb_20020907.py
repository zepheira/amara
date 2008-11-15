########################################################################
# test/xslt/mb_20020907.py
# See 
# http://lists.fourthought.com/pipermail/4suite-dev/2002-September/000732.html

import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

from Ft.Lib import Uri
INC_PATH = Uri.OsPathToUri('test/xslt/borrowed/etc/', attemptAbsolute=1)

commonsource = stringsource()

commonexpected = '<?xml version="1.0" encoding="UTF-8"?>\n'

class test_xslt_vars_1_mb_20020907(xslt_test):
    source = commonsource
    transform = stringsource("""<?xml version="1.0" encoding="utf-8"?>
<xsl:transform version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href="mb_20020907.xsl"/>

  <xsl:variable name="var1" select="'foo'"/>
  <xsl:variable name="var2" select="'bar'"/>
  <xsl:variable name="culprit" select="concat($var1,$var2)"/>

  <xsl:template match="/"/>

</xsl:transform>
""")
    parameters = {}
    expected = commonexpected

    def test_transform(self):
        from amara.xslt import transform
        # stylesheetAltUris=[INC_PATH],
        io = cStringIO.StringIO()
        result = transform(self.source, self.transform, output=io)
        self.assert_(treecompare.html_compare(self.expected, io.getvalue()))
        return

class test_xslt_vars_2_mb_20020907(xslt_test):
    source = commonsource
    transform = stringsource("""<?xml version="1.0" encoding="utf-8"?>
<xsl:transform version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:variable name="var1" select="'foo'"/>
  <xsl:variable name="var2" select="'bar'"/>
  <xsl:variable name="culprit" select="concat($var1,$var2)"/>

  <xsl:template match="/"/>

</xsl:transform>
""")
    parameters = {}
    expected = commonexpected

    def test_transform(self):
        from amara.xslt import transform
        # stylesheetAltUris=[INC_PATH],
        io = cStringIO.StringIO()
        result = transform(self.source, self.transform, output=io)
        self.assert_(treecompare.html_compare(self.expected, io.getvalue()))
        return

if __name__ == '__main__':
    test_main()

