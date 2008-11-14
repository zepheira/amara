########################################################################
# test/xslt/dn_20020325.py
# Examples from the article "Two-stage recursive algorithms in XSLT"
# By Dimitre Novatchev and Slawomir Tyszko
# http://www.topxml.com/xsl/articles/recurse/
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

BOOKS = """   <book>
      <title>Angela's Ashes</title>
      <author>Frank McCourt</author>
      <publisher>HarperCollins</publisher>
      <isbn>0 00 649840 X</isbn>
      <price>6.99</price>
      <sales>235</sales>
   </book>
   <book>
      <title>Sword of Honour</title>
      <author>Evelyn Waugh</author>
      <publisher>Penguin Books</publisher>
      <isbn>0 14 018967 X</isbn>
      <price>12.99</price>
      <sales>12</sales>
   </book>"""

BOOKLIST_XML = """<?xml version="1.0" encoding="utf-8"?>
<booklist>
%s
</booklist>"""

BOOKS_TOTAL = 6.99 * 235 + 12.99 * 12

DIGITS = "0123456789"

DIGITS_XML = """<?xml version="1.0" encoding="utf-8"?>
<text>%s</text>"""

REVERSED_DIGITS = "9876543210"

GOBBLEDY = "dfd dh AAAsrter xcbxb AAAA gghmjk gfghjk ghAAAkghk dgsdfgAAA sdsdg AAA sdsdfg\n"

GOBBLEDY_XML = """<?xml version="1.0" encoding="utf-8"?>
<text>%s</text>"""

GOBBLEDY_OUT = GOBBLEDY.replace('AAA','ZZZ')


