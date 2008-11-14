########################################################################
# test/xslt/dn_20010504.py
# Dimitre Novatchev <dnovatchev@yahoo.com> discovered a brilliant 
# technique for dynamic template selection
import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

from Ft.Lib.Uri import OsPathToUri

class test_xslt_count_children_via_incrementing_counter_dn_20010504(xslt_test):
    source = stringsource("""\
<numbers>
 <num>3</num> 
 <num>2</num> 
 <num>9</num> 
 <num>4</num> 
 <num>6</num> 
 <num>5</num> 
 <num>7</num> 
 <num>8</num> 
 <num>1</num> 
</numbers>""")
    transform = stringsource("""\
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:num="num"
xmlns:num2="num2"
>

  <num:node>num</num:node>
  <num2:node>num2</num2:node>

  <xsl:output method="text" />
  
  <xsl:variable name="document" select="document('')" />
  <xsl:variable name="gtNum-node" select="$document//num:*"/>
  <xsl:variable name="gtNum2-node" select="$document//num2:*"/>

  <xsl:template match="/">
    <xsl:call-template name="get-max">
      <xsl:with-param name="greaterSelector" select="$gtNum-node" />
      <xsl:with-param name="nodes" select="/numbers/num" />
    </xsl:call-template>
    
    <xsl:text>&#xA;</xsl:text>

    <xsl:call-template name="get-max">
      <xsl:with-param name="greaterSelector" select="$gtNum2-node" />
      <xsl:with-param name="nodes" select="/numbers/num" />
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="get-max">
    <xsl:param name="greaterSelector" select="/*"/>
    <xsl:param name="nodes" />

    <xsl:choose>
      <xsl:when test="$nodes">
        <xsl:variable name="max-of-rest">
          <xsl:call-template name="get-max">
            <xsl:with-param name="greaterSelector" select="$greaterSelector" />
            <xsl:with-param name="nodes" select="$nodes[position()!=1]" />
          </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="isGreater">
         <xsl:apply-templates select="$greaterSelector" >
           <xsl:with-param name="n1" select="$nodes[1]"/>
           <xsl:with-param name="n2" select="$max-of-rest"/>
         </xsl:apply-templates>
        </xsl:variable>
        
        <xsl:choose>
          <xsl:when test="$isGreater = 'true'">
            <xsl:value-of select="$nodes[1]" />
          </xsl:when>

          <xsl:otherwise>
            <xsl:value-of select="$max-of-rest" />
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>

      <xsl:otherwise>
        <xsl:value-of select="-999999999" />

<!-- minus infinity -->
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  <xsl:template name="isGreaterNum" match="node()[namespace-uri()='num']">
    <xsl:param name="n1"/>
    <xsl:param name="n2"/>

    <xsl:value-of select="$n1 > $n2"/>
  </xsl:template>

  <xsl:template name="isGreaterNum2" match="node()[namespace-uri()='num2']">
    <xsl:param name="n1"/>
    <xsl:param name="n2"/>

    <xsl:value-of select="1 div $n1 > 1 div $n2"/>
  </xsl:template>

</xsl:stylesheet>""", uri = OsPathToUri(os.path.abspath(__file__)))
    parameters = {}
    expected = """\
9
1"""

if __name__ == '__main__':
    test_main()
