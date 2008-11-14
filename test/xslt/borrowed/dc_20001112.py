########################################################################
# test/xslt/dc_20001112.py
#David Carlisle <davidc@nag.co.uk> plays nifty tricks with xsl:key
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_xslt_xsl_key_dc_20001112(xslt_test):
    source = stringsource("""<x>
  <itemlist>
	<item itemid="Z101" units="1"/>
	<item itemid="Z102" units="2"/>
	<item itemid="Z101" units="4"/>
  </itemlist>

  <itemlist>
	<item itemid="y101" units="1"/>
	<item itemid="y102" units="2"/>
	<item itemid="y102" units="3"/>
	<item itemid="y101" units="4"/>
	<item itemid="y101" units="5"/>
  </itemlist>

</x>""")
    transform = stringsource("""<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0"
                >

<xsl:output method="xml" indent="yes"/>

<xsl:key name="items-by-itemid"
         match="item"
         use="concat(generate-id(..), @itemid)"
/>

<xsl:template match="itemlist">
 <xsl:variable name="x" select="generate-id(.)"/>
  <xsl:for-each select="item[count(. |
                                   key('items-by-itemid',
                                       concat($x, @itemid))[1]) = 1]">

    <xsl:sort select="@itemid" />
    <tr>
      <td><xsl:value-of select="@itemid"/></td>
      <td><xsl:value-of select="sum(key('items-by-itemid',
                                          concat($x, @itemid))/@units)"/></td>
    </tr>
  </xsl:for-each>
</xsl:template>

<xsl:template match='text()'/>

</xsl:stylesheet>""")
    parameters = {}
    expected = """<?xml version="1.0" encoding="UTF-8"?>
<tr>
  <td>Z101</td>
  <td>5</td>
</tr>
<tr>
  <td>Z102</td>
  <td>2</td>
</tr>
<tr>
  <td>y101</td>
  <td>10</td>
</tr>
<tr>
  <td>y102</td>
  <td>5</td>
</tr>"""

if __name__ == '__main__':
    test_main()
