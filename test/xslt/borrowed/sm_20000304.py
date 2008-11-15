########################################################################
# test/xslt/sm20000304.py
# Example from Steve Muench <smuench@us.oracle.com>
# to Jon Smirl <jonsmirl@mediaone.net>
# on 4 March 2000

"""
From: "Steve Muench" <smuench@us.oracle.com>
To: <xsl-list@mulberrytech.com>
Subject: Re: SVG charts and graphs from XML input
Date: Sat, 4 Mar 2000 18:02:53 -0800 (19:02 MST)

This is by no means a bullet-proof, one-size-fits
all charting stylesheet, but it *was* my first foray
into SVG from XSLT.

Given XML results of an Oracle XSQL Page like:

<xsql:query xmlns:xsql="urn:oracle-xsql" connection="demo">
  select ename, sal from dept
</xsql:query>

Which under the covers produces a dynamic XML doc like:

[SNIP source]

The following "salchart.xsl" XSLT stylesheet
renders a dynamic bar chart with "cool colors"
for the employees in the department.

You may have to modify the namespace of the
Java extension functions to get it to work in
XT or Saxon or other XSLT engines.

[SNIP stylesheet]
"""

import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

#Extensions

from Ft.Xml.XPath import Conversions

ORACLE_JAVA_NS = 'http://www.oracle.com/XSL/Transform/java'
JAVA_COLOR_NS = ORACLE_JAVA_NS + '/java.awt.Color'
JAVA_INTEGER_NS = ORACLE_JAVA_NS + '/java.lang.Integer'

def Java_Color_GetHSBColor(context, hue, saturation, brightness):
    hue = Conversions.NumberValue(hue)
    saturation = Conversions.NumberValue(saturation)
    brightness = Conversions.NumberValue(brightness)

    if saturation == 0:
        r = g = b = int(brightness * 255)
    else:
        r = g = b = 0
        h = (hue - int(hue)) * 6.0
        f = h - int(h)
        p = brightness * (1.0 - saturation)
        q = brightness * (1.0 - saturation * f)
        t = brightness * (1.0 - (saturation * (1.0 - f)))

        h = int(h)
        if h == 0:
            r = int(brightness * 255)
            g = int(t * 255)
            b = int(p * 255)
        elif h == 1:
            r = int(q * 255)
            g = int(brightness * 255)
            b = int(p * 255)
        elif h == 2:
            r = int(p * 255)
            g = int(brightness * 255)
            b = int(t * 255)
        elif h == 3:
            r = int(p * 255)
            g = int(q * 255)
            b = int(brightness * 255)
        elif h == 4:
            r = int(t * 255)
            g = int(p * 255)
            b = int(brightness * 255)
        elif h == 5:
            r = int(brightness * 255)
            g = int(p * 255)
            b = int(q * 255)
    return 0xff000000L | (r << 16) | (g << 8) | (b << 0)

def Java_Color_GetRed(context, color):
    color = Conversions.NumberValue(color)
    return (long(color) >> 16) & 0xff

def Java_Color_GetGreen(context, color):
    color = Conversions.NumberValue(color)
    return (long(color) >> 8) & 0xff

def Java_Color_GetBlue(context, color):
    color = Conversions.NumberValue(color)
    return long(color) & 0xff

def Java_Integer_ToHexString(context, number):
    return '%X' % Conversions.NumberValue(number)

ExtFunctions = {
    (JAVA_COLOR_NS, 'getHSBColor') : Java_Color_GetHSBColor,
    (JAVA_COLOR_NS, 'getRed') : Java_Color_GetRed,
    (JAVA_COLOR_NS, 'getGreen') : Java_Color_GetGreen,
    (JAVA_COLOR_NS, 'getBlue') : Java_Color_GetBlue,
    (JAVA_INTEGER_NS, 'toHexString') : Java_Integer_ToHexString,
    }

