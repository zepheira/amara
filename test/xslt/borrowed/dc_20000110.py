########################################################################
# test/xslt/dc_200000110.py
#Example from David Carlisle <davidc@nag.co.uk> to John Robert Gardner 
# <jrgardn@emory.edu> on 10 Jan 2000
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

commonsource = stringsource("""<sample>
<verse meter="gaayatrii" id="rv1.16.1">
    <mantra id="rv1.16.1a">
        aa tvaa vahantu harayo
    </mantra>
    <mantra id="rv1.16.1b">
        vRSaNaM somapiitaye
    </mantra>
    <mantra id="rv1.16.1c">
        indra tvaa suuracakSasaH
    </mantra>
</verse>

<verse meter="gaayatrii" id="rv1.84.10">
    <mantra id="rv1.84.10a">
        svaador itthaa viSuuvato
    </mantra>
    <mantra id="rv1.84.10b">
        madhvaH pibanti gauryaH
    </mantra>
    <mantra id="rv1.84.10c">
        yaa indreNa sayaavariir
    </mantra>
</verse>
</sample>""")

class test_xslt_using_position_dc_200000110(xslt_test):
    source = commonsource
    transform = stringsource("""<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version="1.0"
  >

<xsl:output method="xml" indent="yes"/>

<xsl:template match="sample">
<verse>
<xsl:apply-templates select="verse[@id='rv1.84.10']/mantra"/>
</verse>
</xsl:template>

<xsl:template match="verse[@id='rv1.84.10']/mantra">
<xsl:copy-of select="."/>
<xsl:variable name="x" select="position()"/>
<xsl:copy-of select="../../verse[@id='rv1.16.1']/mantra[position()=$x]"/>
</xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<verse>
  <mantra id='rv1.84.10a'>
        svaador itthaa viSuuvato
    </mantra>
  <mantra id='rv1.16.1a'>
        aa tvaa vahantu harayo
    </mantra>
  <mantra id='rv1.84.10b'>
        madhvaH pibanti gauryaH
    </mantra>
  <mantra id='rv1.16.1b'>
        vRSaNaM somapiitaye
    </mantra>
  <mantra id='rv1.84.10c'>
        yaa indreNa sayaavariir
    </mantra>
  <mantra id='rv1.16.1c'>
        indra tvaa suuracakSasaH
    </mantra>
</verse>"""

class test_xslt_for_each_and_xsl_sort_dc_200000110(xslt_test):
    source = commonsource
    transform = stringsource("""<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version="1.0"
  >

<xsl:output method="xml" indent="yes"/>

<xsl:template match="sample">
<verse>
<xsl:for-each select="verse/mantra">
<xsl:sort select="substring-after(@id,../@id)"/>
<xsl:sort select="../@id" order="descending"/>
<xsl:copy-of select="."/>
</xsl:for-each>
</verse>
</xsl:template>

</xsl:stylesheet>""")
    parameters = {}
    expected = """<?xml version='1.0' encoding='UTF-8'?>
<verse>
  <mantra id='rv1.84.10a'>
        svaador itthaa viSuuvato
    </mantra>
  <mantra id='rv1.16.1a'>
        aa tvaa vahantu harayo
    </mantra>
  <mantra id='rv1.84.10b'>
        madhvaH pibanti gauryaH
    </mantra>
  <mantra id='rv1.16.1b'>
        vRSaNaM somapiitaye
    </mantra>
  <mantra id='rv1.84.10c'>
        yaa indreNa sayaavariir
    </mantra>
  <mantra id='rv1.16.1c'>
        indra tvaa suuracakSasaH
    </mantra>
</verse>"""

if __name__ == '__main__':
    test_main()
