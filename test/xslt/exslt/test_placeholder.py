# -*- encoding: utf-8 -*-
########################################################################
# test/xslt/test_placeholder.py
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource


class test_borrowed_cases(xslt_test):
    #Bug report by Robert Świętochowski
    #http://lists.fourthought.com/pipermail/4suite/2006-September/008025.html
    source = stringsource("<doc><a>2005-05-04T23:00:00+02:00</a><b>2005-05-05T01:00:00+02:00</b></doc>")
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:date="http://exslt.org/dates-and-times"
  >

  <xsl:template match="/">
    <result><xsl:value-of select="date:difference(a,b)"/>|<xsl:value-of select="date:difference(b,a)"/></result>
  </xsl:template>

</xsl:stylesheet>
""")
    expected = stringsource("<result>A|-A</result>")

    def test_transform_output(self):
        from amara.xslt import transform
        io = cStringIO.StringIO()
        result = transform(self.source, self.transform, output=io)
        self.assert_(treecompare.xml_compare(self.expected, io.getvalue()))
        return

if __name__ == '__main__':
    test_main()
