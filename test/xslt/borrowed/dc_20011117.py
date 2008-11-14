########################################################################
# test/xslt/dc_20011117.py
#Dave Carlile's greeting card to XSLT
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_xslt_wacky_translate_dc_20011117(xslt_test):
    source = stringsource("<dummy/>")
    transform = stringsource("""\
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
        version="1.0"><xsl:output method="text"/><xsl:variable name="x"
        select="'y*xxz13fr9hd*z19o19Fe14wfnsk/#S741a%d1#q*9F/214od*zk'"/> <xsl:template match="/"><xsl:value-of select="translate($x, 'Fw*y/x#z134kfq7%9','hwaH pXy BT!iPLnt')"/></xsl:template> </xsl:stylesheet> 
""")
    parameters = {}
    expected = 'Happy Birthday to the Twins! XSLT and XPath 2 Today!'

if __name__ == '__main__':
    test_main()