class test_xslt_recursive_1_dn_20020325(xslt_test):
    source = ""
    # total-sales/simple.xsl
    transform = stringsource("""<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="text"/>

  <xsl:template match="/">
    <xsl:call-template name="sumSales1">
      <xsl:with-param name="pNodes" select="/*/book"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="sumSales1">
    <xsl:param name="pNodes" select="/.."/>
    <xsl:param name="result" select="0"/>
    <xsl:choose>
      <xsl:when test="$pNodes">
        <xsl:call-template name="sumSales1">
          <xsl:with-param name="pNodes" select="$pNodes[position()!=1]"/>
          <xsl:with-param name="result" select="$result+$pNodes[1]/sales*$pNodes[1]/price"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$result"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = ""

    def test_transform(self):
        # how many repetitions of BOOKS for the shortest source doc
        MULTIPLIER = 10
        # how many binary orders of magnitude to go up to
        EXPLIMIT = 1
        from amara.xslt import transform
        for i in range(EXPLIMIT):
            io = cStringIO.StringIO()
            elements = (2 * MULTIPLIER) * 2 ** i
            title = "simple recursion with %d element" % elements + "s" * (elements > 0)
            self.source = stringsource(BOOKLIST_XML % ((BOOKS * MULTIPLIER) * 2 ** i))
            self.expected = str((BOOKS_TOTAL * MULTIPLIER) * 2 ** i)
            result = transform(self.source, self.transform, output=io)
            self.assert_(treecompare.html_compare(self.expected, io.getvalue()))
        return

class test_xslt_recursive_2_dn_20020325(xslt_test):
    source = ""
    # total-sales/dvc.xsl
    transform = stringsource("""<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="text"/>

  <xsl:template match="/">
    <xsl:call-template name="sumSales">
      <xsl:with-param name="pNodes" select="/*/book"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="sumSales">
    <xsl:param name="pNodes" select="/.."/>
    <xsl:param name="result" select="0"/>

    <xsl:variable name="vcntNodes" select="count($pNodes)"/>

    <xsl:choose>
      <xsl:when test="$vcntNodes = 1">
        <xsl:value-of select="$result + $pNodes/sales * $pNodes/price"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="vcntHalf" select="floor($vcntNodes div 2)"/>

        <xsl:variable name="vValue1">
          <xsl:call-template name="sumSales">
            <xsl:with-param name="pNodes" select="$pNodes[position() &lt;= $vcntHalf]"/>
            <xsl:with-param name="result" select="$result"/>
          </xsl:call-template>
        </xsl:variable>

        <xsl:call-template name="sumSales">
          <xsl:with-param name="pNodes" select="$pNodes[position() > $vcntHalf]"/>
          <xsl:with-param name="result" select="$vValue1"/>
        </xsl:call-template>

      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = ""

    def test_transform(self):
        # how many repetitions of BOOKS for the shortest source doc
        MULTIPLIER = 10
        # how many binary orders of magnitude to go up to
        EXPLIMIT = 1
        from amara.xslt import transform
        for i in range(EXPLIMIT):
            io = cStringIO.StringIO()
            elements = (2 * MULTIPLIER) * 2 ** i
            title = "simple recursion with %d element" % elements + "s" * (elements > 0)
            self.source = stringsource(BOOKLIST_XML % ((BOOKS * MULTIPLIER) * 2 ** i))
            self.expected = str((BOOKS_TOTAL * MULTIPLIER) * 2 ** i)
            result = transform(self.source, self.transform, output=io)
            self.assert_(treecompare.html_compare(self.expected, io.getvalue()))
        return

class test_xslt_recursive_3_dn_20020325(xslt_test):
    source = ""
    # total-sales/two-stage.xsl
    # (with $t param added so threshold can be adjusted)
    #
    # The threshold is the # of elements above which DVC will be used,
    # and below which recursion will be used.
    #
    transform = stringsource("""<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="text"/>

  <xsl:param name="t" select="20"/>

  <xsl:template match="/">
    <xsl:call-template name="sumSales">
      <xsl:with-param name="pNodes" select="/*/book"/>
      <xsl:with-param name="threshold" select="$t"/>
    </xsl:call-template>
  </xsl:template>

  <!--   DVC template:     -->

  <xsl:template name="sumSales">
    <xsl:param name="pNodes" select="/.."/>
    <xsl:param name="threshold" select="10"/>
    <xsl:param name="result" select="0"/>

    <xsl:variable name="vcntNodes" select="count($pNodes)"/>

    <xsl:choose>
      <xsl:when test="$vcntNodes &lt;= $threshold">
        <xsl:call-template name="sumSales1">
          <xsl:with-param name="pNodes" select="$pNodes"/>
          <xsl:with-param name="result" select="$result"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="vcntHalf" select="floor($vcntNodes div 2)"/>
        <xsl:variable name="vValue1">
          <xsl:call-template name="sumSales">
            <xsl:with-param name="pNodes" select="$pNodes[position() &lt;= $vcntHalf]"/>
            <xsl:with-param name="threshold" select="$threshold"/>
            <xsl:with-param name="result" select="$result"/>
          </xsl:call-template>
        </xsl:variable>

        <xsl:call-template name="sumSales">
          <xsl:with-param name="pNodes" select="$pNodes[position() > $vcntHalf]"/>
          <xsl:with-param name="threshold" select="$threshold"/>
          <xsl:with-param name="result" select="$vValue1"/>
        </xsl:call-template>

      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!--   simple recursive template:   -->

  <xsl:template name="sumSales1">
    <xsl:param name="pNodes"  select="/.."/>
    <xsl:param name="result"  select="0"/>
    <xsl:choose>
      <xsl:when test="$pNodes">
            <xsl:call-template name="sumSales1">
               <xsl:with-param name="pNodes" select="$pNodes[position()!=1]"/>
               <xsl:with-param name="result" select="$result+$pNodes[1]/sales*$pNodes[1]/price"/>
            </xsl:call-template>
      </xsl:when>
      <xsl:otherwise><xsl:value-of select="$result"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = ""

    def test_transform(self):
        from amara.xslt import transform
        # how many repetitions of BOOKS for the shortest source doc
        MULTIPLIER = 10
        # how many binary orders of magnitude to go up to
        EXPLIMIT = 1
        for i in range(EXPLIMIT):
            io = cStringIO.StringIO()
            threshold = 8 # seems to be best as of 2003-03-23
            elements = (2 * MULTIPLIER) * 2 ** i
            title = "2-stage divide and conquer with %d element" % elements + "s" * (elements > 0)
            title += " (threshold=%d)" % threshold
            self.source = stringsource(BOOKLIST_XML % ((BOOKS * MULTIPLIER) * 2 ** i))
            self.expected = str((BOOKS_TOTAL * MULTIPLIER) * 2 ** i)
            result = transform(self.source, self.transform, output=io, params={'t': threshold})
            self.assert_(treecompare.html_compare(self.expected, io.getvalue()))
        return

class test_xslt_recursive_4_dn_20020325(xslt_test):
    source = ""
    # reverse/lrReverse.xsl
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="text"/>

  <xsl:template match="/">
      <xsl:call-template name="reverse2">
        <xsl:with-param name="theString" select="/*/text()"/>
      </xsl:call-template>
  </xsl:template>

  <xsl:template name="reverse2">
    <xsl:param name="theString"/>
    <xsl:variable name="thisLength" select="string-length($theString)"/>
    <xsl:choose>
      <xsl:when test="$thisLength = 1">
        <xsl:value-of select="$theString"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="length1" select="floor($thisLength div 2)"/>
        <xsl:call-template name="reverse2">
          <xsl:with-param name="theString" select="substring($theString,$length1+1, $thisLength - $length1)"/>
        </xsl:call-template>
        <xsl:call-template name="reverse2">
          <xsl:with-param name="theString" select="substring($theString, 1, $length1)"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = ""

    def test_transform(self):
        from amara.xslt import transform
        # how many repetitions of BOOKS for the shortest source doc
        MULTIPLIER = 10
        # how many binary orders of magnitude to go up to
        EXPLIMIT = 1
        for i in range(EXPLIMIT):
            io = cStringIO.StringIO()
            chars = 1000 * 2 ** i
            title = "divide and conquer reversal of %d-char string" % chars
            self.source = stringsource(DIGITS_XML % ((DIGITS * 100) * 2 ** i))
            self.expected = str((REVERSED_DIGITS * 100) * 2 ** i)
            result = transform(self.source, self.transform, output=io)
            self.assert_(treecompare.html_compare(self.expected, io.getvalue()))
        return
    

class test_xslt_recursive_5_dn_20020325(xslt_test):
    source = ""
    # reverse/lrReverse2.xsl
    # (with $t param added so threshold can be adjusted)
    #
    # The threshold is the # of chars above which DVC will be used,
    # and below which recursion will be used.
    #
    transform = stringsource("""<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="text"/>

  <xsl:param name="t" select="75"/>

  <xsl:template match="/">
    <xsl:call-template name="reverse2">
      <xsl:with-param name="theString" select="/*/text()"/>
      <xsl:with-param name="threshold" select="$t"/>
    </xsl:call-template>
  </xsl:template>

  <!-- DVC template:       -->

  <xsl:template name="reverse2">
    <xsl:param name="theString"/>
    <xsl:param name="threshold" select="30"/>
    <xsl:variable name="thisLength" select="string-length($theString)"/>
    <xsl:choose>
      <xsl:when test="$thisLength &lt;= $threshold">
        <xsl:call-template name="reverse">
          <xsl:with-param name="theString" select="$theString"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="length1" select="floor($thisLength div 2)"/>
        <xsl:call-template name="reverse2">
          <xsl:with-param name="theString" select="substring($theString,$length1+1, $thisLength - $length1)"/>
          <xsl:with-param name="threshold" select="$threshold"/>
        </xsl:call-template>
        <xsl:call-template name="reverse2">
          <xsl:with-param name="theString" select="substring($theString, 1, $length1)"/>
          <xsl:with-param name="threshold" select="$threshold"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- simple recursive template:   -->
  <xsl:template name="reverse">
    <xsl:param name="theString"/>
    <xsl:variable name="thisLength" select="string-length($theString)"/>
    <xsl:choose>
      <xsl:when test="$thisLength = 1">
        <xsl:value-of select="$theString"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="substring($theString,$thisLength,1)"/>
        <xsl:call-template name="reverse">
          <xsl:with-param name="theString" select="substring($theString, 1, $thisLength -1)"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = ""

    def test_transform(self):
        from amara.xslt import transform
        # how many repetitions of BOOKS for the shortest source doc
        MULTIPLIER = 10
        # how many binary orders of magnitude to go up to
        EXPLIMIT = 1
        for i in range(EXPLIMIT):
            io = cStringIO.StringIO()
            threshold = 75
            chars = 1000 * 2 ** i
            title = "2-stage divide and conquer reversal of %d-char string" % chars
            title += " (threshold=%d)" % threshold
            self.source = stringsource(DIGITS_XML % ((DIGITS * 100) * 2 ** i))
            self.expected = str((REVERSED_DIGITS * 100) * 2 ** i)
            result = transform(self.source, self.transform, output=io, params={'t': threshold})
            self.assert_(treecompare.html_compare(self.expected, io.getvalue()))
        return

class test_xslt_recursive_6_dn_20020325(xslt_test):
    source = ""
    transform = stringsource("""<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:exsl="http://exslt.org/common">
  
  <xsl:output method="text" encoding="iso-8859-1" />

  <xsl:template match="/">
    <xsl:variable name="Result">
      <xsl:call-template name="lrReplace">
        <xsl:with-param name="theString" select="/*/text()"/>
        <xsl:with-param name="target" select="'AAA'" />
        <xsl:with-param name="replacement" select="'ZZZ'" />
      </xsl:call-template>
    </xsl:variable>

    <xsl:value-of select="$Result" />
  </xsl:template>

  <xsl:template name="lrReplace">
    <xsl:param name="theString"/>
    <xsl:param name="target"/>
    <xsl:param name="replacement"/>
    <xsl:variable name="lStr" select="string-length($theString)"/>

    <xsl:variable name="resRTF">
      <xsl:call-template name="lrReplace2">
        <xsl:with-param name="theString" select="$theString"/>
        <xsl:with-param name="target" select="$target"/>
        <xsl:with-param name="replacement" select="$replacement"/>
      </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="resNode-set" select="exsl:node-set($resRTF)"/>

    <xsl:value-of select="$resNode-set/text()"/>

    <xsl:value-of select="substring($theString, $lStr - $resNode-set/u+1)" />
  </xsl:template>

  <xsl:template name="lrReplace2">
    <xsl:param name="theString"/>
    <xsl:param name="target"/>
    <xsl:param name="replacement" select="''" />

    <xsl:variable name="lStr" select="string-length($theString)" />

    <xsl:variable name="lTarget" select="string-length($target)" />

    <xsl:choose>
      <xsl:when test="$lStr &lt; $lTarget + $lTarget">
        <xsl:choose>
          <xsl:when 
             test="contains($theString,$target)">
            <xsl:value-of select="substring-before($theString,$target)" />
            <xsl:value-of select="$replacement" />
            <u>
              <xsl:value-of select="string-length(substring-after($theString,$target))" />
            </u>
          </xsl:when>

          <xsl:otherwise>
            <xsl:choose>
              <xsl:when test="$lStr &gt;= $lTarget">
                <xsl:value-of select="substring($theString, 1, $lStr - $lTarget + 1)"/>
                <u>
                  <xsl:value-of select="$lTarget - 1" />
                </u>
              </xsl:when>

              <xsl:otherwise>
                <u>
                  <xsl:value-of select="$lStr" />
                </u>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>

      <!-- Now the general case - theString is not less than twice the replacement -->
      <xsl:otherwise>
        <xsl:variable name="halfLength" select="floor($lStr div 2)"/>

        <xsl:variable name="processedHalf">
          <xsl:call-template name="lrReplace2">
            <xsl:with-param name="theString" select="substring($theString, 1, $halfLength)"/>
            <xsl:with-param name="target" select="$target"/>
            <xsl:with-param name="replacement" select="$replacement"/>
          </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="nodePrHalf" select="exsl:node-set($processedHalf)"/>

        <xsl:value-of select="$nodePrHalf/text()"/>

        <xsl:call-template name="lrReplace2">
          <xsl:with-param name="theString"
          select="substring($theString, $halfLength - $nodePrHalf/u + 1)" />
          <xsl:with-param name="target" select="$target" />
          <xsl:with-param name="replacement" select="$replacement" />
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
</xsl:stylesheet>""")
    parameters = {}
    expected = ""

    def test_transform(self):
        from amara.xslt import transform
        # how many repetitions of BOOKS for the shortest source doc
        MULTIPLIER = 10
        # how many binary orders of magnitude to go up to
        EXPLIMIT = 1
        for i in range(EXPLIMIT):
            io = cStringIO.StringIO()
            chars = (len(GOBBLEDY) * 20) * 2 ** i
            title = "divide and conquer search/replace on %d-char string" % chars
            self.source = stringsource(GOBBLEDY_XML % ((GOBBLEDY * 20) * 2 ** i))
            self.expected = str((GOBBLEDY_OUT * 20) * 2 ** i)
            result = transform(self.source, self.transform, output=io)
            self.assert_(treecompare.html_compare(self.expected, io.getvalue()))
        return

class test_xslt_recursive_7_dn_20020325(xslt_test):
    source = ""
    transform = stringsource("""<xsl:stylesheet version="1.0" 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exsl="http://exslt.org/common">
  <xsl:output method="text" encoding="iso-8859-1" />

  <xsl:template match="/">
    <xsl:variable name="Result">
      <xsl:call-template name="lrReplace">
        <xsl:with-param name="theString" select="/*/text()"/>
        <xsl:with-param name="target" select="'AAA'"/>
        <xsl:with-param name="replacement" select="'ZZZ'"/>
        <xsl:with-param name="threshold" select="2000"/>
      </xsl:call-template>
    </xsl:variable>

    <xsl:value-of select="$Result" />
  </xsl:template>

  <xsl:template name="lrReplace">
    <xsl:param name="theString"/>
    <xsl:param name="target"/>
    <xsl:param name="replacement"/>
    <xsl:param name="threshold" select="150"/>
    <xsl:variable name="lStr" select="string-length($theString)"/>

    <xsl:variable name="resRTF">
      <xsl:call-template name="lrReplace2">
        <xsl:with-param name="theString" select="$theString"/>
        <xsl:with-param name="target" select="$target"/>
        <xsl:with-param name="replacement" select="$replacement"/>
        <xsl:with-param name="threshold" select="$threshold"/>
      </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="resNode-set" select="exsl:node-set($resRTF)"/>

    <xsl:value-of select="$resNode-set/text()"/>

    <xsl:value-of select="substring($theString, $lStr - $resNode-set/u+1)"/>
  </xsl:template>

  <!-- DVC template:        -->
  <xsl:template name="lrReplace2">
    <xsl:param name="theString"/>
    <xsl:param name="target"/>
    <xsl:param name="replacement"/>
    <xsl:param name="threshold" select="150"/>

    <xsl:variable name="lStr" select="string-length($theString)"/>

    <xsl:variable name="lTarget" select="string-length($target)"/>

    <xsl:choose>
      <xsl:when test="$lStr &lt;= $threshold">
        <xsl:call-template name="lrReplace3">
          <xsl:with-param name="theString" select="$theString"/>
          <xsl:with-param name="target" select="$target"/>
          <xsl:with-param name="replacement" select="$replacement"/>
        </xsl:call-template>
      </xsl:when>

      <xsl:otherwise>
        <xsl:variable name="halfLength" select="floor($lStr div 2)"/>

        <xsl:variable name="processedHalf">
          <xsl:call-template name="lrReplace2">
            <xsl:with-param name="theString" select="substring($theString, 1, $halfLength)" />
            <xsl:with-param name="target" select="$target" />
            <xsl:with-param name="replacement" select="$replacement"/>
            <xsl:with-param name="threshold" select="$threshold"/>
          </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="nodePrHalf" select="exsl:node-set($processedHalf)"/>

        <xsl:value-of select="$nodePrHalf/text()"/>

        <xsl:call-template name="lrReplace2">
          <xsl:with-param name="theString" select="substring($theString, $halfLength - $nodePrHalf/u + 1)"/>
          <xsl:with-param name="target" select="$target"/>
          <xsl:with-param name="replacement" select="$replacement"/>
          <xsl:with-param name="threshold" select="$threshold" />
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!--  simple recursive template:   -->
  <xsl:template name="lrReplace3">
    <xsl:param name="theString" />
    <xsl:param name="target" />
    <xsl:param name="replacement" />

    <xsl:choose>
      <xsl:when test="contains($theString, $target)">
        <xsl:value-of select="substring-before($theString, $target)"/>
        <xsl:value-of select="$replacement"/>

        <xsl:call-template name="lrReplace3">
          <xsl:with-param name="theString" select="substring-after($theString, $target)"/>
          <xsl:with-param name="target" select="$target"/>
          <xsl:with-param name="replacement" select="$replacement"/>
        </xsl:call-template>
      </xsl:when>

      <xsl:otherwise>
        <xsl:variable name="lStr" select="string-length($theString)"/>
        <xsl:variable name="lTarget" select="string-length($target)"/>

        <xsl:choose>
          <xsl:when test="$lStr &gt;= $lTarget">
            <xsl:value-of select="substring($theString, 1, $lStr -$lTarget+1)" />
            <u>
              <xsl:value-of select="$lTarget -1"/>
            </u>
          </xsl:when>

          <xsl:otherwise>
            <u>
              <xsl:value-of select="$lStr"/>
            </u>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
</xsl:stylesheet>""")
    parameters = {}
    expected = ""

    def test_transform(self):
        import sys
        from amara.xslt import transform
        # how many repetitions of BOOKS for the shortest source doc
        MULTIPLIER = 10
        # how many binary orders of magnitude to go up to
        EXPLIMIT = 1
        for i in range(EXPLIMIT):
            io = cStringIO.StringIO()
            chars = (len(GOBBLEDY) * 20) * 2 ** i
            title = "2-stage divide and conquer search/replace on %d-char string" % chars
            self.source = stringsource(GOBBLEDY_XML % ((GOBBLEDY * 20) * 2 ** i))
            self.expected = str((GOBBLEDY_OUT * 20) * 2 ** i)
            result = transform(self.source, self.transform, output=io)
            self.assert_(treecompare.html_compare(self.expected, io.getvalue()))
        return

if __name__ == '__main__':
    test_main()