class test_xslt_call_template_ed_20010101(xslt_test):
    source = stringsource("""<?xml version = '1.0'?>
<ROWSET>
   <ROW num="1">
      <ENAME>CLARK</ENAME>
      <SAL>2450</SAL>
   </ROW>
   <ROW num="2">
      <ENAME>KING</ENAME>
      <SAL>3900</SAL>
   </ROW>
   <ROW num="3">
      <ENAME>MILLER</ENAME>
      <SAL>1300</SAL>
   </ROW>
</ROWSET>
""")
    transform = stringsource('''<xsl:stylesheet version="1.0"
   xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
   xmlns:Color="http://www.oracle.com/XSL/Transform/java/java.awt.Color"
   xmlns:Integer="http://www.oracle.com/XSL/Transform/java/java.lang.Integer"
   exclude-result-prefixes="Color Integer">

 <xsl:output media-type="image/svg"/>

 <xsl:template match="/">
 <svg xml:space="preserve" width="1000" height="1000">
   <desc>Salary Chart</desc>
   <g style="stroke:#000000;stroke-width:1;font-family:Arial;font-size:16">
     <xsl:for-each select="ROWSET/ROW">
       <xsl:call-template name="drawBar">
         <xsl:with-param name="rowIndex" select="position()"/>
         <xsl:with-param name="ename" select="ENAME"/>
         <xsl:with-param name="sal" select="number(SAL)"/>
       </xsl:call-template>
     </xsl:for-each>
   </g>
 </svg>
 </xsl:template>

 <xsl:template name="drawBar">
   <xsl:param name="rowIndex" select="number(0)"/>
   <xsl:param name="ename"/>
   <xsl:param name="sal" select="number(0)"/>

   <xsl:variable name="xOffset"   select="number(100)"/>
   <xsl:variable name="yOffset"   select="number(20)"/>
   <xsl:variable name="barHeight" select="number(25)"/>
   <xsl:variable name="gap"       select="number(10)"/>

   <xsl:variable name="x" select="$xOffset"/>
   <xsl:variable name="y" select="$yOffset + $rowIndex * ($barHeight + $gap)"/>
   <xsl:variable name="barWidth" select="$sal div number(10)"/>
   <rect x="{$x}" y="{$y}" height="{$barHeight}" width="{$barWidth}">
     <xsl:attribute name="style">
       <xsl:text>fill:#</xsl:text>
       <xsl:call-template name="getCoolColorStr" xml:space="default">
         <xsl:with-param name="colorIndex" select="$rowIndex"/>
         <xsl:with-param name="totalColors" select="number(14)"/>
       </xsl:call-template>
       <xsl:text> </xsl:text>
     </xsl:attribute>
   </rect>
   <xsl:variable name="fontHeight" select="number(18)"/>
   <text x="20" y="{$y + $fontHeight}">
     <xsl:value-of select="$ename"/>
   </text>
   <xsl:variable name="x2" select="$xOffset + $barWidth + 10"/>
   <text x="{$x2}" y="{$y + $fontHeight}">
     <xsl:value-of select="$sal"/>
   </text>
  </xsl:template>

  <xsl:template name="getCoolColorStr">
    <xsl:param name="colorIndex"/>
    <xsl:param name="totalColors"/>

    <xsl:variable name="SATURATION" select="number(0.6)"/>
    <xsl:variable name="BRIGHTNESS" select="number(0.9)"/>

    <xsl:variable name="hue" select="$colorIndex div $totalColors"/>
    <xsl:variable name="c"   select="Color:getHSBColor($hue, $SATURATION, $BRIGHTNESS)"/>
    <xsl:variable name="r"   select="Color:getRed($c)"/>
    <xsl:variable name="g"   select="Color:getGreen($c)"/>
    <xsl:variable name="b"   select="Color:getBlue($c)"/>
    <xsl:variable name="rs"  select="Integer:toHexString($r)"/>
    <xsl:variable name="gs"  select="Integer:toHexString($g)"/>
    <xsl:variable name="bs"  select="Integer:toHexString($b)"/>
    <xsl:if test="$r &lt; 16">0</xsl:if><xsl:value-of select="$rs"/>
    <xsl:if test="$g &lt; 16">0</xsl:if><xsl:value-of select="$gs"/>
    <xsl:if test="$b &lt; 16">0</xsl:if><xsl:value-of select="$bs"/>
  </xsl:template>

</xsl:stylesheet>
''')
    parameters = {}
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<svg height='1000' xml:space='preserve' width='1000'>
   <desc>Salary Chart</desc>
   <g style='stroke:#000000;stroke-width:1;font-family:Arial;font-size:16'>
     
       <rect height='25' x='100' style='fill:#E5965B ' width='245' y='55'/><text x='20' y='73'>CLARK</text><text x='355' y='73'>2450</text>
     
       <rect height='25' x='100' style='fill:#E5D15B ' width='390' y='90'/><text x='20' y='108'>KING</text><text x='500' y='108'>3900</text>
     
       <rect height='25' x='100' style='fill:#BEE55B ' width='130' y='125'/><text x='20' y='143'>MILLER</text><text x='240' y='143'>1300</text>
     
   </g>
 </svg>"""

    # def test_transform(self):
    #     import sys
    #     from amara.xslt import transform
    # 
    #     result = transform(self.source, self.transform, output=io)
    # 
    #     #FIXME: the numerics break under Python 2.3
    #     test_harness.XsltTest(tester, source, [sheet], expected_1,
    #                           extensionModules=[__name__])
    # 
    #     self.assert_(treecompare.html_compare(self.expected, io.getvalue()))
    # 
    #     return


if __name__ == '__main__':
    test_main()

